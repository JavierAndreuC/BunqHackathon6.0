import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from testenv import CryptoWallet, setup_api_context, BunqContext, ApiContext, ApiEnvironmentType
from bunq.sdk.model.generated.endpoint import MonetaryAccountBank, Payment, RequestInquiry, RequestResponse
from bunq.sdk.model.generated.object_ import Amount, Pointer
import time

# Initialize session state
if 'wallet' not in st.session_state:
    st.session_state.wallet = None
if 'api_context' not in st.session_state:
    st.session_state.api_context = None
if 'test_account' not in st.session_state:
    st.session_state.test_account = None
if 'account_balance' not in st.session_state:
    st.session_state.account_balance = 0.0
if 'pending_requests' not in st.session_state:
    st.session_state.pending_requests = []

# Mock conversion rates (in a real app, these would come from an exchange)
CONVERSION_RATES = {
    'BTC': 40000,  # 1 BTC = 40,000 EUR
    'ETH': 2000    # 1 ETH = 2,000 EUR
}

def get_pending_requests():
    """Get all pending money requests"""
    try:
        requests = RequestResponse.list().value
        return [req for req in requests if req.status == "PENDING"]
    except Exception as e:
        st.error(f"Failed to get pending requests: {str(e)}")
        return []

def accept_request(request_id: int) -> bool:
    """Accept a money request"""
    try:
        RequestResponse.update(
            request_id,
            status="ACCEPTED"
        )
        return True
    except Exception as e:
        st.error(f"Failed to accept request: {str(e)}")
        return False

def request_money(amount: float = 500.0) -> bool:
    """Request money from Sugar Daddy account"""
    try:
        request = RequestInquiry.create(
            amount_inquired=Amount(str(amount), "EUR"),
            counterparty_alias=Pointer("EMAIL", "sugardaddy@bunq.com"),
            description="Test money please!",
            allow_bunqme=False
        )
        st.success(f"Request for €{amount:.2f} sent to Sugar Daddy!")
        return True
    except Exception as e:
        st.error(f"Failed to request money: {str(e)}")
        return False

def check_balance() -> float:
    """Check the current account balance"""
    try:
        account = MonetaryAccountBank.get(st.session_state.test_account.id_).value
        return float(account.balance.value)
    except Exception as e:
        st.error(f"Failed to check balance: {str(e)}")
        return 0.0

def setup_bunq():
    """Setup Bunq API context and create test account"""
    try:
        api_context = setup_api_context()
        BunqContext.load_api_context(api_context)
        st.session_state.api_context = api_context
        
        # Create test account
        response = MonetaryAccountBank.create(
            currency="EUR",
            description="Test Account",
            daily_limit=Amount("1000.00", "EUR"),
            status="ACTIVE"
        )
        account_id = response.value
        account = MonetaryAccountBank.get(account_id).value
        st.session_state.test_account = account
        
        # Create wallet
        st.session_state.wallet = CryptoWallet(account_id)
        
        # Request initial balance of €100
        request = RequestInquiry.create(
            amount_inquired=Amount("100.00", "EUR"),
            counterparty_alias=Pointer("EMAIL", "sugardaddy@bunq.com"),
            description="Initial balance for testing",
            allow_bunqme=False
        )
        
        st.success("Account created successfully! Requesting initial balance of €100...")
        time.sleep(2)  # Wait for the request to process
        return True
    except Exception as e:
        st.error(f"Failed to setup Bunq: {str(e)}")
        return False

def make_payment(amount: float, recipient_iban: str, recipient_name: str) -> bool:
    """Make a payment using Bunq"""
    try:
        payment = Payment.create(
            amount=Amount(str(amount), "EUR"),
            counterparty_alias=Pointer("IBAN", recipient_iban, recipient_name),
            description="Crypto payment conversion"
        )
        return True
    except Exception as e:
        st.error(f"Payment failed: {str(e)}")
        return False

