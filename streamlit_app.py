import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# 1. Page Configuration
st.set_page_config(
    page_title="Open The Books: Forensic Audit",
    page_icon="🏛️",
    layout="wide",
)

# 2. Custom Branding & CSS
st.markdown("""
    <style>
    /* Patriotic Gradient Header */
    .header-container {
        background: linear-gradient(90deg, #1E3A8A 0%, #B91C1C 100%);
        padding: 40px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }
    /* Metric Card Polishing */
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
    
    # State Extraction
    def get_state(title):
        if ',' in str(title): return title.split(',')[-1].strip()
        return "National/Other"
    df['State'] = df['area_title'].apply(get_state)

    # Pro-Rata Allocation Logic
    state_totals = df.groupby('State').agg({'annual_avg_emplvl': 'sum', 'federal_spending': 'max'}).reset_index()
    state_totals.columns = ['State', 'State_Total_Jobs', 'State_Total_Spending']
    df = df.merge(state_totals, on='State', how='left')
    df['Allocated_Spending'] = df['State_Total_Spending'] * (df['annual_avg_emplvl'] / df['State_Total_Jobs'])

    # Forensic Metrics
    df['Efficiency_Index'] = df['Allocated_Spending'] / df['annual_avg_emplvl']
    df['Salary_Replacement_Ratio'] = df['Efficiency_Index'] / df['avg_annual_pay']
    
    # Risk Leveling
    def assign_risk(ratio):
        if ratio > 1.0: return '🚨 Market Perversion'
        elif ratio >= 0.5: return '🟡 Watchlist'
        else: return '✅ Healthy'
    df['Audit_Risk_Level'] = df['Salary_Replacement_Ratio'].apply(assign_risk)
    
    return df

df = load_and_improve_data()

# --- SIDEBAR: NAVIGATION & DYNAMIC AI BOT ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/8/80/Seal_of_the_United_States_Department_of_the_Treasury.svg", width=80)
    st.title("🛡️ Audit Controls")
    
    risk_filter = st.multiselect("Risk Category", options=df['Audit_Risk_Level'].unique(), default=df['Audit_Risk_Level'].unique())
    search = st.text_input("📍 Search County")

    st.markdown("---")
    st.markdown("### 🤖 AI Auditor Chat")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "I am the AI Auditor. Ask me about Red Flags or State spending."}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if chat_input := st.chat_input("Ex: How many red flags?"):
        st.session_state.messages.append({"role": "user", "content": chat_input})
        st.chat_message("user").write(chat_input)
        
        # --- DYNAMIC AI LOGIC ---
        query = chat_input.lower()
        if "red flag" in query or "market perversion" in query:
            val = len(df[df['Audit_Risk_Level'] == '🚨 Market Perversion'])
            response = f"I've found {val} critical Red Flags (Market Perversions) in the audit."
        elif "spending" in query or "highest" in query:
            top_county = df.loc[df['Allocated_Spending'].idxmax(), 'area_title']
            response = f"The highest allocated federal spend is in {top_county}."
        elif "state" in query:
            top_state = df.groupby('State')['Allocated_Spending'].sum().idxmax()
            response = f"The state with the highest total audited spending is {top_state}."
        else:
            response = "I can analyze Red Flags, Spending levels, and regional Efficiency. Try: 'Show me red flags.'"

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.chat_message("assistant").write(response)

# Filter Data for Visuals
filtered_df = df[df['Audit_Risk_Level'].isin(risk_filter)]
if search:
    filtered_df = filtered_df[filtered_df['area_title'].str.contains(search, case=False)]

# --- MAIN DASHBOARD HEADER ---
st.markdown("""
    <div class="header-container">
        <h1 style='margin:0; font-family:serif; font-size:42px;'>🏛️ OPEN THE BOOKS</h1>
        <p style='margin:0; font-size:20px; font-weight:lighter; opacity:0.9;'>Forensic Audit: Federal Spending Efficiency & Market Impact</p>
    </div>
    """, unsafe_allow_html=True)

# KPI Row
m1, m2, m3, m4 = st.columns(4)
total_spend = df.groupby('State')['State_Total_Spending'].max().sum()
m1.metric("FEDERAL SPENDING", f"${total_spend/1e9:.2f}B")
m2.metric("AVG EFFICIENCY INDEX", f"${df['Efficiency_Index'].mean():,.0f}")
m3.metric("RED FLAG COUNT", len(df[df['Audit_Risk_Level'] == '🚨 Market Perversion']))
m4.metric("AVG WAGE GROWTH", f"{df['oty_avg_annual_pay_pct_chg'].mean():.2f}%")

st.divider()

# --- INTERPRETATION BOX ---
st.info("""
### 🔍 The Auditor's Thesis: Input (Jobs) vs. Outcome (Wages)
To measure **Efficiency**, we look at the **Employment Level** as our anchor. It tells us the price the taxpayer is paying to support each worker. 
However, we use **Wage Growth** as our forensic 'check.' If the taxpayer is paying a high premium per job (High Efficiency Index) but local wages are stagnant, 
it indicates that federal spending is **crowding out the private market** rather than enriching it.
""")

# --- VISUAL SUITE WITH INTERPRETATIONS ---

# Row 1: Correlation & Risk
c1, c2 = st.columns([2, 1])
with c1:
    st.markdown("#### 📈 Decoupling Analysis: Spending vs. Wage Growth")
    fig_scatter = px.scatter(df[df['Audit_Risk_Level'].isin(risk_filter)], x='Allocated_Spending', y='oty_avg_annual_pay_pct_chg',
                 size='Efficiency_Index', color='Audit_Risk_Level', hover_name='area_title',
                 color_discrete_map={'🚨 Market Perversion': '#ef4444', '🟡 Watchlist': '#f59e0b', '✅ Healthy': '#10b981'},
                 template='plotly_white', height=400)
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.markdown("""<div class="interpretation-text"><b>Auditor Interpretation:</b> This chart tracks if federal dollars are actually "buying" economic growth. 
    Points in the <b>Red Zone</b> indicate 'Economic Decoupling'—where massive federal investment is failing to result in private-sector wage increases.</div>""", unsafe_allow_html=True)

with c2:
    st.markdown("#### 🥧 Risk Profile Breakdown")
    fig_pie = px.pie(df[df['Audit_Risk_Level'].isin(risk_filter)], names='Audit_Risk_Level', hole=0.4,
                     color='Audit_Risk_Level', color_discrete_map={'🚨 Market Perversion': '#ef4444', '🟡 Watchlist': '#f59e0b', '✅ Healthy': '#10b981'})
    fig_pie.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig_pie, use_container_width=True)
    st.markdown("""<div class="interpretation-text"><b>Interpretation:</b> This measures the 'Portfolio Toxicity.' It quantifies what percentage of the audited market is currently being 'Perverted' (Red) or 'Crowded Out' (Yellow).</div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Row 2: Top States & Distribution
c3, c4 = st.columns(2)
with c3:
    st.markdown("#### 📊 Top 10 States by Job-Support Cost (Least Efficient)")
    state_data = df.groupby('State')['Efficiency_Index'].mean().nlargest(10).reset_index()
    fig_bar = px.bar(state_data, x='State', y='Efficiency_Index', color='State', color_discrete_sequence=['#1E3A8A', '#B91C1C'])
    st.plotly_chart(fig_bar, use_container_width=True)
    st.markdown("""<div class="interpretation-text"><b>Interpretation:</b> These states represent the highest 'Taxpayer Burden.' 
    Higher bars show regions where the government is paying the highest premium to support a single local job.</div>""", unsafe_allow_html=True)

with c4:
    st.markdown("#### 📦 Forensic Distribution: Taxpayer Burden per Job")
    fig_box = px.box(df[df['Audit_Risk_Level'].isin(risk_filter)], y='Efficiency_Index', color='Audit_Risk_Level',
                     color_discrete_map={'🚨 Market Perversion': '#ef4444', '🟡 Watchlist': '#f59e0b', '✅ Healthy': '#10b981'},
                     template='plotly_white', points='outliers')
    st.plotly_chart(fig_box, use_container_width=True)
    st.markdown("""<div class="interpretation-text"><b>Interpretation:</b> Box plots identify 'Statistical Anomalies.' 
    The dots above the whiskers are the <b>Forensic Targets</b>—counties where the cost-per-job is so high it is mathematically indefensible.</div>""", unsafe_allow_html=True)
    
# Row 3: Trend Line
st.markdown("#### 📉 Cumulative Spending Trend vs. Economic Growth")
line_data = filtered_df.sort_values('Allocated_Spending')
fig_line = px.line(line_data, x='Allocated_Spending', y='oty_avg_annual_pay_pct_chg', 
                   template='plotly_white')
st.plotly_chart(fig_line, use_container_width=True)

# --- DATA TABLE & NARRATIVE ---
st.markdown("### 📋 The Audit Ledger")
st.dataframe(filtered_df[['area_title', 'State', 'Allocated_Spending', 'Efficiency_Index', 'Salary_Replacement_Ratio', 'Audit_Risk_Level']]
             .sort_values('Efficiency_Index', ascending=False), use_container_width=True)

with st.expander("📝 Executive Auditor Summary"):
    st.markdown("""
    **Audit Methodology:**
    - **Federal Spending:** Calculated using pro-rata allocation of state totals based on local private sector employment levels.
    - **Efficiency Index:** Represents the total federal cost required to support one job in the region.
    - **Top 10 Chart:** Uses a branded patriotic color scheme to highlight the least efficient regions.
    - **Distribution Plot:** The box plot identifies extreme outliers where job subsidies are significantly higher than the national median.
    """)

st.button("📥 Export Full Forensic Report")
