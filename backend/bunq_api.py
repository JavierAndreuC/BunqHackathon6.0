import time
import os
import json
from bunq.sdk.context.api_context import ApiContext
from bunq.sdk.context.bunq_context import BunqContext
from bunq import ApiEnvironmentType
from bunq.sdk.model.generated.endpoint import MonetaryAccountBank, Payment, RequestInquiry, RequestResponse
from bunq.sdk.model.generated.object_ import Amount, Pointer

# Mock mode for development
MOCK_MODE = True

def retry_with_backoff(func, max_retries=5, initial_delay=3):
    """Execute a function with exponential backoff retry logic"""
    retries = 0
    delay = initial_delay
    
    while retries < max_retries:
        try:
            return func()
        except Exception as e:
            if "429" in str(e):  # Rate limit error
                retries += 1
                if retries == max_retries:
                    raise
                print(f"Rate limited. Waiting {delay} seconds before retry {retries}/{max_retries}...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                raise

class MockMonetaryAccount:
    def __init__(self):
        self.id_ = 12345
        self.balance = type('obj', (object,), {'value': '1000.00'})
        self.alias = [type('obj', (object,), {'value': 'NL12BUNQ1234567890'})]
        self.description = "Test Account"

class BunqAPI:
    def __init__(self):
        self.api_context = None
        self.test_account = None
        if MOCK_MODE:
            self.test_account = MockMonetaryAccount()

    def setup(self):
        """Setup Bunq API context and create test account"""
        if MOCK_MODE:
            print("Running in mock mode - using simulated Bunq API")
            return True

        try:
            # First, setup API context with delay
            print("Setting up API context...")
            self.api_context = self._setup_api_context()
            time.sleep(3)  # Wait before loading context
            
            print("Loading API context...")
            BunqContext.load_api_context(self.api_context)
            time.sleep(3)  # Wait after loading context
            
            # Check if we already have a test account
            if self._load_existing_account():
                print("Using existing test account...")
                return True
            
            # Create new test account with retry
            print("Creating new test account...")
            def create_account():
                response = MonetaryAccountBank.create(
                    currency="EUR",
                    description="Test Account",
                    daily_limit=Amount("1000.00", "EUR"),
                    status="ACTIVE"
                )
                return response.value
            
            account_id = retry_with_backoff(create_account)
            time.sleep(3)  # Wait after account creation
            
            print("Getting account details...")
            self.test_account = MonetaryAccountBank.get(account_id).value
            time.sleep(3)  # Wait after getting account
            
            # Save account details for future use
            self._save_account_details()
            
            return True
        except Exception as e:
            print(f"Failed to setup Bunq: {str(e)}")
            return False

    def _load_existing_account(self):
        """Try to load existing account details"""
        if MOCK_MODE:
            return True

        try:
            account_file = "test_account.json"
            if os.path.exists(account_file):
                with open(account_file, "r") as f:
                    account_id = int(f.read().strip())
                    self.test_account = MonetaryAccountBank.get(account_id).value
                    return True
        except Exception:
            pass
        return False

    def _save_account_details(self):
        """Save account ID for future use"""
        if MOCK_MODE:
            return

        try:
            account_file = "test_account.json"
            with open(account_file, "w") as f:
                f.write(str(self.test_account.id_))
        except Exception:
            pass

    def _setup_api_context(self):
        """Create or load API context"""
        if MOCK_MODE:
            return None

        context_file = "bunq_api_context.conf"
        
        if os.path.exists(context_file):
            try:
                return ApiContext.restore(context_file)
            except Exception:
                os.remove(context_file)
        
        api_context = ApiContext.create(
            ApiEnvironmentType.SANDBOX,
            "sandbox_9dbf8a1c3304f541e0fb522a49379846f86539bcc802d23dd05af088",
            "My Device Description"
        )
        api_context.save(context_file)
        return api_context

    def _request_initial_balance(self):
        """Request initial balance from Sugar Daddy"""
        try:
            def make_request():
                RequestInquiry.create(
                    amount_inquired=Amount("100.00", "EUR"),
                    counterparty_alias=Pointer("EMAIL", "sugardaddy@bunq.com"),
                    description="Initial balance for testing",
                    allow_bunqme=False
                )
            
            retry_with_backoff(make_request)
            time.sleep(3)  # Wait for the request to process
        except Exception as e:
            print(f"Failed to request initial balance: {str(e)}")

    def get_balance(self) -> float:
        """Get current account balance"""
        if MOCK_MODE:
            return 1000.0

        try:
            def get_account():
                account = MonetaryAccountBank.get(self.test_account.id_).value
                return float(account.balance.value)
            
            return retry_with_backoff(get_account)
        except Exception as e:
            print(f"Failed to get balance: {str(e)}")
            return 0.0

    def make_payment(self, amount: float, recipient_iban: str, recipient_name: str) -> bool:
        """Make a payment using Bunq"""
        if MOCK_MODE:
            print(f"Mock payment: Sending €{amount} to {recipient_name} ({recipient_iban})")
            return True

        try:
            def create_payment():
                Payment.create(
                    amount=Amount(str(amount), "EUR"),
                    counterparty_alias=Pointer("IBAN", recipient_iban, recipient_name),
                    description="Crypto payment conversion"
                )
                return True
            
            return retry_with_backoff(create_payment)
        except Exception as e:
            print(f"Payment failed: {str(e)}")
            return False

    def request_money(self, amount: float = 500.0) -> bool:
        """Request money from Sugar Daddy account"""
        if MOCK_MODE:
            print(f"Mock request: Requesting €{amount} from Sugar Daddy")
            return True

        try:
            def make_request():
                RequestInquiry.create(
                    amount_inquired=Amount(str(amount), "EUR"),
                    counterparty_alias=Pointer("EMAIL", "sugardaddy@bunq.com"),
                    description="Test money please!",
                    allow_bunqme=False
                )
                return True
            
            return retry_with_backoff(make_request)
        except Exception as e:
            print(f"Failed to request money: {str(e)}")
            return False

    def get_pending_requests(self):
        """Get all pending money requests"""
        if MOCK_MODE:
            return []

        try:
            def get_requests():
                requests = RequestResponse.list().value
                return [req for req in requests if req.status == "PENDING"]
            
            return retry_with_backoff(get_requests)
        except Exception as e:
            print(f"Failed to get pending requests: {str(e)}")
            return []

    def accept_request(self, request_id: int) -> bool:
        """Accept a money request"""
        if MOCK_MODE:
            print(f"Mock accept: Accepting request {request_id}")
            return True

        try:
            def accept():
                RequestResponse.update(
                    request_id,
                    status="ACCEPTED"
                )
                return True
            
            return retry_with_backoff(accept)
        except Exception as e:
            print(f"Failed to accept request: {str(e)}")
            return False 