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

# --- File Upload and Error Log Directories ---
UPLOAD_DIR = "/home/ubuntu/fraud_uploads"
ERROR_LOG_DIR = "/home/ubuntu/bulk_processing_errors"

# Ensure these directories exist when the config is loaded
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(ERROR_LOG_DIR, exist_ok=True)
