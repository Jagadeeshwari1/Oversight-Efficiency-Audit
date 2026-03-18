import streamlit as st
import pandas as pd
import plotly.express as px

# Set Page Config
st.set_page_config(page_title="Oversight Forensic Audit", layout="wide")

# 1. Title & Executive Summary
st.title("🏛️ Federal Earmark Efficiency Audit (FY2024)")
st.markdown("""
**Audit Goal:** Identify "Market Perversion" where federal spending decouples from local economic reality.
**Target Metric:** Efficiency Index (Taxpayer Cost Per Private Sector Job).
""")

# 2. Load and Improve Data (Internal Logic)
@st.cache_data
def load_and_improve_data():
   df = pd.read_excel('Oversight_Audit_Master (2).xlsx')
    
    # Contextual Improvements
    df['Salary_Equivalent_Count'] = df['federal_spending'] / df['avg_annual_pay']
    
    # Traffic Light Risk Levels
    def assign_risk(ratio):
        if ratio > 1.0: return '🚨 Market Perversion'
        elif ratio >= 0.5: return '🟡 Watchlist'
        else: return '✅ Healthy'
    
    df['Audit_Risk_Level'] = df['Salary_Replacement_Ratio'].apply(assign_risk)
    return df

df = load_and_improve_data()

# 3. Sidebar Filters
st.sidebar.header("Forensic Filters")
risk_filter = st.sidebar.multiselect("Filter by Risk Level", 
                                     options=df['Audit_Risk_Level'].unique(),
                                     default=df['Audit_Risk_Level'].unique())
filtered_df = df[df['Audit_Risk_Level'].isin(risk_filter)]

# 4. Top Row: Scorecards
col1, col2, col3 = st.columns(3)
col1.metric("Total Audited Spend", f"${df['federal_spending'].sum():,.0f}")
col2.metric("Avg Wage Growth", f"{df['oty_avg_annual_pay_pct_chg'].mean():.2f}%")
col3.metric("Records Audited", len(df))

# 5. The "Smoking Gun" Chart
st.header("📈 The Inverse Correlation: Spending vs. Wage Growth")
fig = px.scatter(filtered_df, x='federal_spending', y='oty_avg_annual_pay_pct_chg',
                 size='Efficiency_Index', color='Audit_Risk_Level',
                 hover_name='area_title', 
                 color_discrete_map={'🚨 Market Perversion': 'red', '🟡 Watchlist': 'orange', '✅ Healthy': 'green'},
                 labels={'oty_avg_annual_pay_pct_chg': 'Wage Growth (%)', 'federal_spending': 'Federal Spend ($)'})
fig.add_hline(y=1.5, line_dash="dot", annotation_text="Inflation Target")
st.plotly_chart(fig, use_container_width=True)

# 6. Forensic Table (Traffic Light Table)
st.header("📋 Market Perversion Rankings")
st.dataframe(filtered_df[['area_title', 'federal_spending', 'Efficiency_Index', 
                          'Salary_Equivalent_Count', 'Audit_Risk_Level']]
             .sort_values(by='Efficiency_Index', ascending=False),
             use_container_width=True)
