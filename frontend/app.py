import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sys
import os
import time
import json

# Add backend to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from wallet import CryptoWallet
from bunq_api import BunqAPI
from fetch_conversion_rate import fetch_rate

# Initialize session state
if 'wallet' not in st.session_state:
    st.session_state.wallet = None
if 'bunq_api' not in st.session_state:
    st.session_state.bunq_api = None
if 'test_account' not in st.session_state:
    st.session_state.test_account = None
if 'account_balance' not in st.session_state:
    st.session_state.account_balance = 0.0
if 'last_transaction' not in st.session_state:
    st.session_state.last_transaction = None
if 'balance_updates' not in st.session_state:
    st.session_state.balance_updates = []
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'conversion_rates' not in st.session_state:
    st.session_state.conversion_rates = {}

def get_conversion_rate(crypto_type: str) -> float:
    """Get the current conversion rate for a cryptocurrency"""
    try:
        if crypto_type not in st.session_state.conversion_rates:
            st.session_state.conversion_rates[crypto_type] = fetch_rate(crypto_type, "EUR")
        return st.session_state.conversion_rates[crypto_type]
    except Exception as e:
        st.error(f"Error fetching conversion rate: {e}")
        # Fallback to mock rates if API fails
        return {
            'BTC': 40000,
            'ETH': 2000
        }[crypto_type]

def get_fiat_value(crypto_type: str, amount: float) -> float:
    """Calculate fiat value of crypto"""
    rate = get_conversion_rate(crypto_type)
    return amount * rate

def format_balance(amount: float, crypto_type: str) -> str:
    """Format balance with fiat value"""
    fiat_value = get_fiat_value(crypto_type, amount)
    return f"{amount:.6f} {crypto_type} (≈€{fiat_value:,.2f})"

def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"€{amount:,.2f}"

def add_balance_update(crypto_type: str, amount: float, is_positive: bool):
    """Add a balance update to show in the UI"""
    st.session_state.balance_updates.append({
        'type': crypto_type,
        'amount': amount,
        'is_positive': is_positive,
        'timestamp': time.time()
    })

# Streamlit UI
st.set_page_config(layout="wide", page_title="Crypto Payment Simulator")

# Dark mode toggle
col1, col2 = st.columns([1, 0.1])
with col1:
    st.title("Crypto Payment Simulator")
