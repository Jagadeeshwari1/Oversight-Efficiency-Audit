import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Set Page Config
st.set_page_config(page_title="Forensic Oversight Audit", layout="wide")

# --- DATA ENGINE ---
@st.cache_data
def load_and_improve_data():
    # 1. Load the CSV file (much more stable than XLSX on GitHub)
    try:
        # We use 'audit_data.csv' - ensure this matches your GitHub filename exactly
        df = pd.read_csv('audit_data.csv')
    except Exception as e:
        st.error(f"❌ Data Loading Error: {e}")
        st.info("Check if 'audit_data.csv' is in your GitHub root folder and named correctly.")
        st.stop()
    
    # Clean column names for safety
    df.columns = df.columns.str.strip()

    # 2. Logic Check & Forensic Calculations
    # Ensuring all derived columns exist
    if 'Efficiency_Index' not in df.columns:
        df['Efficiency_Index'] = df['federal_spending'] / df['annual_avg_emplvl']
    
    if 'Salary_Replacement_Ratio' not in df.columns:
        df['Salary_Replacement_Ratio'] = df['Efficiency_Index'] / df['avg_annual_pay']

    df['Salary_Equivalent_Count'] = df['federal_spending'] / df['avg_annual_pay']
    
    # 3. State Benchmarking (Z-Score)
    def get_state(title):
        if ',' in str(title):
            return title.split(',')[-1].strip()
        return "National/Other"
    
    df['State'] = df['area_title'].apply(get_state)
    
    state_stats = df.groupby('State')['Efficiency_Index'].agg(['mean', 'std']).reset_index()
    state_stats.columns = ['State', 'State_Mean', 'State_Std']
    
    df = df.merge(state_stats, on='State', how='left')
    df['State_Std'] = df['State_Std'].replace(0, np.nan) 
    df['Efficiency_State_ZScore'] = (df['Efficiency_Index'] - df['State_Mean']) / df['State_Std']
    df['Efficiency_State_ZScore'] = df['Efficiency_State_ZScore'].fillna(0)
    
    # 4. Traffic Light Risk Levels
    def assign_risk(ratio):
        if ratio > 1.0: 
            return '🚨 Market Perversion'
        elif ratio >= 0.5: 
            return '🟡 Watchlist'
        else: 
            return '✅ Healthy'
    
    df['Audit_Risk_Level'] = df['Salary_Replacement_Ratio'].apply(assign_risk)
    
    return df

# Initialize Data
df = load_and_improve_data()

# --- SIDEBAR FILTERS ---
st.sidebar.header("Forensic Search")
risk_options = df['Audit_Risk_Level'].unique()
risk_filter = st.sidebar.multiselect("Filter by Audit Risk:", options=risk_options, default=risk_options)
search_query = st.sidebar.text_input("Search County Name:")

# Apply Filters
filtered_df = df[df['Audit_Risk_Level'].isin(risk_filter)]
if search_query:
    filtered_df = filtered_df[filtered_df['area_title'].str.contains(search_query, case=False)]

# --- DASHBOARD LAYOUT ---
st.title("🏛️ Federal Earmark Efficiency Audit")
st.markdown("### Identifying Market Perversion via Taxpayer-to-Private Sector Ratios")

# Top Row Scorecards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Audited Spend", f"${df['federal_spending'].sum():,.0f}")
col2.metric("Avg Efficiency Index", f"${df['Efficiency_Index'].mean():,.0f}")
col3.metric("Critical Red Flags", len(df[df['Audit_Risk_Level'] == '🚨 Market Perversion']))
col4.metric("Avg Wage Growth", f"{df['oty_avg_annual_pay_pct_chg'].mean():.2f}%")

st.divider()

# Visualization
st.header("📈 Spending vs. Local Wage Growth")
fig = px.scatter(
    filtered_df, x='federal_spending', y='oty_avg_annual_pay_pct_chg',
    size='Efficiency_Index', color='Audit_Risk_Level',
    hover_name='area_title',
    hover_data=['Salary_Equivalent_Count', 'Efficiency_State_ZScore'],
    color_discrete_map={'🚨 Market Perversion': '#e63946', '🟡 Watchlist': '#fca311', '✅ Healthy': '#2a9d8f'},
    labels={'oty_avg_annual_pay_pct_chg': 'Wage Growth (%)', 'federal_spending': 'Federal Spend ($)'},
    template='plotly_white'
)
fig.add_hline(y=1.5, line_dash="dot", annotation_text="Inflation Target (1.5%)")
st.plotly_chart(fig, use_container_width=True)

# Forensic Table
st.header("📋 Audit Ledger: Market Perversion Rankings")
st.dataframe(
    filtered_df[['area_title', 'State', 'federal_spending', 'Efficiency_Index', 
                 'Salary_Equivalent_Count', 'Audit_Risk_Level']]
    .sort_values(by='Efficiency_Index', ascending=False),
    use_container_width=True
)
