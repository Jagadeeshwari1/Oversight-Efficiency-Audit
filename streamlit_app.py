import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from sklearn.linear_model import LinearRegression

# 1. Page Config
st.set_page_config(page_title="Open The Books: Predictive Audit", layout="wide")

# --- DATA ENGINE ---
@st.cache_data
def load_and_improve_data():
    df = pd.read_csv('audit_data.csv')
    df.columns = df.columns.str.strip()
    
    # State & Allocation Logic
    df['State'] = df['area_title'].apply(lambda x: x.split(',')[-1].strip() if ',' in str(x) else "National")
    state_totals = df.groupby('State').agg({'annual_avg_emplvl': 'sum', 'federal_spending': 'max'}).reset_index()
    state_totals.columns = ['State', 'State_Total_Jobs', 'State_Total_Spending']
    df = df.merge(state_totals, on='State', how='left')
    df['Allocated_Spending'] = df['State_Total_Spending'] * (df['annual_avg_emplvl'] / df['State_Total_Jobs'])

    # Metrics
    df['Efficiency_Index'] = df['Allocated_Spending'] / df['annual_avg_emplvl']
    df['Salary_Replacement_Ratio'] = df['Efficiency_Index'] / df['avg_annual_pay']
    
    def assign_risk(ratio):
        if ratio > 1.0: return '🚨 Market Perversion'
        elif ratio >= 0.5: return '🟡 Watchlist'
        else: return '✅ Healthy'
    df['Audit_Risk_Level'] = df['Salary_Replacement_Ratio'].apply(assign_risk)
    
    # --- PREDICTIVE MODELING (ML) ---
    # We predict Wage Growth based on Allocated Spending
    X = df[['Allocated_Spending']].values
    y = df['oty_avg_annual_pay_pct_chg'].values
    model = LinearRegression()
    model.fit(X, y)
    
    df['Predicted_Wage_Growth'] = model.predict(X)
    df['Growth_Deficit'] = df['oty_avg_annual_pay_pct_chg'] - df['Predicted_Wage_Growth']
    
    return df

df = load_and_improve_data()

# --- BRANDED HEADER ---
st.markdown("""
    <div style="background: linear-gradient(90deg, #1E3A8A 0%, #B91C1C 100%); padding: 25px; border-radius: 15px; color: white; text-align: center;">
        <h1 style='margin:0;'>🏛️ OPEN THE BOOKS: PREDICTIVE AUDITOR</h1>
        <p style='margin:0; opacity:0.9;'>AI-Driven Economic Impact & Wage Growth Prediction</p>
    </div>
    """, unsafe_allow_html=True)

# --- SIDEBAR: DYNAMIC AI CHATBOT ---
with st.sidebar:
    st.title("🤖 AI Auditor Bot")
    st.caption("I can now answer specific questions about the data.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if chat_input := st.chat_input("Ex: Which state has the most Red Flags?"):
        st.session_state.messages.append({"role": "user", "content": chat_input})
        st.chat_message("user").write(chat_input)
        
        # --- DYNAMIC RESPONSE LOGIC ---
        query = chat_input.lower()
        if "red flag" in query or "market perversion" in query:
            count = len(df[df['Audit_Risk_Level'] == '🚨 Market Perversion'])
            top_state = df[df['Audit_Risk_Level'] == '🚨 Market Perversion']['State'].value_counts().idxmax()
            answer = f"There are {count} Market Perversions. {top_state} has the highest concentration of these red flags."
        elif "highest spending" in query:
            max_area = df.loc[df['Allocated_Spending'].idxmax(), 'area_title']
            answer = f"The area with the highest allocated spending is {max_area}."
        elif "efficiency" in query:
            avg_eff = df['Efficiency_Index'].mean()
            answer = f"The average Efficiency Index across all counties is ${avg_eff:,.2f} per job."
        else:
            answer = "I'm analyzing the data. Could you ask specifically about Red Flags, Spending levels, or Efficiency?"

        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.chat_message("assistant").write(answer)

# --- PREDICTIVE DASHBOARD SECTION ---
st.header("🔮 Predictive Audit: Wage Growth Forecasting")
st.markdown("""
This model uses **Linear Regression** to calculate the 'Expected Wage Growth' based on federal investment. 
Counties appearing **below** the line are failing to translate taxpayer dollars into citizen income.
""")

fig_pred = px.scatter(df, x='Allocated_Spending', y='oty_avg_annual_pay_pct_chg',
                 color='Audit_Risk_Level', hover_name='area_title',
                 trendline="ols", # This adds the predictive regression line
                 title="Actual vs. Predicted Growth")
st.plotly_chart(fig_pred, use_container_width=True)

# Distribution of the "Growth Deficit"
st.subheader("⚠️ Underperforming Counties (Predictive Deficit)")
deficit_df = df[df['Growth_Deficit'] < 0].sort_values('Growth_Deficit').head(10)
fig_bar = px.bar(deficit_df, x='area_title', y='Growth_Deficit', 
                 title="Top 10 Counties with Highest Wage Growth Deficit (Relative to Spend)",
                 color_discrete_sequence=['#B91C1C'])
st.plotly_chart(fig_bar, use_container_width=True)

# --- DATA TABLE ---
st.header("📋 Audit Ledger with Predictive Metrics")
st.dataframe(df[['area_title', 'Allocated_Spending', 'oty_avg_annual_pay_pct_chg', 'Predicted_Wage_Growth', 'Growth_Deficit', 'Audit_Risk_Level']]
             .sort_values('Growth_Deficit'), use_container_width=True)
