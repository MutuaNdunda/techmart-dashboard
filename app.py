# dashboard_app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIG ---
st.set_page_config(
    page_title="TechMart Analytics Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD DATA ---
@st.cache_data(ttl=600)
def load_data():
    """Load TechMart transactions data from Google Drive."""
    file_id = '16yRoXnEY8AP50tmyCPSdTMOzXD8ipxdb'
    url = f'https://drive.google.com/uc?id={file_id}&export=download'

    try:
        df = pd.read_csv(url)

        # Normalize column names
        df.columns = df.columns.str.strip().str.lower()

        # Clean timestamp column
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
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

    except Exception as e:
        st.error(f"❌ Error loading CSV: {e}")
        return pd.DataFrame()

# --- LOAD DATA ---
with st.spinner("Loading transaction data..."):
    df = load_data()

if df.empty:
    st.warning("No data available. Please verify your data source.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.title("Navigation")
st.sidebar.markdown("Use filters below to explore sales data.")
st.sidebar.markdown("#Filters")

# --- FILTERS ---
counties = sorted(df['county'].dropna().unique())
selected_county = st.sidebar.multiselect("County", counties)

# Store filter depends on selected counties
if selected_county:
    store_names = sorted(df[df['county'].isin(selected_county)]['storename'].dropna().unique())
else:
    store_names = sorted(df['storename'].dropna().unique())
selected_store = st.sidebar.multiselect("Store Name", store_names)

# Other filters
categories = sorted(df['category'].dropna().unique())
products = sorted(df['product'].dropna().unique())
payments = sorted(df['paymentmethod'].dropna().unique())
genders = sorted(df['gender'].dropna().unique())

selected_category = st.sidebar.multiselect("Category", categories)
selected_product = st.sidebar.multiselect("Product", products)
selected_payment = st.sidebar.multiselect("Payment Method", payments)
selected_gender = st.sidebar.multiselect("Gender", genders)
selected_age_group = st.sidebar.multiselect("Age Group", ["Minor", "Youth", "Adult"])

# --- DATE FILTER ---
st.sidebar.markdown("### Date Range Filter")
date_selection = st.sidebar.date_input(
    "Select Date Range",
    value=[],
    help="Select start and end dates to filter transactions",
)

# --- APPLY FILTERS ---
filtered_df = df.copy()

if selected_county:
    filtered_df = filtered_df[filtered_df['county'].isin(selected_county)]
if selected_store:
    filtered_df = filtered_df[filtered_df['storename'].isin(selected_store)]
if selected_category:
    filtered_df = filtered_df[filtered_df['category'].isin(selected_category)]
if selected_product:
    filtered_df = filtered_df[filtered_df['product'].isin(selected_product)]
if selected_payment:
    filtered_df = filtered_df[filtered_df['paymentmethod'].isin(selected_payment)]
if selected_gender:
    filtered_df = filtered_df[filtered_df['gender'].isin(selected_gender)]
if selected_age_group:
    filtered_df = filtered_df[filtered_df['age_group'].isin(selected_age_group)]

# Apply date filter safely
if isinstance(date_selection, (list, tuple)) and len(date_selection) == 2:
    start_date, end_date = date_selection
    filtered_df = filtered_df[
        (filtered_df["timestamp"].dt.date >= start_date)
        & (filtered_df["timestamp"].dt.date <= end_date)
    ]
elif isinstance(date_selection, (list, tuple)) and len(date_selection) == 1:
    start_date = date_selection[0]
    filtered_df = filtered_df[filtered_df["timestamp"].dt.date == start_date]
else:
    st.sidebar.caption("Select one or two dates to apply filtering.")

# --- MAIN PANEL ---
st.title("TechMart Sales Analytics Dashboard")
st.markdown(f"**Data Last Loaded:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- KPIs ---
total_txns = len(filtered_df)
total_revenue = filtered_df['revenue'].sum()
avg_sale = filtered_df['revenue'].mean()
total_discount = filtered_df['discount'].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Transactions", f"{total_txns:,}")
col2.metric("Total Revenue", f"KES {total_revenue:,.0f}")
col3.metric("Total Discount", f"KES {total_discount:,.0f}")
col4.metric("Avg Sale Value", f"KES {avg_sale:,.0f}")

st.divider()

# --- TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Location Comparison",
    "🔍 Drill-Down Analysis",
    "📈 Roll-Up Summary",
    "🔄 Pivot View",
    "👥 Team Members"
])

# --- TAB 1: Location Comparison ---
with tab1:
    st.subheader("Sales by Category — Location vs Overall")
    if 'county' in filtered_df.columns:
        county_sales = (
            filtered_df.groupby('county')['revenue']
            .sum()
            .reset_index()
            .sort_values('revenue', ascending=False)
        )
        fig_county = px.bar(
            county_sales,
            x='county',
            y='revenue',
            title="Revenue by County",
            labels={"revenue": "Revenue (KES)"}
        )
        st.plotly_chart(fig_county, use_container_width=True)
    else:
        st.info("No county data available in this dataset.")

# --- TAB 2: Drill-Down ---
with tab2:
    st.subheader("Drill-Down: Monthly → Daily → Hourly Sales")
    view_option = st.radio("Select Drill Level", ["Monthly", "Daily", "Hourly"], horizontal=True)
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
    roll_option = st.radio("Select Roll-Up Period", ["Monthly", "Quarterly"], horizontal=True)
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

# --- TAB 5: Team Members ---
with tab5:
    st.subheader("Project Team Members")

    team_data = {
        "Registration Number": [
            "ST62/80168/2024",
            "ST62/80313/2024",
            "ST62/80195/2024",
            "ST62/80774/2024",
            "ST62/80472/2024"
        ],
        "Name": [
            "Gabriel Ndunda",
            "Donsy Ombura",
            "Leonard Kiti",
            "Josephat Motonu",
            "Tabitha Kiarie"
        ]
    }

    df_team = pd.DataFrame(team_data)

    st.table(df_team)


st.sidebar.markdown("---")
st.sidebar.caption("© 2025 TechMart Analytics | Built with Streamlit 🚀")
