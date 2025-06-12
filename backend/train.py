# train.py

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib

print("--- Starting Model Training Process ---")

# ==============================================================================
# 1. LOAD RAW DATA
# ==============================================================================
print("STEP 1: Loading raw data...")
try:
    transactions_df = pd.read_csv("synthetic_transaction_data_15k.csv")
    customer_df = pd.read_csv("synthetic_customer_data_15k.csv")
    print("Data loaded successfully.")
except FileNotFoundError as e:
    print(f"ERROR: {e}. Make sure the CSV files are in the same directory.")
    exit()

# ==============================================================================
# 2. PREPROCESS TRANSACTION DATA
# ==============================================================================
print("STEP 2: Preprocessing transaction data...")
# Drop irrelevant columns
cols_to_drop_txn = ['descr', 'exch_rate', 'pay_ref', 'auth_code']
transactions_df.drop(columns=cols_to_drop_txn, inplace=True, errors='ignore')

# Convert txn_date and txn_time to a single datetime object
transactions_df['txn_datetime'] = pd.to_datetime(transactions_df['txn_date'] + ' ' + transactions_df['txn_time'])
transactions_df.drop(columns=['txn_date', 'txn_time'], inplace=True)

# Derive time-based features
transactions_df['txn_hour'] = transactions_df['txn_datetime'].dt.hour
transactions_df['txn_dayofweek'] = transactions_df['txn_datetime'].dt.dayofweek
transactions_df['txn_day'] = transactions_df['txn_datetime'].dt.day
transactions_df['txn_month'] = transactions_df['txn_datetime'].dt.month
transactions_df['txn_year'] = transactions_df['txn_datetime'].dt.year

# ==============================================================================
# 3. FEATURE ENGINEERING & ANOMALY DETECTION (ISOLATION FOREST)
# ==============================================================================
print("STEP 3: Engineering features and running Isolation Forest...")
# Amount-based feature
transactions_df['log_amount'] = np.log1p(transactions_df['amount'])

# Time since last transaction feature
transactions_df.sort_values(['acct_num', 'txn_datetime'], inplace=True)
transactions_df['time_since_last_txn_seconds'] = transactions_df.groupby('acct_num')['txn_datetime'].diff().dt.total_seconds()
transactions_df['time_since_last_txn_seconds'].fillna(0, inplace=True)

# One-hot encode categorical features for the anomaly model
categorical_cols_txn = ['txn_type', 'currency', 'channel', 'pay_method']
transactions_df_encoded = pd.get_dummies(transactions_df, columns=categorical_cols_txn, prefix=categorical_cols_txn)

# Define features for Isolation Forest
feature_cols_if = ['amount', 'fee', 'txn_hour', 'txn_dayofweek', 'log_amount', 'time_since_last_txn_seconds']
# Add the one-hot encoded columns to the feature list
for col in transactions_df_encoded.columns:
    if any(prefix in col for prefix in [c + '_' for c in categorical_cols_txn]):
        if transactions_df_encoded[col].nunique() > 1: # Exclude constant columns
            feature_cols_if.append(col)

X_if = transactions_df_encoded[feature_cols_if]

# Train Isolation Forest
model_iso_forest = IsolationForest(n_estimators=100, contamination=0.02, random_state=42, n_jobs=-1)
print("Training Isolation Forest model...")
model_iso_forest.fit(X_if)

# Get anomaly predictions (-1 for anomaly, 1 for normal)
# We convert this to a 0/1 label for easier aggregation
transactions_df['anomaly_label_if'] = model_iso_forest.predict(X_if)
transactions_df['anomaly_label_if'] = transactions_df['anomaly_label_if'].apply(lambda x: 1 if x == -1 else 0)
print(f"Detected {transactions_df['anomaly_label_if'].sum()} anomalous transactions.")

# ==============================================================================
# 4. AGGREGATE DATA TO CUSTOMER LEVEL
# ==============================================================================
print("STEP 4: Aggregating transaction data to customer level...")
# Rename customer account column for merging
if 'acc_num' in customer_df.columns:
    customer_df.rename(columns={'acc_num': 'acct_num'}, inplace=True)