with col2:
    dark_mode = st.toggle("🌙", key="dark_mode")
    if dark_mode:
        st.markdown("""
        <style>
        .stApp {
            background-color: #1E1E1E;
            color: #FFFFFF;
        }
        </style>
        """, unsafe_allow_html=True)

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
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "💸 Make Payment", "✅ Transaction History"])

    with tab1:
        st.header("Wallet Overview")
        
        # Display balances in a grid with animations
        col1, col2, col3 = st.columns(3)
        balances = st.session_state.wallet.get_balances()
        
        with col1:
            st.metric(
                "BTC Balance",
                format_balance(balances['BTC'], 'BTC'),
                help="Bitcoin balance with approximate EUR value"
            )
            # BTC Recent Changes
            with st.expander("Recent BTC Changes", expanded=False):
                btc_changes = [update for update in st.session_state.balance_updates if update['type'] == 'BTC']
                if btc_changes:
                    for change in btc_changes[-5:]:  # Show last 5 changes
                        st.write(f"{'+' if change['is_positive'] else '-'}{change['amount']:.6f} BTC")
                else:
                    st.write("No recent changes")
        
        with col2:
            st.metric(
                "ETH Balance",
                format_balance(balances['ETH'], 'ETH'),
                help="Ethereum balance with approximate EUR value"
            )
            # ETH Recent Changes
            with st.expander("Recent ETH Changes", expanded=False):
                eth_changes = [update for update in st.session_state.balance_updates if update['type'] == 'ETH']
                if eth_changes:
                    for change in eth_changes[-5:]:  # Show last 5 changes
                        st.write(f"{'+' if change['is_positive'] else '-'}{change['amount']:.6f} ETH")
                else:
                    st.write("No recent changes")
        
        with col3:
            st.metric(
                "xEUR Balance",
                f"€{balances['xEUR']:.2f}",
                help="Stablecoin balance for payments"
            )
            # xEUR Recent Changes
            with st.expander("Recent xEUR Changes", expanded=False):
                xeur_changes = [update for update in st.session_state.balance_updates if update['type'] == 'xEUR']
                if xeur_changes:
                    for change in xeur_changes[-5:]:  # Show last 5 changes
                        st.write(f"{'+' if change['is_positive'] else '-'}{format_currency(change['amount'])}")
                else:
                    st.write("No recent changes")

    with tab2:
        st.header("Make a Payment")
        
        # Payment form
        col1, col2 = st.columns([1, 2])
        
        with col1:
            crypto_type = st.selectbox(
                "Select Crypto",
                ["BTC", "ETH"],
                help="Choose which cryptocurrency to spend"
            )
            
            # Show current balance and max spendable
            current_balance = balances[crypto_type]
            max_eur = get_fiat_value(crypto_type, current_balance)
            st.write(f"Available: {format_balance(current_balance, crypto_type)}")
            st.write(f"Max spendable: €{max_eur:,.2f}")
        
        with col2:
            # Input EUR amount with auto-conversion to crypto
            eur_amount = st.number_input(
                "Amount in EUR",
                min_value=0.01,
                max_value=get_fiat_value(crypto_type, current_balance),
                step=0.01,
                format="%.2f",
                value=1.00,  # Set default value to 1
                help="Enter the amount in EUR to spend"
            )
            
            # Show conversion rate and BTC value
            rate = get_conversion_rate(crypto_type)
            crypto_amount = eur_amount / rate
            st.markdown(f"""
            ### Current Rate
            **1 {crypto_type} = €{rate:,.2f}**
            """)
            st.write(f"Total: {crypto_amount:.6f} {crypto_type}")
        
        # Payment details
        st.subheader("Payment Details")
        merchant_iban = st.text_input(
            "Merchant IBAN",
            value=st.session_state.test_account.alias[0].value,
            help="Enter the merchant's IBAN"
        )
        merchant_name = st.text_input(
            "Merchant Name",
            value="Test Merchant",
            help="Enter the merchant's name"
        )
        
        # Visual preview card
        st.subheader("Payment Preview")
        st.info(f"""
        You are about to spend {crypto_amount:.6f} {crypto_type} (€{eur_amount:.2f}) to send {format_currency(eur_amount)} to {merchant_name} (IBAN: {merchant_iban})
        """)
        
        # Convert and Pay button
        if st.button("Convert and Pay", type="primary"):
            with st.spinner("Processing payment..."):
                # Disable form
                st.session_state.form_disabled = True
                
                # Step 1: Show crypto balance before conversion
                st.write("### Payment Process:")
                st.write("1. Current balances before conversion:")
                balances_before = st.session_state.wallet.get_balances()
                st.write(f"- {crypto_type}: {balances_before[crypto_type]:.6f}")
                st.write(f"- xEUR: {format_currency(balances_before['xEUR'])}")
                
                # Step 2: Convert crypto to xEUR
                st.write("2. Converting crypto to xEUR...")
                if st.session_state.wallet.convert_crypto_to_xeur(crypto_type, eur_amount):
                    add_balance_update(crypto_type, -crypto_amount, False)
                    add_balance_update('xEUR', eur_amount, True)
                    
                    # Show intermediate balances
                    st.write("3. Balances after conversion:")
                    balances_after_conversion = st.session_state.wallet.get_balances()
                    st.write(f"- {crypto_type}: {balances_after_conversion[crypto_type]:.6f}")
                    st.write(f"- xEUR: {format_currency(balances_after_conversion['xEUR'])}")
                    
                    # Step 3: Withdraw xEUR for payment
                    st.write("4. Withdrawing xEUR for payment...")
                    if st.session_state.wallet.withdraw_xeur(eur_amount, merchant_iban):
                        add_balance_update('xEUR', -eur_amount, False)
                        
                        # Show balances after withdrawal
                        st.write("5. Balances after xEUR withdrawal:")
                        balances_after_withdrawal = st.session_state.wallet.get_balances()
                        st.write(f"- xEUR: {format_currency(balances_after_withdrawal['xEUR'])}")
                        
                        # Step 4: Make payment
                        st.write("6. Sending payment to merchant...")
                        if st.session_state.bunq_api.make_payment(
                            eur_amount,
                            merchant_iban,
                            merchant_name
                        ):
                            # Store last transaction for confirmation view
                            st.session_state.last_transaction = {
                                'crypto_type': crypto_type,
                                'crypto_amount': crypto_amount,
                                'eur_value': eur_amount,
                                'merchant_name': merchant_name,
                                'merchant_iban': merchant_iban
                            }
                            
                            st.success(f"""
                            ✅ Payment Successful!
                            
                            You paid {format_currency(eur_amount)} using {crypto_amount:.6f} {crypto_type}
                            
                            Recipient: {merchant_name} ({merchant_iban})
                            """)
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Payment to merchant failed")
                    else:
                        st.error("Failed to withdraw xEUR")
                else:
                    st.error("Insufficient crypto balance")

    with tab3:
        st.header("Transaction History")
        
        # Show last transaction if available
        if st.session_state.last_transaction:
            tx = st.session_state.last_transaction
            st.success(f"""
            ### Last Transaction
            - Spent: {tx['crypto_amount']:.6f} {tx['crypto_type']}
            - Value: {format_currency(tx['eur_value'])}
            - To: {tx['merchant_name']} ({tx['merchant_iban']})
            """)
        
        # Transaction history
        transactions = st.session_state.wallet.get_transaction_history()
        if transactions:
            df = pd.DataFrame(transactions)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Group transactions by timestamp
            grouped_transactions = {}
            for _, tx in df.sort_values('timestamp', ascending=False).iterrows():
                timestamp = tx['timestamp'].strftime('%Y-%m-%d %H:%M')
                if timestamp not in grouped_transactions:
                    grouped_transactions[timestamp] = []
                grouped_transactions[timestamp].append(tx)
            
            # Display grouped transactions
            st.subheader("Recent Transactions")
            for timestamp, tx_group in grouped_transactions.items():
                # Find the main transaction (usually the payment)
                main_tx = next((tx for tx in tx_group if tx['status'] == "MERCHANT_PAYMENT"), tx_group[0])
                conversion_tx = next((tx for tx in tx_group if tx['status'] == "CRYPTO_TO_xEUR"), None)
                
                # Create expander with improved summary
                with st.expander(f"🟢 Paid {format_currency(main_tx['eur_amount'])} to {main_tx.get('recipient', 'Test Merchant')} using {conversion_tx['crypto_amount']:.6f} {conversion_tx['crypto_type']} — {timestamp}"):
                    # Transaction flow in a card
                    with st.container():
                        st.markdown("### 🔁 Flow")
                        flow_text = f"""
                        <div style='text-align: center; font-size: 1.2em; padding: 10px; background-color: #f0f2f6; border-radius: 5px;'>
                            🪙 {conversion_tx['crypto_amount']:.6f} {conversion_tx['crypto_type']} ➝ 💶 {format_currency(conversion_tx['eur_amount'])} xEUR ➝ 🏦 {format_currency(conversion_tx['eur_amount'])} via Bunq ➝ {main_tx.get('recipient', 'Test Merchant')}
                        </div>
                        """
                        st.markdown(flow_text, unsafe_allow_html=True)
                    
                    # Steps in a timeline format
                    with st.container():
                        st.markdown("### 📋 Steps")
                        steps = []
                        for tx in sorted(tx_group, key=lambda x: x['timestamp']):
                            if tx['status'] == "CRYPTO_TO_xEUR":
                                steps.append(f"1. ↪️ Converted {tx['crypto_amount']:.6f} {tx['crypto_type']} → {format_currency(tx['eur_amount'])} xEUR")
                            elif tx['status'] == "xEUR_WITHDRAWAL":
                                steps.append(f"2. 📤 Withdrew {format_currency(tx['eur_amount'])} xEUR")
                            elif tx['status'] == "MERCHANT_PAYMENT":
                                steps.append(f"3. 🏦 Debited {format_currency(tx['eur_amount'])} from Bunq account and sent to {tx.get('recipient', 'Test Merchant')}")
                        
                        for step in steps:
                            st.markdown(step)
                    
                    # Status section in a card
                    with st.container():
                        st.markdown("### ✅ Status")
                        status_text = f"""
                        <div style='padding: 10px; background-color: #f0f2f6; border-radius: 5px;'>
                            <p style='margin: 0;'><strong>Status:</strong> ✅ Completed</p>
                            <p style='margin: 0;'><strong>Method:</strong> 🔧 Internal conversion + Bunq API</p>
                        </div>
                        """
                        st.markdown(status_text, unsafe_allow_html=True)
                        
                        # Add Bunq Transfer section
                        st.markdown("### 🏦 Bunq Transfer")
                        bunq_tx = next((tx for tx in tx_group if tx['status'] == "MERCHANT_PAYMENT"), None)
                        if bunq_tx is not None:
                            bunq_text = f"""
                            <div style='padding: 10px; background-color: #f0f2f6; border-radius: 5px;'>
                                <p style='margin: 0;'><strong>Debited:</strong> {format_currency(bunq_tx['eur_amount'])} from platform Bunq account</p>
                                <p style='margin: 0;'><strong>Sent to:</strong> IBAN: {bunq_tx.get('recipient', 'Test Merchant')}</p>
                                <p style='margin: 0;'><strong>Reference:</strong> "Crypto payment via xEUR"</p>
                            </div>
                            """
                            st.markdown(bunq_text, unsafe_allow_html=True)
            
            # Remove the full transaction table and spending trends
            # ... existing code ...
        else:
            st.info("No transactions yet")

        # Reset button
        if st.button("Reset Balances"):
            st.session_state.wallet.reset_balances()
            st.success("Balances reset to default values")
            st.rerun() 