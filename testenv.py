from bunq.sdk.context.api_context import ApiContext
from bunq.sdk.context.bunq_context import BunqContext
from bunq import ApiEnvironmentType
from bunq.sdk.model.generated.endpoint import MonetaryAccountBank, Payment, User, RequestInquiry
from bunq.sdk.model.generated.object_ import Amount, Pointer
import time
import os
import random
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
        """Simulate converting crypto to xEUR"""
        # Mock conversion rates
        rates = {
            'BTC': 40000,  # 1 BTC = 40,000 EUR
            'ETH': 2000    # 1 ETH = 2,000 EUR
        }
        
        crypto_amount = amount_in_eur / rates[crypto_type]
        
        if crypto_type == 'BTC' and self.btc_balance >= crypto_amount:
            self.btc_balance -= crypto_amount
            self.xeur_balance += amount_in_eur
            return True
        elif crypto_type == 'ETH' and self.eth_balance >= crypto_amount:
            self.eth_balance -= crypto_amount
            self.xeur_balance += amount_in_eur
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

def print_progress(message):
    print(f"\n[PROGRESS] {message}")

def retry_with_backoff(func, max_retries=5, initial_delay=2):
    """Execute a function with exponential backoff retry logic"""
    retries = 0
    delay = initial_delay
    
    while retries < max_retries:
        try:
            print_progress(f"Attempting operation (attempt {retries + 1}/{max_retries})")
            print_progress(f"Waiting {delay} seconds before making request...")
            time.sleep(delay)
            
            result = func()
            print_progress("Operation successful!")
            return result
        except Exception as e:
            retries += 1
            if retries == max_retries:
                print(f"\n[ERROR] Max retries ({max_retries}) reached. Last error: {str(e)}")
                raise
            
            delay *= 2
            print(f"\n[WARNING] Error occurred. Retrying in {delay} seconds... (Attempt {retries}/{max_retries})")
            time.sleep(delay)
    
    raise Exception("Max retries reached")

def setup_api_context():
    """Create or load API context"""
    context_file = "bunq_api_context.conf"
    
    if os.path.exists(context_file):
        print_progress("Found existing API context file")
        try:
            print_progress("Attempting to load existing context...")
            api_context = ApiContext.restore(context_file)
            print_progress("Successfully loaded existing context")
            return api_context
        except Exception as e:
            print(f"\n[WARNING] Failed to load existing context: {e}")
            print_progress("Deleting invalid context file...")
            os.remove(context_file)
            print_progress("Creating new context...")
    
    print_progress("Creating new API context...")
    api_context = ApiContext.create(
        ApiEnvironmentType.SANDBOX,
        "sandbox_9dbf8a1c3304f541e0fb522a49379846f86539bcc802d23dd05af088",
        "My Device Description"
    )
    
    print_progress("Saving API context for future use...")
    api_context.save(context_file)
    return api_context

def create_test_account():
    """Create a test monetary account in the sandbox environment"""
    print("\n=== Creating Test Account ===")
    
    # First, get the user info
    print_progress("Getting user information...")
    user = User.get().value
    print(f"User Info: {user}")
    
    # Create a new monetary account
    print_progress("Creating new monetary account...")
    currency = "EUR"
    description = "Test Account"
    
    response = MonetaryAccountBank.create(
        currency=currency,
        description=description,
        daily_limit=Amount("1000.00", currency),
        status="ACTIVE"
    )
    
    account_id = response.value
    print(f"\n[SUCCESS] Created new monetary account:")
    print(f"Account ID: {account_id}")
    
    # Get the account details including IBAN
    account_details = MonetaryAccountBank.get(account_id).value
    print(f"Account IBAN: {account_details.alias[0].value}")
    
    return account_details

def make_payment(amount, recipient_iban, recipient_name="Test Account"):
    """Make a payment using Bunq"""
    print_progress(f"Making payment of {amount} EUR to IBAN {recipient_iban}")
    return Payment.create(
        amount=Amount(str(amount), "EUR"),
        counterparty_alias=Pointer("IBAN", recipient_iban, recipient_name),
        description="Crypto payment conversion"
    ).value

def request_spending_money(account_id):
    """Request money from the Sugar Daddy account in sandbox"""
    print("\n=== Requesting Spending Money ===")
    print_progress("Requesting €500 from Sugar Daddy account...")
    
    request = RequestInquiry.create(
        amount_inquired=Amount("500.00", "EUR"),
        counterparty_alias=Pointer("EMAIL", "sugardaddy@bunq.com"),
        description="Test money please!",
        allow_bunqme=False
    )
    
    print("[SUCCESS] Money request sent!")
    print("Waiting for money to arrive...")
    
    # Wait and check balance
    max_attempts = 5
    for attempt in range(max_attempts):
        time.sleep(5)  # Wait 5 seconds between checks
        account = MonetaryAccountBank.get(account_id).value
        balance = float(account.balance.value)
        print(f"Current balance: €{balance}")
        
        if balance >= 500:
            print("[SUCCESS] Money received!")
            return True
        
        if attempt < max_attempts - 1:
            print("Still waiting for money...")
    
    print("[WARNING] Timeout waiting for money to arrive")
    return False

print("\n=== Starting Crypto Payment Simulator ===")
print("This script simulates crypto payments through Bunq")

# Initialize API context
print_progress("Setting up API context...")
api_context = retry_with_backoff(setup_api_context)

# Load the API context into the SDK
print_progress("Loading API context into SDK...")
BunqContext.load_api_context(api_context)

# Create a test account
test_account = create_test_account()

# Request some money for testing
if not request_spending_money(test_account.id_):
    print("[ERROR] Failed to receive test money. Payments may fail.")

# Create a wallet
wallet = CryptoWallet(test_account.id_)
print("\n[INFO] Initial wallet balances:")
balances = wallet.get_balances()
for currency, balance in balances.items():
    print(f"{currency}: {balance}")

# Update payment code to use the new test account
print("\n=== Simulating BTC Payment ===")
amount_eur = 10.0
print(f"Amount in EUR: {amount_eur}")

# Convert BTC to xEUR and make payment
if wallet.convert_crypto_to_xeur("BTC", amount_eur):
    try:
        # Check account balance before payment
        account = MonetaryAccountBank.get(test_account.id_).value
        balance = float(account.balance.value)
        print(f"\nAccount balance before payment: €{balance}")
        
        if balance < amount_eur:
            print(f"[ERROR] Insufficient balance (€{balance}) for payment of €{amount_eur}")
        else:
            # Make payment to our own test account
            payment_id = make_payment(
                amount_eur,
                test_account.alias[0].value,  # Use the IBAN from the account
                test_account.description  # Use the account description as name
            )
            print(f"\n[SUCCESS] Payment completed!")
            print(f"Payment ID: {payment_id}")
            
            # Check new balance
            account = MonetaryAccountBank.get(test_account.id_).value
            balance = float(account.balance.value)
            print(f"Account balance after payment: €{balance}")
            
            print("\nNew wallet balances:")
            balances = wallet.get_balances()
            for currency, balance in balances.items():
                print(f"{currency}: {balance}")
    except Exception as e:
        print(f"\n[ERROR] Payment failed: {str(e)}")
else:
    print("\n[ERROR] Not enough BTC balance for the conversion")

print("\n=== Script completed successfully ===")