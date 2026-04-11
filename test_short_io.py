import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("PUBLIC_SHORT_API")
domain = os.getenv("SHORT_IO_DOMAIN")

print(f"Key: {api_key}")
print(f"Domain: {domain}")

# List domains
print("--- FETCHING DOMAINS ---")
try:
    response = requests.get("https://api.short.io/api/domains", headers={"authorization": api_key})
    print(f"Domains Status: {response.status_code}")
    print(f"Domains Body: {response.text}")
except Exception as e:
    print(f"Domains Error: {e}")

# Try to list links for this domain
print("\n--- FETCHING LINKS ---")
try:
    response = requests.get(f"https://api.short.io/api/links?domain={domain}", headers={"authorization": api_key})
    print(f"Links Status: {response.status_code}")
    print(f"Links Body: {response.text[:200]}...") # Keep it short but readable
except Exception as e:
    print(f"Links Error: {e}")
