import streamlit as st
import stripe
import yfinance as yf
from openai import OpenAI

# Initialize Streamlit Page Config
st.set_page_config(page_title="AI Stock Pro - Global", layout="wide")

# Configure Stripe API Keys (Set these in Streamlit Cloud Secrets)
stripe.api_key = st.secrets.get("STRIPE_SECRET_KEY", "sk_test_YOUR_SECRET_KEY")
PRICE_ID = st.secrets.get("STRIPE_PRICE_ID", "price_YOUR_STRIPE_PRICE_ID")

# Initialize Subscription State
if "subscribed" not in st.session_state:
    st.session_state.subscribed = False

# Check if user was redirected back from Stripe Checkout successfully
query_params = st.query_params
if "session_id" in query_params and not st.session_state.subscribed:
    session_id = query_params["session_id"]
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == "paid" or session.status == "complete":
            st.session_state.subscribed = True
            st.success("🎉 Payment successful! Welcome to AI Stock Pro.")
    except Exception as e:
        st.error(f"Error verifying payment: {e}")

st.title("📈 AI-Powered Blue-Chip Stock Analyzer (Global Pro)")

# --- GLOBAL SUBSCRIPTION PAYWALL GATE ($10 / month) ---
if not st.session_state.subscribed:
    st.warning("🔒 **Locked Feature:** Subscribe for **$10 / month** to unlock instant AI fundamental reports worldwide.")

    if st.button("Subscribe with Card (Global)"):
        try:
            # Replace with your live app URL when deployed
            current_url = "https://your-app-name.streamlit.app" 
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price": PRICE_ID,
                    "quantity": 1,
                }],
                mode="subscription",
                success_url=f"{current_url}/?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{current_url}/",
            )
            
            # Redirect user safely to Stripe's global hosted checkout page
            st.markdown(f'<meta http-equiv="refresh" content="0;url={checkout_session.url}">', unsafe_allow_html=True)
            st.markdown(f"If you are not redirected, [click here to pay]({checkout_session.url})")
            
        except Exception as e:
            st.error(f"Failed to create Stripe Checkout session: {e}")

else:
    # --- UNLOCKED APP CONTENT FOR SUBSCRIBERS ---
    st.success("✨ Pro Subscription Active")

    # Sidebar for OpenAI API Key
    st.sidebar.header("Configuration")
    api_key = st.sidebar.text_input("Enter OpenAI API Key", type="password")

    ticker_symbol = st.text_input("Stock Ticker Symbol (e.g., AAPL, MSFT, RELIANCE.NS)", value="AAPL")

    if st.button("Analyze Fundamentals"):
        if not api_key:
            st.error("Please enter your OpenAI API key in the sidebar.")
        else:
            with st.spinner(f"Fetching data and running AI analysis for {ticker_symbol.upper()}..."):
                try:
                    stock = yf.Ticker(ticker_symbol)
                    info = stock.info
                    
                    name = info.get("shortName", ticker_symbol)
                    sector = info.get("sector", "N/A")
                    market_cap = info.get("marketCap", "N/A")
                    pe_ratio = info.get("trailingPE", "N/A")
                    dividend_yield = info.get("dividendYield", "N/A")
                    profit_margins = info.get("profitMargins", "N/A")
                    debt_to_equity = info.get("debtToEquity", "N/A")
                    description = info.get("longBusinessSummary", "No summary available.")

                    market_cap_str = f"${market_cap / 1e9:.2f} Billion" if isinstance(market_cap, (int, float)) else "N/A"
                    dividend_yield_str = f"{dividend_yield * 100:.2f}%" if isinstance(dividend_yield, (int, float)) else "N/A"

                    st.subheader(f"Company Overview: {name} ({sector})")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Market Cap", market_cap_str)
                    col2.metric("Trailing P/E", str(pe_ratio))
                    col3.metric("Dividend Yield", dividend_yield_str)
                    col4.metric("Debt-to-Equity", str(debt_to_equity))

                    with st.expander("Read Business Summary"):
                        st.write(description)

                    prompt = f"""
                    You are an expert equity research analyst. Analyze the following fundamental metrics for blue-chip stock {name} ({ticker_symbol}):
                    - Sector: {sector}
                    - Market Cap: {market_cap_str}
                    - P/E Ratio: {pe_ratio}
                    - Dividend Yield: {dividend_yield_str}
                    - Profit Margins: {profit_margins}
                    - Debt-to-Equity: {debt_to_equity}

                    Provide a structured fundamental report covering:
                    1. **Financial Health & Stability**
                    2. **Valuation Assessment**
                    3. **Income & Dividends**
                    4. **Overall Investment Verdict**
                    """

                    client = OpenAI(api_key=api_key)
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a professional stock analyst."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3
                    )

                    st.markdown("---")
                    st.subheader("🤖 AI Fundamental Research Report")
                    st.markdown(response.choices[0].message.content)

                except Exception as e:
                    st.error(f"An error occurred: {e}")
