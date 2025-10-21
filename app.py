# dashboard_app.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
from datetime import datetime

# --- CONFIG ---
DB_URL = "postgresql://postgres:%23Kenya%402025@db.jojtpfepksshdzpxjlvf.supabase.co:5432/postgres?sslmode=require"

st.set_page_config(
    page_title="TechMart Analytics Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD DATA ---
@st.cache_data(ttl=600)
def load_data():
    engine = create_engine(DB_URL)
    query = "SELECT * FROM transactions;"
    df = pd.read_sql(query, engine)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['month'] = df['timestamp'].dt.to_period('M').astype(str)
    df['day'] = df['timestamp'].dt.date
    df['hour'] = df['timestamp'].dt.hour
    df['quarter'] = df['timestamp'].dt.to_period('Q').astype(str)

    # Define age groups
    def age_group(age):
        try:
            age = int(age)
            if age < 18:
                return "Minor"
            elif age < 35:
                return "Youth"
            else:
                return "Adult"
        except:
            return "Unknown"

    df["age_group"] = df["age"].apply(age_group)
    return df

# --- SIDEBAR ---
st.sidebar.title("🧭 Navigation")
st.sidebar.markdown("Use filters below to explore sales data.")

with st.sidebar:
    st.divider()
    st.markdown("### 🔍 Filters")
    refresh = st.button("🔄 Refresh Data")

# Load data
with st.spinner("Loading transaction data..."):
    df = load_data()

if refresh:
    st.cache_data.clear()
    st.rerun()

# --- SIDEBAR FILTERS ---
# County filter
counties = sorted(df['county'].dropna().unique())
selected_county = st.sidebar.multiselect("📍 County", counties)

# Store filter depends on selected counties
if selected_county:
    store_names = sorted(df[df['county'].isin(selected_county)]['store_name'].dropna().unique())
else:
    store_names = sorted(df['store_name'].dropna().unique())
selected_store = st.sidebar.multiselect("🏪 Store Name", store_names)

# Other filters
categories = sorted(df['category'].dropna().unique())
products = sorted(df['product'].dropna().unique())
payments = sorted(df['payment_method'].dropna().unique())
genders = sorted(df['gender'].dropna().unique())

selected_category = st.sidebar.multiselect("🛍️ Category", categories)
selected_product = st.sidebar.multiselect("📦 Product", products)
selected_payment = st.sidebar.multiselect("💳 Payment Method", payments)
selected_gender = st.sidebar.multiselect("🚻 Gender", genders)
selected_age_group = st.sidebar.multiselect("👶🧑‍💼👨‍🦳 Age Group", ["Minor", "Youth", "Adult"])

view_option = st.sidebar.radio("📅 Drill-Down Level", ["Monthly", "Daily", "Hourly"])
roll_option = st.sidebar.radio("📊 Roll-Up Period", ["Monthly", "Quarterly"])

st.sidebar.markdown("---")
st.sidebar.caption("💡 Data auto-refreshes every 10 minutes or manually via the refresh button.")

# --- APPLY FILTERS ---
filtered_df = df.copy()
if selected_county:
    filtered_df = filtered_df[filtered_df['county'].isin(selected_county)]
if selected_store:
    filtered_df = filtered_df[filtered_df['store_name'].isin(selected_store)]
if selected_category:
    filtered_df = filtered_df[filtered_df['category'].isin(selected_category)]
if selected_product:
    filtered_df = filtered_df[filtered_df['product'].isin(selected_product)]
if selected_payment:
    filtered_df = filtered_df[filtered_df['payment_method'].isin(selected_payment)]
if selected_gender:
    filtered_df = filtered_df[filtered_df['gender'].isin(selected_gender)]
if selected_age_group:
    filtered_df = filtered_df[filtered_df['age_group'].isin(selected_age_group)]

# --- MAIN PANEL ---
st.title("🛒 TechMart Sales Analytics Dashboard")
st.markdown(f"**Data Last Loaded:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- KPIs ---
total_txns = len(filtered_df)
total_revenue = filtered_df['revenue'].sum()
avg_sale = filtered_df['revenue'].mean()
total_discount = filtered_df['discount'].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("🧾 Transactions", f"{total_txns:,}")
col2.metric("💰 Total Revenue", f"KES {total_revenue:,.0f}")
col3.metric("🎟️ Total Discount", f"KES {total_discount:,.0f}")
col4.metric("📊 Avg Sale Value", f"KES {avg_sale:,.0f}")

st.divider()

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Location Comparison",
    "🔍 Drill-Down Analysis",
    "📈 Roll-Up Summary",
    "🔄 Pivot View"
])

# --- TAB 1: Location Comparison ---
with tab1:
    st.subheader("Sales by Category — Location vs Overall")

    if 'county' in filtered_df.columns:
        county_sales = (
            filtered_df.groupby('county')['revenue'].sum().reset_index().sort_values('revenue', ascending=False)
        )
        fig_county = px.bar(
            county_sales, x='county', y='revenue',
            title="Revenue by County", labels={"revenue": "Revenue (KES)"}
        )
        st.plotly_chart(fig_county, use_container_width=True)
    else:
        st.info("No county data available in this dataset.")

# --- TAB 2: Drill-Down ---
with tab2:
    st.subheader("Drill-Down: Monthly → Daily → Hourly Sales")

    if view_option == "Monthly":
        drill_df = filtered_df.groupby('month')['revenue'].sum().reset_index()
        fig = px.line(drill_df, x='month', y='revenue', title='Monthly Sales Trend')
    elif view_option == "Daily":
        drill_df = filtered_df.groupby('day')['revenue'].sum().reset_index()
        fig = px.line(drill_df, x='day', y='revenue', title='Daily Sales Trend')
    else:
        drill_df = filtered_df.groupby('hour')['revenue'].sum().reset_index()
        fig = px.bar(drill_df, x='hour', y='revenue', title='Hourly Sales Trend')

    st.plotly_chart(fig, use_container_width=True)

# --- TAB 3: Roll-Up ---
with tab3:
    st.subheader("Roll-Up: Monthly and Quarterly Totals")

    if roll_option == "Monthly":
        roll_df = filtered_df.groupby('month')['revenue'].sum().reset_index()
        fig_roll = px.bar(roll_df, x='month', y='revenue', title='Monthly Total Sales')
    else:
        roll_df = filtered_df.groupby('quarter')['revenue'].sum().reset_index()
        fig_roll = px.bar(roll_df, x='quarter', y='revenue', title='Quarterly Total Sales')

    st.plotly_chart(fig_roll, use_container_width=True)

# --- TAB 4: Pivot ---
with tab4:
    st.subheader("Pivot View: Product Category vs Month")
    pivot_df = filtered_df.pivot_table(
        index='category',
        columns='month',
        values='revenue',
        aggfunc='sum',
        fill_value=0
    )

    st.dataframe(pivot_df.style.format("{:,.0f}"))

    fig_pivot = px.imshow(
        pivot_df,
        text_auto=True,
        aspect="auto",
        title="Revenue Heatmap: Category vs Month",
        color_continuous_scale="YlGnBu"
    )
    st.plotly_chart(fig_pivot, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.caption("© 2025 TechMart Analytics | Built with Streamlit 🚀")
