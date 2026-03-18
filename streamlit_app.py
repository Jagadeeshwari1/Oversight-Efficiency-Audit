import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from sklearn.linear_model import LinearRegression

# 1. Page Configuration
st.set_page_config(page_title="Open The Books: Predictive Audit", layout="wide")

# 2. Open The Books Branding (Red & Blue Gradient)
st.markdown("""
    <style>
    .header-container {
        background: linear-gradient(90deg, #1E3A8A 0%, #B91C1C 100%);
        padding: 35px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
    }
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #1E3A8A;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

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

    # Forensic Metrics
    df['Efficiency_Index'] = df['Allocated_Spending'] / df['annual_avg_emplvl']
    df['Salary_Replacement_Ratio'] = df['Efficiency_Index'] / df['avg_annual_pay']
    
    def assign_risk(ratio):
        if ratio > 1.0: return '🚨 Market Perversion'
        elif ratio >= 0.5: return '🟡 Watchlist'
        else: return '✅ Healthy'
    df['Audit_Risk_Level'] = df['Salary_Replacement_Ratio'].apply(assign_risk)

    # --- PREDICTIVE MODEL ---
    X = df[['Allocated_Spending']].values
    y = df['oty_avg_annual_pay_pct_chg'].values
    model = LinearRegression().fit(X, y)
    df['Predicted_Growth'] = model.predict(X)
    df['Growth_Deficit'] = df['oty_avg_annual_pay_pct_chg'] - df['Predicted_Growth']
    
    return df

df = load_and_improve_data()

# --- SIDEBAR: SMART AI AUDITOR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/8/80/Seal_of_the_United_States_Department_of_the_Treasury.svg", width=80)
    st.title("🛡️ AI Auditor Bot")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "I am the AI Auditor. Ask me about Red Flags or State Efficiency."}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if chat_input := st.chat_input("Ask a question..."):
        st.session_state.messages.append({"role": "user", "content": chat_input})
        st.chat_message("user").write(chat_input)
        
        # DYNAMIC LOGIC
        q = chat_input.lower()
        if "red flag" in q or "perversion" in q:
            val = len(df[df['Audit_Risk_Level'] == '🚨 Market Perversion'])
            ans = f"Audit complete: I found {val} counties in 'Market Perversion' where federal spend exceeds private pay."
        elif "highest" in q:
            top = df.loc[df['Allocated_Spending'].idxmax(), 'area_title']
            ans = f"The highest allocated spend is in {top}."
        else:
            ans = "I can analyze Red Flags, Efficiency, and Spending. Try: 'How many red flags are there?'"
        
        st.session_state.messages.append({"role": "assistant", "content": ans})
        st.chat_message("assistant").write(ans)

# --- HEADER ---
st.markdown("""
    <div class="header-container">
        <h1 style='margin:0; font-family:serif; font-size:38px;'>🏛️ OPEN THE BOOKS</h1>
        <p style='margin:0; font-size:18px; opacity:0.9;'>Forensic AI Audit & Predictive Economic Impact</p>
    </div>
    """, unsafe_allow_html=True)

# Metrics
c1, c2, c3, c4 = st.columns(4)
total_s = df.groupby('State')['State_Total_Spending'].max().sum()
c1.metric("TOTAL PORTFOLIO", f"${total_s/1e9:.1f}B")
c2.metric("AVG EFFICIENCY", f"${df['Efficiency_Index'].mean():,.0f}")
c3.metric("RED FLAGS", len(df[df['Audit_Risk_Level'] == '🚨 Market Perversion']))
c4.metric("AVG WAGE GROWTH", f"{df['oty_avg_annual_pay_pct_chg'].mean():.2f}%")

st.divider()

# --- VISUAL SUITE ---
row1_left, row1_right = st.columns([2, 1])

with row1_left:
    st.markdown("#### 🔮 Actual vs. Predicted Wage Growth (Regression)")
    fig_scatter = px.scatter(df, x='Allocated_Spending', y='oty_avg_annual_pay_pct_chg',
                 color='Audit_Risk_Level', size='Efficiency_Index', hover_name='area_title',
                 trendline="ols", # This is what needs statsmodels
                 color_discrete_map={'🚨 Market Perversion': '#ef4444', '🟡 Watchlist': '#f59e0b', '✅ Healthy': '#10b981'},
                 template='plotly_white')
    st.plotly_chart(fig_scatter, use_container_width=True)

with row1_right:
    st.markdown("#### 🥧 Audit Risk Profile")
    fig_pie = px.pie(df, names='Audit_Risk_Level', hole=0.4,
                     color='Audit_Risk_Level', color_discrete_map={'🚨 Market Perversion': '#ef4444', '🟡 Watchlist': '#f59e0b', '✅ Healthy': '#10b981'})
    st.plotly_chart(fig_pie, use_container_width=True)

row2_left, row2_right = st.columns(2)

with row2_left:
    st.markdown("#### 📊 Top 10 States by Job-Support Cost")
    state_avg = df.groupby('State')['Efficiency_Index'].mean().nlargest(10).reset_index()
    fig_bar = px.bar(state_avg, x='State', y='Efficiency_Index', color='Efficiency_Index', color_continuous_scale='Reds')
    st.plotly_chart(fig_bar, use_container_width=True)

with row2_right:
    st.markdown("#### 📉 Distribution of Taxpayer Burden")
    fig_hist = px.histogram(df, x='Efficiency_Index', color='Audit_Risk_Level', 
                            color_discrete_map={'🚨 Market Perversion': '#ef4444', '🟡 Watchlist': '#f59e0b', '✅ Healthy': '#10b981'})
    st.plotly_chart(fig_hist, use_container_width=True)

# --- LEDGER ---
st.markdown("### 📋 Full Audit Ledger")
st.dataframe(df[['area_title', 'State', 'Allocated_Spending', 'Efficiency_Index', 'Growth_Deficit', 'Audit_Risk_Level']]
             .sort_values('Efficiency_Index', ascending=False), use_container_width=True)

st.info("💡 **Methodology:** This audit utilizes Linear Regression to predict 'Expected Growth' based on federal investment. The 'Growth Deficit' indicates regions where spending failed to meet economic expectations.")
