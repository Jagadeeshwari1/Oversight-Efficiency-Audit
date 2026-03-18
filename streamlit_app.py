import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from sklearn.linear_model import LinearRegression

# 1. Page Configuration
st.set_page_config(
    page_title="Open The Books: Forensic Audit",
    page_icon="🏛️",
    layout="wide",
)

# 2. Open The Books Branding (Red & Blue Gradient Header)
st.markdown("""
    <style>
    .header-container {
        background: linear-gradient(90deg, #1E3A8A 0%, #B91C1C 100%);
        padding: 40px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
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

    # Allocation Logic
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

    # PREDICTIVE MODEL (Linear Regression)
    X = df[['Allocated_Spending']].values
    y = df['oty_avg_annual_pay_pct_chg'].values
    model = LinearRegression().fit(X, y)
    df['Predicted_Growth'] = model.predict(X)
    df['Growth_Deficit'] = df['oty_avg_annual_pay_pct_chg'] - df['Predicted_Growth']
    
    return df

df = load_and_improve_data()

# --- SIDEBAR: DYNAMIC AI CHATBOT ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/8/80/Seal_of_the_United_States_Department_of_the_Treasury.svg", width=80)
    st.title("🛡️ Forensic Controls")
    
    st.markdown("### Filter Results")
    risk_filter = st.multiselect("Risk Category", options=df['Audit_Risk_Level'].unique(), default=df['Audit_Risk_Level'].unique())
    search = st.text_input("📍 Search County")

    st.markdown("---")
    st.markdown("### 🤖 AI Auditor Chat")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Auditor ready. Ask me about Red Flags or specific State spending."}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if chat_input := st.chat_input("Ask the Auditor..."):
        st.session_state.messages.append({"role": "user", "content": chat_input})
        st.chat_message("user").write(chat_input)
        
        # DYNAMIC RESPONSE LOGIC
        q = chat_input.lower()
        if "red flag" in q or "perversion" in q:
            val = len(df[df['Audit_Risk_Level'] == '🚨 Market Perversion'])
            ans = f"Audit reveals {val} counties are in 'Market Perversion' where federal spend exceeds private pay."
        elif "highest" in q:
            top = df.loc[df['Allocated_Spending'].idxmax(), 'area_title']
            ans = f"The highest spending density is in {top}."
        elif "state" in q:
            found_state = next((s for s in df['State'].unique() if s.lower() in q), None)
            if found_state:
                state_data = df[df['State'] == found_state]
                ans = f"Analysis of {found_state}: Total federal spending allocated is ${state_data['Allocated_Spending'].sum():,.0f}."
            else:
                ans = "I can analyze specific states. Try: 'Tell me about Texas'."
        else:
            ans = "I'm monitoring the data. I can answer questions about Red Flags, Highest Spending, or specific States."

        st.session_state.messages.append({"role": "assistant", "content": ans})
        st.chat_message("assistant").write(ans)

# Filter Data
filtered_df = df[df['Audit_Risk_Level'].isin(risk_filter)]
if search:
    filtered_df = filtered_df[filtered_df['area_title'].str.contains(search, case=False)]

# --- HEADER ---
st.markdown("""
    <div class="header-container">
        <h1 style='margin:0; font-family:serif; font-size:42px;'>🏛️ OPEN THE BOOKS</h1>
        <p style='margin:0; font-size:20px; font-weight:lighter; opacity:0.9;'>Forensic Audit: Federal Spending Efficiency & Market Impact</p>
    </div>
    """, unsafe_allow_html=True)

# KPI Scorecards
m1, m2, m3, m4 = st.columns(4)
total_spend = df.groupby('State')['State_Total_Spending'].max().sum()
# REPLACED TOTAL PORTFOLIO WITH FEDERAL SPENDING
m1.metric("FEDERAL SPENDING", f"${total_spend/1e9:.1f}B")
m2.metric("AVG EFFICIENCY INDEX", f"${df['Efficiency_Index'].mean():,.0f}")
m3.metric("RED FLAG COUNT", len(df[df['Audit_Risk_Level'] == '🚨 Market Perversion']))
m4.metric("AVG WAGE GROWTH", f"{df['oty_avg_annual_pay_pct_chg'].mean():.2f}%")

st.divider()

# --- VISUAL SUITE ---

# Row 1: Predictive Analysis and Risk Breakdown
c1, c2 = st.columns([2, 1])
with c1:
    st.markdown("#### 🔮 Predictive Growth Model: Actual vs. Expected")
    fig_scatter = px.scatter(filtered_df, x='Allocated_Spending', y='oty_avg_annual_pay_pct_chg',
                 size='Efficiency_Index', color='Audit_Risk_Level', hover_name='area_title',
                 trendline="ols", # This is the predictive regression line
                 color_discrete_map={'🚨 Market Perversion': '#ef4444', '🟡 Watchlist': '#f59e0b', '✅ Healthy': '#10b981'},
                 template='plotly_white', height=400)
    st.plotly_chart(fig_scatter, use_container_width=True)

with c2:
    st.markdown("#### 🥧 Risk Profile Breakdown")
    fig_pie = px.pie(filtered_df, names='Audit_Risk_Level', hole=0.4,
                     color='Audit_Risk_Level', color_discrete_map={'🚨 Market Perversion': '#ef4444', '🟡 Watchlist': '#f59e0b', '✅ Healthy': '#10b981'})
    fig_pie.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig_pie, use_container_width=True)

# Row 2: State Performance & Efficiency Outliers
c3, c4 = st.columns(2)
with c3:
    st.markdown("#### 📊 Top 10 States by Efficiency Index (Cost Per Job)")
    state_data = filtered_df.groupby('State')['Efficiency_Index'].mean().nlargest(10).reset_index()
    fig_bar = px.bar(state_data, x='State', y='Efficiency_Index', color='Efficiency_Index', 
                     color_continuous_scale='Reds')
    st.plotly_chart(fig_bar, use_container_width=True)

with c4:
    # REPLACED HISTOGRAM WITH BOX PLOT FOR OUTLIER ANALYSIS
    st.markdown("#### 📉 Efficiency Distribution & Outlier Analysis")
    fig_box = px.box(filtered_df, y='Efficiency_Index', x='Audit_Risk_Level', color='Audit_Risk_Level',
                     color_discrete_map={'🚨 Market Perversion': '#ef4444', '🟡 Watchlist': '#f59e0b', '✅ Healthy': '#10b981'},
                     template='plotly_white', height=400)
    st.plotly_chart(fig_box, use_container_width=True)

# Row 3: Growth Deficit Trend
st.markdown("#### 📉 Wage Growth Deficit (Underperforming Markets)")
line_data = filtered_df.sort_values('Growth_Deficit')
fig_line = px.line(line_data, x='area_title', y='Growth_Deficit', 
                   template='plotly_white', title="Ranking Counties by Growth Deficit (Actual - Predicted)")
st.plotly_chart(fig_line, use_container_width=True)

# --- CONTENT & DATA TABLE ---
st.markdown("### 📋 The Audit Ledger")
st.dataframe(filtered_df[['area_title', 'State', 'Allocated_Spending', 'Efficiency_Index', 'Growth_Deficit', 'Audit_Risk_Level']]
             .sort_values('Efficiency_Index', ascending=False), use_container_width=True)

with st.expander("📝 Auditor's Narrative & Predictive Logic"):
    st.markdown("""
    **Executive Summary:**
    This dashboard utilizes a **Linear Regression model** to calculate the 'Expected Wage Growth' a county should have based on federal investment. 
    
    **New Metrics:**
    1. **Federal Spending:** Total allocated federal taxpayer dollars in the audit scope.
    2. **Growth Deficit:** The difference between actual wage growth and the model's prediction. A negative deficit means federal spending is **not** producing the expected local economic return.
    3. **Outlier Analysis (Box Plot):** Visually identifies the "Extreme Waste" counties that pull the average Efficiency Index higher.
    """)

st.button("📥 Export Full Forensic Report")