# Streamlit UI
st.title("Crypto Payment Simulator")
st.write("Convert and pay with crypto through Bunq")

# Setup section
if st.session_state.wallet is None:
    if st.button("Initialize System"):
        if setup_bunq():
            st.success("System initialized successfully!")
            st.rerun()

if st.session_state.wallet is not None:
    # Display account balance and money management
    st.header("Account Management")
    current_balance = check_balance()
    st.session_state.account_balance = current_balance
    st.metric("Current Balance", f"€{current_balance:.2f}")
    
    # Check for pending requests
    pending_requests = get_pending_requests()
    if pending_requests:
        st.subheader("Pending Money Requests")
        for req in pending_requests:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"Request for €{float(req.amount_inquired.value):.2f} from {req.counterparty_alias.value}")
            with col2:
                if st.button(f"Accept €{float(req.amount_inquired.value):.2f}", key=f"accept_{req.id_}"):
                    if accept_request(req.id_):
                        st.success("Request accepted!")
                        time.sleep(2)
                        st.rerun()
    
    if current_balance < 10.0:  # If balance is too low for testing
        st.warning("Your account balance is low. Request some test money from Sugar Daddy!")
        if st.button("Request €500 from Sugar Daddy"):
            if request_money():
                time.sleep(2)  # Wait a bit for the request to process
                st.rerun()

    # Display crypto balances
    st.header("Wallet Balances")
    balances = st.session_state.wallet.get_balances()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("BTC Balance", f"{balances['BTC']:.6f} BTC")
    with col2:
        st.metric("ETH Balance", f"{balances['ETH']:.6f} ETH")
    with col3:
        st.metric("xEUR Balance", f"€{balances['xEUR']:.2f}")

    # Payment form
    st.header("Make a Payment")
    crypto_type = st.selectbox("Select Crypto", ["BTC", "ETH"])
    
    # Show current conversion rate
    st.write(f"Current rate: 1 {crypto_type} = €{CONVERSION_RATES[crypto_type]:,.2f}")
    
    # Input crypto amount
    crypto_amount = st.number_input(
        f"Amount in {crypto_type}",
        min_value=0.000001,
        max_value=balances[crypto_type],
        step=0.000001,
        format="%.6f"
    )
    
    # Calculate EUR value
    eur_value = crypto_amount * CONVERSION_RATES[crypto_type]
    st.write(f"This equals: €{eur_value:.2f}")
    
    if st.button("Convert and Pay"):
        # Convert crypto to xEUR
        if st.session_state.wallet.convert_crypto_to_xeur(crypto_type, eur_value):
            # Make payment through Bunq
            if make_payment(
                eur_value,
                st.session_state.test_account.alias[0].value,
                st.session_state.test_account.description
            ):
                # Record transaction
                st.session_state.wallet.add_transaction(
                    crypto_type=crypto_type,
                    crypto_amount=crypto_amount,
                    eur_amount=eur_value,
                    recipient=st.session_state.test_account.alias[0].value,
                    status="COMPLETED"
                )
                st.success(f"Successfully paid €{eur_value:.2f} using {crypto_amount:.6f} {crypto_type}")
                st.rerun()
        else:
            st.error("Insufficient crypto balance")

    # Transaction history
    st.header("Transaction History")
    transactions = st.session_state.wallet.get_transaction_history()
    if transactions:
        df = pd.DataFrame(transactions)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        st.dataframe(df)
        
        # Plot spending trends
        st.subheader("Spending Trends")
        df['date'] = df['timestamp'].dt.date
        daily_spending = df.groupby('date')['eur_amount'].sum().reset_index()
        fig = px.line(daily_spending, x='date', y='eur_amount', 
                     title='Daily Spending in EUR')
        st.plotly_chart(fig)
    else:
        st.info("No transactions yet")

    # Reset button
    if st.button("Reset Balances"):
        st.session_state.wallet.reset_balances()
        st.success("Balances reset to default values")
        st.rerun() 