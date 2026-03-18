import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# 1. Page Configuration & Custom Branding
st.set_page_config(page_title="Forensic Audit v2.5", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1E3A8A;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data
def load_data():
    df = pd.read_csv('audit_data.csv')
    df.columns = df.columns.str.strip()
    
    # State Extraction
    df['State'] = df['area_title'].apply(lambda x: x.split(',')[-1].strip() if ',' in str(x) else "National")
    
    # PRO-RATA ALLOCATION (Fixed Math)
    state_totals = df.groupby('State').agg({'annual_avg_emplvl': 'sum', 'federal_spending': 'max'}).reset_index()
    state_totals.columns = ['State', 'State_Jobs', 'State_Spend']
    df = df.merge(state_totals, on='State')
    df['Allocated_Spending'] = df['State_Spend'] * (df['annual_avg_emplvl'] / df['State_Jobs'])
    
    # Metrics
    df['Efficiency_Index'] = df['Allocated_Spending'] / df['annual_avg_emplvl']
    df['Replacement_Ratio'] = df['Efficiency_Index'] / df['avg_annual_pay']
    
    def assign_risk(ratio):
        if ratio > 1.0: return '🚨 Market Perversion'
        elif ratio >= 0.5: return '🟡 Watchlist'
        return '✅ Healthy'
    df['Risk_Level'] = df['Replacement_Ratio'].apply(assign_risk)
    return df

df = load_data()

# --- SIDEBAR ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/8/80/Seal_of_the_United_States_Department_of_the_Treasury.svg", width=80)
st.sidebar.title("Audit Filters")
state_select = st.sidebar.multiselect("Select States", options=sorted(df['State'].unique()), default=df['State'].unique()[:5])
risk_select = st.sidebar.multiselect("Risk Level", options=df['Risk_Level'].unique(), default=df['Risk_Level'].unique())

filtered_df = df[(df['State'].isin(state_select)) & (df['Risk_Level'].isin(risk_select))]

# --- HEADER SECTION ---
st.title("🏛️ Earmark Forensic Audit: Economic Impact Dashboard")
st.markdown("#### Identifying regions where federal job-subsidies decouple from private-sector wage reality.")

# KPI Row
c1, c2, c3, c4 = st.columns(4)
total_audited = df.groupby('State')['State_Spend'].max().sum()
c1.metric("Total Federal Portfolio", f"${total_audited/1e9:.2f}B")
c2.metric("Avg Efficiency Index", f"${df['Efficiency_Index'].mean():,.0f}")
c3.metric("Market Perversions", len(df[df['Risk_Level'] == '🚨 Market Perversion']))
c4.metric("Avg Private Wage", f"${df['avg_annual_pay'].mean():,.0f}")

st.divider()

# --- VISUALIZATION ROW 1: THE BIG PICTURE ---
col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### 📊 Regional Efficiency Comparison")
    # Bar Chart: Comparing Average Efficiency Index by State
    state_bar = filtered_df.groupby('State')['Efficiency_Index'].mean().sort_values(ascending=False).reset_index()
    fig_bar = px.bar(state_bar, x='State', y='Efficiency_Index', 
                     color='Efficiency_Index', color_continuous_scale='Reds',
                     title="Cost Per Job Supported (State Average)")
    st.plotly_chart(fig_bar, use_container_width=True)

with col_b:
    st.markdown("### 📉 Spending vs. Wage Growth Trend")
    # Line/Scatter Hybrid: Showing how spending correlates with growth
    fig_trend = px.scatter(filtered_df, x='avg_annual_pay', y='oty_avg_annual_pay_pct_chg',
                         size='Allocated_Spending', color='Risk_Level',
                         trendline="ols", title="Wage Growth Momentum vs. Average Pay")
    st.plotly_chart(fig_trend, use_container_width=True)

# --- VISUALIZATION ROW 2: DISTRIBUTION & RISK ---
col_c, col_d = st.columns(2)

with col_c:
    st.markdown("### 🔔 Efficiency Distribution")
    # Histogram: Showing the frequency of specific cost-per-job levels
    fig_hist = px.histogram(filtered_df, x='Efficiency_Index', nbins=50,
                            color='Risk_Level', title="Audit Frequency by Cost-Per-Job")
    st.plotly_chart(fig_hist, use_container_width=True)

with col_d:
    st.markdown("### 🥧 Portfolio Risk Profile")
    # Pie Chart for visual breakdown
    risk_pie = filtered_df['Risk_Level'].value_counts().reset_index()
    fig_pie = px.pie(risk_pie, values='count', names='Risk_Level', hole=0.5,
                     color='Risk_Level', color_discrete_map={'🚨 Market Perversion':'#ef4444', '🟡 Watchlist':'#f59e0b', '✅ Healthy':'#10b981'})
    st.plotly_chart(fig_pie, use_container_width=True)

# --- AUDIT LEDGER ---
st.header("📋 Detailed Audit Ledger")
st.dataframe(filtered_df[['area_title', 'Allocated_Spending', 'Efficiency_Index', 'Replacement_Ratio', 'Risk_Level']].sort_values(by='Efficiency_Index', ascending=False), use_container_width=True)

# --- EXPLANATION SECTION ---
st.markdown("---")
with st.expander("📝 Executive Auditor's Explanation"):
    st.write("""
    ### How to Interpret this Audit:
    1. **Bar Chart (Regional Efficiency):** Shows which states are "expensive" for the taxpayer. A higher bar means the government is paying more to support a single job in that state.
    2. **Scatter Trend:** We look for a *positive* trendline. If the line is flat or negative, it means high federal spending is **not** resulting in higher wage growth for the citizens.
    3. **Histogram (Efficiency Distribution):** This identifies "Normal" spending vs. "Extreme Outliers." The bars on the far right represent the most inefficient use of funds.
    4. **Replacement Ratio:** If this exceeds 1.0, the taxpayer is literally paying more for the job's *overhead* than the worker takes home in *pay*. This is a primary indicator of Market Perversion.
    """)
