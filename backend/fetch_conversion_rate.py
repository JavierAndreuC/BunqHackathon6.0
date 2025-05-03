import os
import requests

import requests, json

API_KEY = 'f2bc3721-aa8b-415f-9617-0a248e630522'
URL = "https://api.livecoinwatch.com/coins/single"
HEADERS = {
    "content-type": "application/json",
    "x-api-key": API_KEY,
}


def fetch_rate(code: str, currency: str) -> float:
    '''
    Fetches the conversion rate from a crypto currency to a real currency

    :param code: The cryptocurrency code (e.g. "BTC", "ETH").
    :param currency: The currency to convert to (e.g. "EUR", "USD").
    :type code: str
    :type currency: str
    :return: The conversion rate in EUR.
    :rtype: float
    '''
    payload = json.dumps({
        "currency": currency,
        "code": code,
        "meta": False
    })
    resp = requests.post(URL, headers=HEADERS, data=payload)
    resp.raise_for_status()
    data = resp.json()
    return data["rate"]

if __name__ == "__main__":
    btc_eur = fetch_rate("BTC", "EUR")
    eth_eur = fetch_rate("ETH", "USD")
    print(f"1 BTC = {btc_eur:.2f} EUR")
    print(f"1 ETH = {eth_eur:.2f} USD")
