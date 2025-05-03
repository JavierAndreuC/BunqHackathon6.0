import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sys
import os

# Add backend to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from wallet import CryptoWallet
from bunq_api import BunqAPI

# Initialize session state
if 'wallet' not in st.session_state:
    st.session_state.wallet = None
if 'bunq_api' not in st.session_state:
    st.session_state.bunq_api = None
if 'test_account' not in st.session_state:
    st.session_state.test_account = None
if 'account_balance' not in st.session_state:
    st.session_state.account_balance = 0.0

# Mock conversion rates (in a real app, these would come from an exchange)
CONVERSION_RATES = {
    'BTC': 40000,  # 1 BTC = 40,000 EUR
    'ETH': 2000    # 1 ETH = 2,000 EUR
}

# Streamlit UI
st.title("Crypto Payment Simulator")
st.write("Convert and pay with crypto through Bunq")

# Setup section
if st.session_state.wallet is None:
    if st.button("Initialize System"):
        # Initialize Bunq API
        bunq_api = BunqAPI()
        if bunq_api.setup():
            st.session_state.bunq_api = bunq_api
            st.session_state.test_account = bunq_api.test_account
            
            # Create wallet
            st.session_state.wallet = CryptoWallet(str(bunq_api.test_account.id_))
            st.success("System initialized successfully!")
            st.rerun()

if st.session_state.wallet is not None:
    # Display account balance and money management
    st.header("Account Management")
    current_balance = st.session_state.bunq_api.get_balance()
    st.session_state.account_balance = current_balance
    st.metric("Current Balance", f"€{current_balance:.2f}")
    
    # Check for pending requests
    pending_requests = st.session_state.bunq_api.get_pending_requests()
    if pending_requests:
        st.subheader("Pending Money Requests")
        for req in pending_requests:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"Request for €{float(req.amount_inquired.value):.2f} from {req.counterparty_alias.value}")
            with col2:
                if st.button(f"Accept €{float(req.amount_inquired.value):.2f}", key=f"accept_{req.id_}"):
                    if st.session_state.bunq_api.accept_request(req.id_):
                        st.success("Request accepted!")
                        time.sleep(2)
                        st.rerun()
    
    if current_balance < 10.0:  # If balance is too low for testing
        st.warning("Your account balance is low. Request some test money from Sugar Daddy!")
        if st.button("Request €500 from Sugar Daddy"):
            if st.session_state.bunq_api.request_money():
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
    st.write("""
    ### Payment Flow:
    1. Select crypto and amount to spend
    2. System automatically converts crypto to xEUR
    3. xEUR is used to make the payment
    4. Payment is sent to merchant's IBAN
    """)
    
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
    
    # Payment details
    st.subheader("Payment Details")
    merchant_iban = st.text_input("Merchant IBAN", value=st.session_state.test_account.alias[0].value)
    merchant_name = st.text_input("Merchant Name", value="Test Merchant")
    
    if st.button("Convert and Pay"):
        # Show payment flow steps
        st.write("### Payment Process:")
        
        # Step 1: Show crypto balance before conversion
        st.write("1. Current balances before conversion:")
        balances_before = st.session_state.wallet.get_balances()
        st.write(f"- {crypto_type}: {balances_before[crypto_type]:.6f}")
        st.write(f"- xEUR: €{balances_before['xEUR']:.2f}")
        
        # Step 2: Convert crypto to xEUR
        st.write("2. Converting crypto to xEUR...")
        if st.session_state.wallet.convert_crypto_to_xeur(crypto_type, eur_value):
            # Record the crypto to xEUR conversion
            st.session_state.wallet.add_transaction(
                crypto_type=crypto_type,
                crypto_amount=crypto_amount,
                eur_amount=eur_value,
                recipient="Bunq Internal",
                status="CRYPTO_TO_xEUR"
            )
            
            # Show intermediate balances
            st.write("3. Balances after conversion:")
            balances_after = st.session_state.wallet.get_balances()
            st.write(f"- {crypto_type}: {balances_after[crypto_type]:.6f}")
            st.write(f"- xEUR: €{balances_after['xEUR']:.2f}")
            
            # Step 3: Make payment
            st.write("4. Sending payment to merchant...")
            if st.session_state.bunq_api.make_payment(
                eur_value,
                merchant_iban,
                merchant_name
            ):
                # Record the final merchant payment
                st.session_state.wallet.add_transaction(
                    crypto_type="xEUR",
                    crypto_amount=eur_value,
                    eur_amount=eur_value,
                    recipient=merchant_iban,
                    status="MERCHANT_PAYMENT"
                )
                
                st.success(f"""
                ### Payment Successful!
                Transaction Flow:
                1. Spent: {crypto_amount:.6f} {crypto_type}
                2. Converted to: €{eur_value:.2f} xEUR
                3. xEUR debited by Bunq
                4. Sent to: {merchant_name} ({merchant_iban})
                """)
                st.rerun()
        else:
            st.error("Insufficient crypto balance")

    # Transaction history with improved visualization
    st.header("Transaction History")
    transactions = st.session_state.wallet.get_transaction_history()
    if transactions:
        df = pd.DataFrame(transactions)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Format the transaction display
        st.subheader("Recent Transactions")
        for _, tx in df.sort_values('timestamp', ascending=False).head(5).iterrows():
            with st.expander(f"Transaction on {tx['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"):
                if tx['status'] == "CRYPTO_TO_xEUR":
                    st.write("**Conversion Process:**")
                    st.write(f"- Converted {tx['crypto_amount']:.6f} {tx['crypto_type']} to €{tx['eur_amount']:.2f} xEUR")
                    st.write("- Processed by Bunq internal conversion")
                elif tx['status'] == "xEUR_DEBIT":
                    st.write("**xEUR Processing:**")
                    st.write(f"- Bunq debited €{tx['eur_amount']:.2f} xEUR")
                    st.write("- Preparing for merchant payment")
                elif tx['status'] == "MERCHANT_PAYMENT":
                    st.write("**Merchant Payment:**")
                    st.write(f"- Sent €{tx['eur_amount']:.2f} to {tx['recipient']}")
                    st.write("- Payment completed")
                else:
                    st.write("**Transaction Details:**")
                    st.write(f"- Type: {tx['crypto_type']}")
                    st.write(f"- Amount: {tx['crypto_amount']:.6f}")
                    st.write(f"- EUR Value: €{tx['eur_amount']:.2f}")
                    st.write(f"- Recipient: {tx['recipient']}")
                    st.write(f"- Status: {tx['status']}")
        
        # Full transaction table
        st.subheader("All Transactions")
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