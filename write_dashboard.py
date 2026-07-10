#!/usr/bin/env python3
"""Write the full rich dashboard to dashboard/app.py"""

dashboard_code = '''"""
TRON Enterprise Dashboard - Full Rich UI with Animations & Visualizations
Data Center Licensing, Live Metrics, ROI Simulator, and Royalty Management
"""
import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# ===== PAGE CONFIG =====
API_BASE = "http://127.0.0.1:9000"
TIMEOUT = 5

st.set_page_config(
    page_title="TRON Enterprise Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# ===== CUSTOM CSS & ANIMATIONS =====
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Space+Mono:wght@400;700&display=swap');
    
    * { font-family: 'Space Mono', monospace; }
    
    @keyframes glow {
        0%, 100% { text-shadow: 0 0 5px #00d9ff, 0 0 10px #00d9ff, 0 0 20px #00d9ff; }
        50% { text-shadow: 0 0 10px #00d9ff, 0 0 20px #00d9ff, 0 0 40px #00d9ff; }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    @keyframes slide-in {
        from { transform: translateX(-30px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    h1 {
        font-family: 'Orbitron', sans-serif;
        animation: glow 3s infinite;
        color: #00d9ff;
        text-align: center;
        font-size: 3.5em !important;
        margin-bottom: 0.5rem !important;
        text-transform: uppercase;
        letter-spacing: 3px;
    }
    
    h2 {
        font-family: 'Orbitron', sans-serif;
        animation: glow 3s infinite;
        color: #00d9ff;
        font-size: 1.8em !important;
        margin-top: 2rem !important;
        letter-spacing: 2px;
    }
    
    h3 {
        color: #00d9ff;
        font-family: 'Orbitron', sans-serif;
        letter-spacing: 1px;
    }
    
    .metric-box {
        background: linear-gradient(135deg, #0a1e2e 0%, #16213e 100%);
        border: 2px solid #00d9ff;
        border-radius: 10px;
        padding: 2rem;
        animation: glow 3s infinite, float 3s ease-in-out infinite;
        box-shadow: 0 0 20px rgba(0, 217, 255, 0.3);
        margin: 1rem 0;
    }
    
    .dashboard-panel {
        background: linear-gradient(135deg, rgba(10, 30, 46, 0.8) 0%, rgba(22, 33, 62, 0.8) 100%);
        border-left: 4px solid #00d9ff;
        border-radius: 8px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 0 15px rgba(0, 217, 255, 0.2);
        animation: slide-in 0.8s ease-out;
    }
    
    .rack-card {
        background: linear-gradient(135deg, #1a2332 0%, #0f1419 100%);
        border: 2px solid #00d9ff;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 0.8rem 0;
        animation: glow 4s infinite, float 4s ease-in-out infinite;
        box-shadow: 0 0 15px rgba(0, 217, 255, 0.3);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #00d9ff 0%, #0099ff 100%);
        color: #0a1e2e !important;
        border: none;
        border-radius: 8px;
        font-weight: bold !important;
        font-family: 'Orbitron', sans-serif;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 0 15px rgba(0, 217, 255, 0.5);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        box-shadow: 0 0 30px rgba(0, 217, 255, 0.8);
        transform: scale(1.05);
    }
    
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background: rgba(26, 35, 50, 0.9) !important;
        color: #00d9ff !important;
        border: 2px solid #00d9ff !important;
        border-radius: 6px !important;
    }
    
    .stTabs [role="tab"] {
        background: linear-gradient(135deg, #1a2332 0%, #0f1419 100%);
        border: 2px solid #00d9ff;
        color: #00d9ff !important;
        font-family: 'Orbitron', sans-serif;
        letter-spacing: 1px;
        margin: 0.5rem;
        border-radius: 6px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00d9ff 0%, #0099ff 100%);
        color: #0a1e2e !important;
        box-shadow: 0 0 20px rgba(0, 217, 255, 0.6);
    }
    
    hr {
        border: 1px solid #00d9ff;
        box-shadow: 0 0 10px rgba(0, 217, 255, 0.3);
    }
    
    .status-online {
        color: #00ff00;
        font-weight: bold;
        animation: pulse 2s infinite;
    }
    
    .status-offline {
        color: #ff0000;
        font-weight: bold;
    }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: linear-gradient(135deg, #0a1e2e 0%, #16213e 100%);
    }
    
    body {
        background: linear-gradient(135deg, #0a1e2e 0%, #16213e 100%);
    }
    
    .stAlert {
        border-left: 4px solid #00d9ff;
        background: rgba(0, 217, 255, 0.1);
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ===== HELPER FUNCTIONS =====
@st.cache_data(ttl=3)
def fetch_racks():
    try:
        r = requests.get(f"{API_BASE}/enterprise/racks", timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json().get("racks", [])
    except:
        pass
    return []

@st.cache_data(ttl=3)
def fetch_workers():
    try:
        r = requests.get(f"{API_BASE}/workers", timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json().get("workers", [])
    except:
        pass
    return []

@st.cache_data(ttl=10)
def fetch_active_jobs():
    try:
        r = requests.get(f"{API_BASE}/active_jobs", timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json().get("jobs", [])
    except:
        pass
    return []

@st.cache_data(ttl=10)
def fetch_ledger():
    try:
        r = requests.get(f"{API_BASE}/ledger", timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json().get("ledger", [])
    except:
        pass
    return []

def license_facility(location: str, total_gpus: int):
    try:
        payload = {"location": location, "total_gpus": total_gpus}
        r = requests.post(f"{API_BASE}/enterprise/license", json=payload, timeout=TIMEOUT)
        return r.status_code, r.text
    except Exception as e:
        return 500, str(e)

# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("## ⚙️ DASHBOARD CONTROLS")
    st.markdown("---")
    refresh_interval = st.slider("Refresh Interval (seconds)", 1, 30, 5)
    st.markdown("---")
    st.markdown("### 📊 System Status")
    workers = fetch_workers()
    racks = fetch_racks()
    jobs = fetch_active_jobs()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🖥️ Workers", len(workers))
    with col2:
        st.metric("🏢 Racks", len(racks))
    st.metric("💼 Active Jobs", len(jobs))
    st.markdown("---")
    st.markdown("### 📡 API Status")
    try:
        r = requests.get(f"{API_BASE}/health", timeout=2)
        st.success("✅ Master Online") if r.status_code == 200 else st.error("❌ Master Offline")
    except:
        st.error("❌ Master Offline")

# ===== MAIN HEADER =====
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1>🏛️ TRON ENTERPRISE</h1>
    <p style="color: #00d9ff; font-size: 1.2em; letter-spacing: 2px;">AUTONOMOUS COMPUTE NETWORK | DATA CENTER LICENSING & MONETIZATION</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ===== MAIN TABS =====
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "📋 License", "🖥️ Infrastructure", "💰 Royalties", "🎯 ROI"])

# ===== TAB 1: MAIN DASHBOARD =====
with tab1:
    st.markdown("## 📈 Real-Time Dashboard")
    st.markdown("---")
    workers = fetch_workers()
    racks = fetch_racks()
    active_jobs = fetch_active_jobs()
    ledger = fetch_ledger()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-box"><div style="text-align: center;"><h2 style="margin: 0;">🖥️</h2><h3 style="margin: 0; font-size: 2em;">{len(workers)}</h3><p style="color: #0099ff; margin: 0;">Active Workers</p></div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-box"><div style="text-align: center;"><h2 style="margin: 0;">🏢</h2><h3 style="margin: 0; font-size: 2em;">{len(racks)}</h3><p style="color: #0099ff; margin: 0;">Licensed Racks</p></div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-box"><div style="text-align: center;"><h2 style="margin: 0;">💼</h2><h3 style="margin: 0; font-size: 2em;">{len(active_jobs)}</h3><p style="color: #0099ff; margin: 0;">Active Jobs</p></div></div>', unsafe_allow_html=True)
    with col4:
        total_gpus = sum(r.get("total_gpus", 0) for r in racks)
        st.markdown(f'<div class="metric-box"><div style="text-align: center;"><h2 style="margin: 0;">⚡</h2><h3 style="margin: 0; font-size: 2em;">{total_gpus}</h3><p style="color: #0099ff; margin: 0;">Total GPUs</p></div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📊 Worker Distribution")
        if workers:
            worker_states = {}
            for w in workers:
                state = w.get("state", "idle")
                worker_states[state] = worker_states.get(state, 0) + 1
            fig = go.Figure(data=[go.Pie(labels=list(worker_states.keys()), values=list(worker_states.values()), marker=dict(colors=['#00d9ff', '#0099ff', '#00ff00']))])
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#00d9ff'))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No workers online yet")
    
    with col2:
        st.markdown("### 💰 Revenue Breakdown")
        if ledger:
            revenue_by_type = {}
            for entry in ledger:
                t = entry.get('type', 'unknown')
                amt = float(entry.get('amount', 0))
                revenue_by_type[t] = revenue_by_type.get(t, 0) + amt
            fig = go.Figure(data=[go.Bar(x=list(revenue_by_type.keys()), y=list(revenue_by_type.values()), marker_color='#00d9ff')])
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_title="Type", yaxis_title="Revenue ($)", font=dict(color='#00d9ff'))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No revenue data yet")

# ===== TAB 2: LICENSE FACILITY =====
with tab2:
    st.markdown("## 📋 Onboard New Data Center")
    st.markdown("---")
    st.markdown('<div class="dashboard-panel"><h3>🚀 Get Started in Minutes</h3><ul><li>Provide facility location and GPU inventory</li><li>TRON auto-provisions infrastructure</li><li>Start earning 15% royalties immediately</li><li>Monthly payouts via Stripe or Smart Contract</li></ul></div>', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        location = st.text_input("Facility Location", placeholder="e.g., US-East-1, Europe-DE, Asia-SG")
    with col2:
        total_gpus = st.number_input("Total GPUs Available", min_value=1, max_value=10000, step=1, value=10)
    
    if st.button("🚀 LICENSE THIS FACILITY", use_container_width=True):
        if location:
            status, response = license_facility(location, total_gpus)
            if status == 200:
                st.success(f"✅ Facility licensed successfully!")
                st.markdown(f'<div class="dashboard-panel"><strong>Response:</strong><br>{response}</div>', unsafe_allow_html=True)
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ Licensing failed ({status}): {response}")
        else:
            st.warning("⚠️ Please enter a facility location")

# ===== TAB 3: INFRASTRUCTURE =====
with tab3:
    st.markdown("## 🖥️ Live Infrastructure")
    st.markdown("---")
    st.markdown("### 👥 Connected Workers")
    workers = fetch_workers()
    if workers:
        for w in workers:
            st.markdown(f'<div class="rack-card"><div style="display: flex; justify-content: space-between;"><div><h4 style="margin: 0;">{w.get("name", "Unknown")}</h4><p style="margin: 0.3rem 0; color: #0099ff;">🔧 {w.get("gpu_name", "N/A")} | {w.get("vram_gb", "?")} GB VRAM</p><p style="margin: 0; color: #0099ff;">📡 {w.get("network_bandwidth_gbps", "?")} Gbps</p></div><div style="text-align: right;"><span class="status-online">● ONLINE</span></div></div></div>', unsafe_allow_html=True)
    else:
        st.info("No workers connected yet")
    
    st.markdown("---")
    st.markdown("### 🏢 Licensed Racks")
    racks = fetch_racks()
    if racks:
        for rack in racks:
            st.markdown(f'<div class="rack-card"><div style="display: flex; justify-content: space-between;"><div><h4 style="margin: 0;">Rack: {rack.get("id", "Unknown")[:12]}</h4><p style="margin: 0.3rem 0; color: #0099ff;">📍 {rack.get("location", "N/A")}</p><p style="margin: 0; color: #0099ff;">⚡ {rack.get("total_gpus", "?")} GPUs | {rack.get("status", "unknown")}</p></div><div style="text-align: right;"><span style="color: #00ff00; font-weight: bold;">✓ ACTIVE</span></div></div></div>', unsafe_allow_html=True)
    else:
        st.info("No licensed racks yet")

# ===== TAB 4: ROYALTIES =====
with tab4:
    st.markdown("## 💰 Royalty Ledger & Payments")
    st.markdown("---")
    ledger = fetch_ledger()
    if ledger:
        total_revenue = sum(float(entry.get("amount", 0)) for entry in ledger)
        total_royalties = total_revenue * 0.15
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="metric-box"><div style="text-align: center;"><h2 style="margin: 0;">💵</h2><h3 style="margin: 0; font-size: 2em;">${total_revenue:.2f}</h3><p style="color: #0099ff; margin: 0;">Total Revenue</p></div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-box"><div style="text-align: center;"><h2 style="margin: 0;">🏦</h2><h3 style="margin: 0; font-size: 2em;">${total_royalties:.2f}</h3><p style="color: #0099ff; margin: 0;">Your Royalties (15%)</p></div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-box"><div style="text-align: center;"><h2 style="margin: 0;">📊</h2><h3 style="margin: 0; font-size: 2em;">{len(ledger)}</h3><p style="color: #0099ff; margin: 0;">Transactions</p></div></div>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("### 📝 Transaction History")
        for entry in ledger[-20:]:
            st.markdown(f'<div class="dashboard-panel"><div style="display: flex; justify-content: space-between;"><div><strong>{entry.get("type", "unknown")}</strong><p style="margin: 0; color: #0099ff; font-size: 0.9em;">{entry.get("timestamp", "N/A")}</p></div><div style="text-align: right;"><h3 style="margin: 0; color: #00ff00;">${entry.get("amount", 0)}</h3></div></div></div>', unsafe_allow_html=True)
    else:
        st.info("No ledger entries yet")

# ===== TAB 5: ROI SIMULATOR =====
with tab5:
    st.markdown("## 🎯 ROI Simulator")
    st.markdown("---")
    st.markdown('<div class="dashboard-panel"><h3>💡 Calculate Your Potential Earnings</h3><p>Simulate different scenarios and see projected returns</p></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        gpus = st.slider("Number of GPUs", 1, 1000, 10)
    with col2:
        utilization = st.slider("Daily Utilization %", 0, 100, 50)
    with col3:
        gpu_rate = st.slider("$ per GPU/Hour", 0.5, 10.0, 2.0, step=0.5)
    
    st.markdown("---")
    hours_per_day = (24 * utilization) / 100
    daily_revenue = gpus * hours_per_day * gpu_rate
    daily_royalty = daily_revenue * 0.15
    monthly_revenue = daily_revenue * 30
    monthly_royalty = daily_royalty * 30
    yearly_royalty = monthly_royalty * 12
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-box"><div style="text-align: center;"><p style="color: #0099ff; margin: 0;">Daily Royalty</p><h3 style="margin: 0; font-size: 2em;">${daily_royalty:.2f}</h3></div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-box"><div style="text-align: center;"><p style="color: #0099ff; margin: 0;">Monthly Royalty</p><h3 style="margin: 0; font-size: 2em;">${monthly_royalty:.2f}</h3></div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-box"><div style="text-align: center;"><p style="color: #0099ff; margin: 0;">Yearly Royalty</p><h3 style="margin: 0; font-size: 2em;">${yearly_royalty:.2f}</h3></div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-box"><div style="text-align: center;"><p style="color: #0099ff; margin: 0;">5-Year Total</p><h3 style="margin: 0; font-size: 2em;">${yearly_royalty * 5:.2f}</h3></div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    months = list(range(1, 61))
    cumulative = [monthly_royalty * m for m in months]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=months, y=cumulative, mode='lines+markers', name='Cumulative Earnings', line=dict(color='#00d9ff', width=3), marker=dict(size=4), fill='tozeroy', fillcolor='rgba(0, 217, 255, 0.2)'))
    fig.update_layout(title="5-Year Earnings Projection", xaxis_title="Months", yaxis_title="Cumulative Royalties ($)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#00d9ff'), hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)

# ===== FOOTER =====
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #0099ff; font-size: 0.9em; margin-top: 2rem;">
    <p>🏛️ <strong>TRON ENTERPRISE</strong> | Autonomous Compute Network</p>
    <p>Earn 15% on idle GPU capacity with zero setup friction • Monthly Payouts • Smart Contract Settlement</p>
    <p style="margin-top: 1rem; color: #00d9ff;">v1.0 BETA | Enterprise Dashboard</p>
</div>
""", unsafe_allow_html=True)
'''

# Write the file
with open('dashboard/app.py', 'w', encoding='utf-8') as f:
    f.write(dashboard_code)

print("✅ Dashboard file written successfully")