# Define aggregations
aggregations = {
    'txn_datetime': 'count',
    'amount': ['sum', 'mean', 'max'],
    'anomaly_label_if': 'sum',
    'time_since_last_txn_seconds': ['mean', 'min', 'max']
}
customer_aggregated_txn_df = transactions_df.groupby('acct_num').agg(aggregations)
# Flatten multi-index columns
customer_aggregated_txn_df.columns = ['_'.join(col).strip() for col in customer_aggregated_txn_df.columns.values]
customer_aggregated_txn_df.rename(columns={'txn_datetime_count': 'total_transactions'}, inplace=True)

# Calculate percentage of anomalous transactions
customer_aggregated_txn_df['percentage_anomalous_txns'] = \
    (customer_aggregated_txn_df['anomaly_label_if_sum'] / customer_aggregated_txn_df['total_transactions']) * 100
customer_aggregated_txn_df['percentage_anomalous_txns'].fillna(0, inplace=True)

# Merge aggregated data with original customer data
final_df = pd.merge(customer_df, customer_aggregated_txn_df, on='acct_num', how='left')
# Fill NaNs for customers with no transactions
for col in customer_aggregated_txn_df.columns:
    if pd.api.types.is_numeric_dtype(final_df[col]):
        final_df[col].fillna(0, inplace=True)

# ==============================================================================
# 5. APPLY RULE-BASED LABELS FOR TRAINING
# ==============================================================================
print("STEP 5: Applying rule-based labels for the training set...")
final_df['account_label'] = 'Normal'

# Suspicious Rules (based on your notebook)
suspicious_conditions = (
    (final_df['account_label'] == 'Normal') &
    (final_df['aqb'] > 0) &
    (
        (final_df['amount_max'] > final_df['aqb'] * 10) |
        (final_df['amount_sum'] > final_df['aqb'] * 10)
    ) &
    (final_df['percentage_anomalous_txns'] >= 10)
)
final_df.loc[suspicious_conditions, 'account_label'] = 'Suspicious'
print(f"Labeled {final_df['account_label'].value_counts().get('Suspicious', 0)} accounts as 'Suspicious'.")


# ==============================================================================
# 6. TRAIN FINAL CLASSIFIER (RANDOM FOREST)
# ==============================================================================
print("STEP 6: Training final RandomForestClassifier...")
# One-hot encode categorical features from the customer data
final_df.drop(columns=['customer_joining_date', 'last_txn_date', 'dob'], inplace=True) # Drop datetime objects
customer_categorical_cols = final_df.select_dtypes(include=['object', 'category']).columns.tolist()
customer_categorical_cols = [col for col in customer_categorical_cols if col not in ['cust_id', 'account_label']]

final_df_encoded = pd.get_dummies(final_df, columns=customer_categorical_cols)

# Prepare data for training
target_column = 'account_label'
potential_identifiers = ['cust_id', 'acct_num']
# Align columns with encoded dataframe
all_cols = final_df_encoded.columns
feature_columns = [col for col in all_cols if col not in [target_column] + potential_identifiers]

X = final_df_encoded[feature_columns]
y = final_df_encoded[target_column]

# Handle potential missing columns if a category is not present during prediction
# This is handled by saving the feature_columns list
X.fillna(0, inplace=True)

# Encode Target Variable
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# Scale Features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train the final classifier
model_rf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced_subsample', n_jobs=-1)
model_rf.fit(X_scaled, y_encoded)
print("Classifier training complete.")

# ==============================================================================
# 7. SAVE ARTIFACTS
# ==============================================================================
print("STEP 7: Saving model artifacts...")
joblib.dump(model_rf, 'random_forest_model.joblib')
joblib.dump(scaler, 'scaler.joblib')
joblib.dump(le, 'label_encoder.joblib')
joblib.dump(feature_columns, 'feature_columns.joblib') # Saves the exact column order

print("--- All artifacts saved successfully. ---")
print("You can now move the .joblib files to your server.")