import json
import sys

import requests


API_URL = "https://api.playenginecup.com/api/points/transfer"
API_KEY = "b1b941f2180732c4cb55515a0fef6a28ufeur9384928f89yhe2380dh8hc0j329hrjd239p"
EMAIL = "tobiaidetyc@gmail.com"
AMOUNT = 0.1
TRANSFER_ID = "11111111-1111-4111-8111-111111111111"


def mask_key(key: str) -> str:
    if not key:
        return "<empty>"
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:4]}...{key[-4:]}"


def transfer_points() -> int:
    if not EMAIL:
        print("❌ EMAIL is empty. Set a valid email in this file.")
        return 1

    if AMOUNT <= 0:
        print("❌ Amount must be greater than 0.")
        return 1

    if not API_KEY:
        print("❌ API_KEY is empty. Set your x-playshop-api-key in this file.")
        return 1

    if not TRANSFER_ID:
        print("❌ TRANSFER_ID is empty. Set a UUID in this file.")
        return 1

    headers = {
        "Content-Type": "application/json",
        "x-playshop-api-key": API_KEY,
    }
    payload = {
        "email": EMAIL,
        "amount": AMOUNT,
        "transfer_id": TRANSFER_ID,
    }

    print("🧪 Testing points transfer endpoint")
    print("=" * 50)
    print(f"URL: {API_URL}")
    print(f"Email: {EMAIL}")
    print(f"Amount: {AMOUNT}")
    print(f"Transfer ID: {TRANSFER_ID}")
    print(f"API Key: {mask_key(API_KEY)}")

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
    except requests.RequestException as exc:
        print(f"\n❌ Request error: {exc}")
        return 1

    print("\n📥 Response")
    print("=" * 50)
    print(f"Status: {response.status_code}")

    try:
        print(json.dumps(response.json(), indent=2))
    except ValueError:
        print(response.text)

    if 200 <= response.status_code < 300:
        print("\n✅ Transfer request succeeded")
        return 0

    print("\n⚠️ Transfer request failed")
    return 1


def main() -> int:
    return transfer_points()


if __name__ == "__main__":
    sys.exit(main())
