# Crypto Payment Simulator

A proof-of-concept application that demonstrates how users can pay with cryptocurrencies (BTC/ETH) by converting them to xEUR through Bunq.

## Features

- Convert BTC/ETH to xEUR for payments
- Track transaction history
- View spending trends
- Simple and intuitive user interface
- Integration with Bunq API

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your Bunq API credentials:
   - Create a `.env` file in the project root
   - Add your Bunq API key:
   ```
   BUNQ_API_KEY=your_api_key_here
   ```

3. Run the application:
```bash
streamlit run app.py
```

## Usage

1. Click "Initialize System" to set up the Bunq connection and create a test account
2. View your crypto and xEUR balances
3. Select a crypto type (BTC/ETH) and enter the amount in EUR
4. Click "Convert and Pay" to make a payment
5. View transaction history and spending trends
6. Use "Reset Balances" to restore default wallet values

## Notes

- This is a proof-of-concept implementation
- Uses mock conversion rates for BTC and ETH
- Transactions are stored locally in JSON format
- Requires a valid Bunq API key for testing 