import time
import os
from bunq.sdk.context.api_context import ApiContext
from bunq.sdk.context.bunq_context import BunqContext
from bunq import ApiEnvironmentType
from bunq.sdk.model.generated.endpoint import MonetaryAccountBank, Payment, RequestInquiry, RequestResponse
from bunq.sdk.model.generated.object_ import Amount, Pointer

class BunqAPI:
    def __init__(self):
        self.api_context = None
        self.test_account = None

    def setup(self):
        """Setup Bunq API context and create test account"""
        try:
            self.api_context = self._setup_api_context()
            BunqContext.load_api_context(self.api_context)
            
            # Create test account
            response = MonetaryAccountBank.create(
                currency="EUR",
                description="Test Account",
                daily_limit=Amount("1000.00", "EUR"),
                status="ACTIVE"
            )
            account_id = response.value
            self.test_account = MonetaryAccountBank.get(account_id).value
            
            # Request initial balance
            self._request_initial_balance()
            return True
        except Exception as e:
            print(f"Failed to setup Bunq: {str(e)}")
            return False

    def _setup_api_context(self):
        """Create or load API context"""
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
            RequestInquiry.create(
                amount_inquired=Amount("100.00", "EUR"),
                counterparty_alias=Pointer("EMAIL", "sugardaddy@bunq.com"),
                description="Initial balance for testing",
                allow_bunqme=False
            )
            time.sleep(2)  # Wait for the request to process
        except Exception as e:
            print(f"Failed to request initial balance: {str(e)}")

    def get_balance(self) -> float:
        """Get current account balance"""
        try:
            account = MonetaryAccountBank.get(self.test_account.id_).value
            return float(account.balance.value)
        except Exception as e:
            print(f"Failed to get balance: {str(e)}")
            return 0.0

    def make_payment(self, amount: float, recipient_iban: str, recipient_name: str) -> bool:
        """Make a payment using Bunq"""
        try:
            Payment.create(
                amount=Amount(str(amount), "EUR"),
                counterparty_alias=Pointer("IBAN", recipient_iban, recipient_name),
                description="Crypto payment conversion"
            )
            return True
        except Exception as e:
            print(f"Payment failed: {str(e)}")
            return False

    def request_money(self, amount: float = 500.0) -> bool:
        """Request money from Sugar Daddy account"""
        try:
            RequestInquiry.create(
                amount_inquired=Amount(str(amount), "EUR"),
                counterparty_alias=Pointer("EMAIL", "sugardaddy@bunq.com"),
                description="Test money please!",
                allow_bunqme=False
            )
            return True
        except Exception as e:
            print(f"Failed to request money: {str(e)}")
            return False

    def get_pending_requests(self):
        """Get all pending money requests"""
        try:
            requests = RequestResponse.list().value
            return [req for req in requests if req.status == "PENDING"]
        except Exception as e:
            print(f"Failed to get pending requests: {str(e)}")
            return []

    def accept_request(self, request_id: int) -> bool:
        """Accept a money request"""
        try:
            RequestResponse.update(
                request_id,
                status="ACCEPTED"
            )
            return True
        except Exception as e:
            print(f"Failed to accept request: {str(e)}")
            return False 