import json
from datetime import datetime
from typing import Dict, List, Optional

class Transaction:
    def __init__(self, timestamp: str, crypto_type: str, crypto_amount: float, 
                 eur_amount: float, recipient: str, status: str):
        self.timestamp = timestamp
        self.crypto_type = crypto_type
        self.crypto_amount = crypto_amount
        self.eur_amount = eur_amount
        self.recipient = recipient
        self.status = status

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "crypto_type": self.crypto_type,
            "crypto_amount": self.crypto_amount,
            "eur_amount": self.eur_amount,
            "recipient": self.recipient,
            "status": self.status
        }

class CryptoWallet:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.btc_balance = 0.012
        self.eth_balance = 0.5
        self.xeur_balance = 50.0
        self.transaction_history: List[Transaction] = []
        self.load_user_data()

    def load_user_data(self):
        """Load user data from JSON file if it exists"""
        try:
            with open(f"user_{self.user_id}.json", "r") as f:
                data = json.load(f)
                self.btc_balance = data.get("btc_balance", self.btc_balance)
                self.eth_balance = data.get("eth_balance", self.eth_balance)
                self.xeur_balance = data.get("xeur_balance", self.xeur_balance)
                self.transaction_history = [
                    Transaction(**tx) for tx in data.get("transactions", [])
                ]
        except FileNotFoundError:
            # If file doesn't exist, use default values
            pass

    def save_user_data(self):
        """Save user data to JSON file"""
        data = {
            "btc_balance": self.btc_balance,
            "eth_balance": self.eth_balance,
            "xeur_balance": self.xeur_balance,
            "transactions": [tx.to_dict() for tx in self.transaction_history]
        }
        with open(f"user_{self.user_id}.json", "w") as f:
            json.dump(data, f, indent=2)

    def convert_crypto_to_xeur(self, crypto_type: str, amount_in_eur: float) -> bool:
        """Convert crypto to xEUR"""
        # Mock conversion rates
        rates = {
            'BTC': 40000,  # 1 BTC = 40,000 EUR
            'ETH': 2000    # 1 ETH = 2,000 EUR
        }
        
        crypto_amount = amount_in_eur / rates[crypto_type]
        
        if crypto_type == 'BTC' and self.btc_balance >= crypto_amount:
            self.btc_balance -= crypto_amount
            self.xeur_balance += amount_in_eur
            # Add conversion transaction
            self.add_transaction(
                crypto_type=crypto_type,
                crypto_amount=crypto_amount,
                eur_amount=amount_in_eur,
                recipient="Internal Conversion",
                status="CRYPTO_TO_xEUR"
            )
            return True
        elif crypto_type == 'ETH' and self.eth_balance >= crypto_amount:
            self.eth_balance -= crypto_amount
            self.xeur_balance += amount_in_eur
            # Add conversion transaction
            self.add_transaction(
                crypto_type=crypto_type,
                crypto_amount=crypto_amount,
                eur_amount=amount_in_eur,
                recipient="Internal Conversion",
                status="CRYPTO_TO_xEUR"
            )
            return True
        return False

    def withdraw_xeur(self, amount: float, recipient: str) -> bool:
        """Withdraw xEUR for payment"""
        if self.xeur_balance >= amount:
            self.xeur_balance -= amount
            # Add withdrawal transaction
            self.add_transaction(
                crypto_type="xEUR",
                crypto_amount=amount,
                eur_amount=amount,
                recipient=recipient,
                status="xEUR_WITHDRAWAL"
            )
            self.save_user_data()
            return True
        return False

    def add_transaction(self, crypto_type: str, crypto_amount: float, 
                       eur_amount: float, recipient: str, status: str):
        """Add a transaction to the history"""
        transaction = Transaction(
            timestamp=datetime.now().isoformat(),
            crypto_type=crypto_type,
            crypto_amount=crypto_amount,
            eur_amount=eur_amount,
            recipient=recipient,
            status=status
        )
        self.transaction_history.append(transaction)
        self.save_user_data()

    def get_balances(self) -> Dict[str, float]:
        return {
            'BTC': self.btc_balance,
            'ETH': self.eth_balance,
            'xEUR': self.xeur_balance
        }

    def get_transaction_history(self) -> List[Dict]:
        return [tx.to_dict() for tx in self.transaction_history]

    def reset_balances(self):
        """Reset balances to default values"""
        self.btc_balance = 0.012
        self.eth_balance = 0.5
        self.xeur_balance = 50.0
        self.transaction_history = []
        self.save_user_data() 