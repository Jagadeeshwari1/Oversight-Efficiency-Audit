import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Set Page Config for a professional look
st.set_page_config(page_title="Forensic Oversight Audit", layout="wide")

# --- DATA ENGINE ---
@st.cache_data
def load_and_improve_data():
    # 1. Load the Excel file (Ensure this name matches exactly in GitHub)
    # If you renamed your file to 'audit_data.xlsx', update it here
    df = pd.read_excel('Oversight_Audit_Master (2).xlsx')
    
    # 2. Add Contextual Improvements
    # Salary Equivalent: How many workers' salaries the spend represents
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
try:
    df = load_and_improve_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("Forensic Search")
risk_filter = st.sidebar.multiselect(
    "Filter by Audit Risk:",
    options=df['Audit_Risk_Level'].unique(),
    default=df['Audit_Risk_Level'].unique()
)

search_query = st.sidebar.text_input("Search County/Area Name:")

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

# Visualization Section
st.header("📈 The Inverse Correlation: Spending vs. Local Growth")
st.caption("Hover over bubbles to see County-specific Salary Equivalents")

fig = px.scatter(
    filtered_df, 
    x='federal_spending', 
    y='oty_avg_annual_pay_pct_chg',
    size='Efficiency_Index', 
    color='Audit_Risk_Level',
    hover_name='area_title',
    hover_data=['Salary_Equivalent_Count', 'Efficiency_State_ZScore'],
    color_discrete_map={
        '🚨 Market Perversion': '#e63946', 
        '🟡 Watchlist': '#fca311', 
        '✅ Healthy': '#2a9d8f'
    },
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

st.markdown("---")
st.info("💡 **Auditor Note:** 'Market Perversion' is triggered when the federal cost to support a job exceeds the actual annual private-sector salary of that job.")
