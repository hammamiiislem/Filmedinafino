import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class FlouciService:
    BASE_URL = "https://developers.flouci.com/api"
    
    def __init__(self):
        self.app_token = getattr(settings, "FLOUCI_APP_TOKEN", "")
        self.app_public = getattr(settings, "FLOUCI_APP_PUBLIC", "")
        self.app_secret = getattr(settings, "FLOUCI_APP_SECRET", "")

    def generate_payment(self, amount_dt, success_url, fail_url, developer_id):
        """
        amount_dt: Amount in Dinars (will be converted to millimes if needed, 
        but Flouci usually takes millimes/cents)
        """
        endpoint = f"{self.BASE_URL}/generate_payment"
        
        # Convert TND to millimes (cents)
        amount_millimes = int(float(amount_dt) * 1000)
        
        payload = {
            "app_token": self.app_token,
            "app_public": self.app_public,
            "amount": amount_millimes,
            "accept_card": "true",
            "session_timeout_secs": 1200,
            "success_link": success_url,
            "fail_link": fail_url,
            "developer_tracking_id": str(developer_id)
        }
        
        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json() # contains 'payment_id' and 'link'
        except Exception as e:
            logger.error(f"Flouci error: {e}")
            return None

    def verify_payment(self, payment_id):
        endpoint = f"{self.BASE_URL}/verify_payment/{payment_id}"
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            return response.json() # success true/false
        except Exception as e:
            logger.error(f"Flouci verify error: {e}")
            return None

class KonnectService:
    BASE_URL = "https://api.konnect.network/api/v2"
    
    def __init__(self):
        self.api_key = getattr(settings, "KONNECT_API_KEY", "")
        self.wallet_id = getattr(settings, "KONNECT_WALLET_ID", "")

    def init_payment(self, amount_dt, first_name, last_name, email, success_url, fail_url):
        endpoint = f"{self.BASE_URL}/payments/init-payment"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Konnect takes amount in TND but sometimes milli? Actually V2 is often TND.
        payload = {
            "receiverWalletId": self.wallet_id,
            "amount": float(amount_dt),
            "token": "TND",
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "add_Ret_Url": success_url,
            "fail_Ret_Url": fail_url
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            return response.json() # contains 'payUrl' and 'paymentRef'
        except Exception as e:
            logger.error(f"Konnect error: {e}")
            return None
