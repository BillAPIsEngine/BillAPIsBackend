import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'supersecretkey')
    UPLOAD_FOLDER = os.getenv('INVOICE_TEMPLATE_UPLOAD_FOLDER', 'uploads/')
    ALLOWED_EXTENSIONS = {'html'}

    # API Managers
    API_MANAGERS = {
        "WSO2": os.getenv('WSO2_API_URL'),
        "Apigee": os.getenv('APIGEE_API_URL'),
        "Kong": os.getenv('KONG_API_URL'),
        "AWS": os.getenv('AWS_API_URL'),
        "Azure": os.getenv('AZURE_API_URL')
    }

    # ERP Systems
    ERP_SYSTEMS = {
        "SAP": os.getenv('ERP_SAP_API_URL'),
        "Odoo": os.getenv('ERP_ODOO_API_URL'),
        "OracleFusion": os.getenv('ERP_ORACLE_FUSION_API_URL')
    }

    # Pricing Configuration
    PRICE_MAPPING = {
        "monthly": 0.10,
        "weekly": 0.25,
        "biweekly": 0.50,
        "annually": 1.00,
        "hourly": 0.02
    }

    DEFAULT_BILLING_FREQUENCY = os.getenv('DEFAULT_BILLING_FREQUENCY', 'monthly')

    SQLALCHEMY_DATABASE_URI = 'sqlite:///your_database.db'  # Change this for your actual database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your_secret_key'
