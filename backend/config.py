# config.py
import os

# --- Database Connection Parameters ---
DB_CONNECTION_PARAMS = {
    "host": "34.47.219.225",
    "database": "unitedb",
    "user": "unitedb_user",
    "password": "password123",
    "port": "5432"
}

# --- Keycloak Configuration ---
KEYCLOAK_CONFIG = {
    "server_url": "https://34.47.219.225:8443/",
    "realm_name": "bank_oauth",
    "client_id": "python-client",
    "client_secret_key": "zP2VkwyJqVzIw3a0BvyWttUoZi77YoVf",
    "verify_ssl": False # Set to True if you have valid SSL certificates
}

# Get the absolute path of the directory where config.py is located (i.e., the 'backend' folder)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- File Upload and Error Log Directories ---
# Create paths relative to the backend folder
UPLOAD_DIR = os.path.join(BASE_DIR, "fraud_uploads")
ERROR_LOG_DIR = os.path.join(BASE_DIR, "bulk_processing_errors")

# Ensure these directories exist when the config is loaded
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(ERROR_LOG_DIR, exist_ok=True)

# --- Case Management Configuration ---
# Risk Officer Delayed Cases (for Super User)
RISK_OFFICER_DELAY_THRESHOLD_DAYS = 5  # Days without action for risk officer cases

# Department Delayed Cases (for Supervisors)
COMPLIANCE_DEPARTMENT_DELAY_THRESHOLD_DAYS = 3  # Days without action for Compliance department cases
FINANCE_DEPARTMENT_DELAY_THRESHOLD_DAYS = 10     # Days without action for Finance department cases

# Legacy setting (keeping for backward compatibility)
DELAY_THRESHOLD_DAYS = 60  # Cases older than this many days with status 'new' are considered delayed
