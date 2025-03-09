import requests
from config import Config

def fetch_api_details(api_manager):
    """Fetch details from an API Manager."""
    url = Config.API_MANAGERS.get(api_manager)
    if url:
        return requests.get(url).json()
    return {}

def fetch_datadog_usage():
    """Fetch API usage from Datadog."""
    url = os.getenv('DATADOG_API_URL')
    return requests.get(url).json()

def fetch_elk_usage():
    """Fetch API usage from ELK."""
    url = os.getenv('ELK_API_URL')
    return requests.get(url).json()
