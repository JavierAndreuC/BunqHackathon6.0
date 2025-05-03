# Crypto Payment Simulator with Bunq Integration

A demonstration of how crypto payments can be processed through Bunq by converting cryptocurrencies to a stablecoin (xEUR) for transactions.

## Project Structure

```
.
├── backend/                 # Backend components
│   ├── __init__.py
│   ├── wallet.py           # Crypto wallet implementation
│   └── bunq_api.py         # Bunq API interface
├── frontend/               # Frontend components
│   ├── __init__.py
│   └── app.py             # Streamlit UI application
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Features

- Convert BTC/ETH to xEUR (stablecoin)
- Make payments using converted xEUR
- Track transaction history
- Visualize spending trends
- Manage crypto and fiat balances

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the Streamlit app:
   ```bash
   cd frontend
   streamlit run app.py
   ```

## How It Works

1. User selects crypto (BTC/ETH) and amount to spend
2. System converts crypto to xEUR at current rates
3. xEUR is used to make the payment through Bunq
4. Payment is sent to merchant's IBAN
5. Transaction history shows the complete flow

## Development

- Backend team can work on `backend/` directory
- Frontend team can work on `frontend/` directory
- Both teams can work simultaneously without conflicts

## Notes

- Uses Bunq sandbox environment for testing
- Mock conversion rates for demonstration
- Real implementation would integrate with crypto exchanges 