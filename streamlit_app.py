import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# 1. Page Configuration
st.set_page_config(
    page_title="Forensic Audit: Federal Spending",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished Metric Cards
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 28px;
        color: #1E3A8A;
    }
    [data-testid="stMetricLabel"] {
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .main {
        background-color: #f8fafc;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data
def load_and_improve_data():
    try:
        df = pd.read_csv('audit_data.csv')
    except Exception as e:
        st.error(f"Data Connection Error: {e}")
        st.stop()
    
    df.columns = df.columns.str.strip()
    def get_state(title):
        if ',' in str(title): return title.split(',')[-1].strip()
        return "National/Other"
    
    df['State'] = df['area_title'].apply(get_state)

    # ALLOCATION LOGIC (The Math Fix)
    state_totals = df.groupby('State').agg({
        'annual_avg_emplvl': 'sum',
        'federal_spending': 'max' 
    }).reset_index()
    state_totals.columns = ['State', 'State_Total_Jobs', 'State_Total_Spending']
    df = df.merge(state_totals, on='State', how='left')
    df['Allocated_Spending'] = df['State_Total_Spending'] * (df['annual_avg_emplvl'] / df['State_Total_Jobs'])

    # FORENSIC METRICS
    df['Efficiency_Index'] = df['Allocated_Spending'] / df['annual_avg_emplvl']
    df['Salary_Replacement_Ratio'] = df['Efficiency_Index'] / df['avg_annual_pay']
    df['Salary_Equivalent_Count'] = df['Allocated_Spending'] / df['avg_annual_pay']

    def assign_risk(ratio):
        if ratio > 1.0: return '🚨 Market Perversion'
        elif ratio >= 0.5: return '🟡 Watchlist'
        else: return '✅ Healthy'
    df['Audit_Risk_Level'] = df['Salary_Replacement_Ratio'].apply(assign_risk)
    
    return df

# Initialize
df = load_and_improve_data()

# --- SIDEBAR: NAVIGATION & FILTERS ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/8/80/Seal_of_the_United_States_Department_of_the_Treasury.svg", width=100)
    st.title("Audit Controls")
    st.markdown("---")
    risk_filter = st.multiselect("Risk Category", options=df['Audit_Risk_Level'].unique(), default=df['Audit_Risk_Level'].unique())
    search = st.text_input("📍 Search County/MSA")
    st.markdown("---")
    st.info("Version 2.1: Pro-Rata Allocation Enabled")

# Filter Data
filtered_df = df[df['Audit_Risk_Level'].isin(risk_filter)]
if search:
    filtered_df = filtered_df[filtered_df['area_title'].str.contains(search, case=False)]

# --- MAIN DASHBOARD ---
st.title("🏛️ Federal Earmark Forensic Audit")
st.subheader("Efficiency Analysis: FY2024 Spending vs. Local Private Workforce")

# 1. High-Level Metrics Row
m1, m2, m3, m4 = st.columns(4)
total_spend = df.groupby('State')['State_Total_Spending'].max().sum()
m1.metric("Total Audited Budget", f"${total_spend/1e9:.1f}B")
m2.metric("Efficiency Index (Avg)", f"${df['Efficiency_Index'].mean():,.0f}")
m3.metric("Critical Red Flags", len(df[df['Audit_Risk_Level'] == '🚨 Market Perversion']))
m4.metric("Avg Wage Growth", f"{df['oty_avg_annual_pay_pct_chg'].mean():.2f}%")

st.markdown("---")

# 2. Visualizations Row
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("#### Economic Decoupling: Allocated Spend vs. Wage Growth")
    fig = px.scatter(
        filtered_df, x='Allocated_Spending', y='oty_avg_annual_pay_pct_chg',
        size='Efficiency_Index', color='Audit_Risk_Level',
        hover_name='area_title',
        color_discrete_map={'🚨 Market Perversion': '#ef4444', '🟡 Watchlist': '#f59e0b', '✅ Healthy': '#10b981'},
        labels={'oty_avg_annual_pay_pct_chg': 'Wage Growth (%)', 'Allocated_Spending': 'Allocated Spend ($)'},
        template='plotly_white', height=500
    )
    fig.update_layout(showlegend=True, margin=dict(l=0, r=0, b=0, t=0))
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown("#### Audit Breakdown")
    risk_counts = filtered_df['Audit_Risk_Level'].value_counts().reset_index()
    fig_pie = px.pie(risk_counts, values='count', names='Audit_Risk_Level', 
                     color='Audit_Risk_Level',
                     color_discrete_map={'🚨 Market Perversion': '#ef4444', '🟡 Watchlist': '#f59e0b', '✅ Healthy': '#10b981'},
                     hole=0.4)
    fig_pie.update_layout(margin=dict(l=0, r=0, b=0, t=0), height=350)
    st.plotly_chart(fig_pie, use_container_width=True)
    
    st.warning("Note: Red flags indicate areas where federal cost-per-job exceeds actual annual salary.")

# 3. Data Definitions & Table
with st.expander("📖 View Methodology & Audit Definitions"):
    st.write("""
    - **Allocated Spending:** Pro-rata distribution of state-level earmarks based on county workforce size.
    - **Efficiency Index:** The total federal cost required to support a single private sector job in that region.
    - **Market Perversion:** Occurs when Efficiency Index > Average Annual Pay (Ratio > 1.0).
    """)

st.markdown("#### 📋 Comprehensive Audit Ledger")
st.dataframe(
    filtered_df[['area_title', 'State', 'Allocated_Spending', 'Efficiency_Index', 'Salary_Replacement_Ratio', 'Audit_Risk_Level']]
    .sort_values(by='Salary_Replacement_Ratio', ascending=False),
    use_container_width=True
)

st.button("Export Audit Report (CSV)")
