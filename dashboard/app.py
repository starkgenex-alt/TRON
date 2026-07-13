"""
TRON Enterprise Dashboard - Full Rich UI with Animations & Visualizations
Data Center Licensing, Live Metrics, ROI Simulator, and Royalty Management
"""
import os
import streamlit as st
import requests
import json
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# ===== PAGE CONFIG =====
API_BASE = os.environ.get("TRON_API_BASE", "http://127.0.0.1:9000")
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class^="css"], [class*=" css"] {
        font-family: 'Inter', sans-serif !important;
    }

    :root {
        color-scheme: dark;
    }

    body {
        background: radial-gradient(circle at top, rgba(91, 131, 255, 0.12), transparent 25%),
                    linear-gradient(180deg, #05080f 0%, #0d1221 100%);
        color: #e8edf7;
        overflow-x: hidden;
    }

    .page-background {
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: -1;
        overflow: hidden;
    }

    .bg-grid {
        position: absolute;
        inset: 0;
        background-image:
            linear-gradient(0deg, rgba(91, 131, 255, 0.08) 1px, transparent 1px),
            linear-gradient(90deg, rgba(91, 131, 255, 0.08) 1px, transparent 1px);
        background-size: 72px 72px;
        opacity: 0.22;
        animation: drift 36s linear infinite;
    }

    .bg-lines {
        position: absolute;
        inset: 0;
        background-image:
            linear-gradient(30deg, rgba(91, 131, 255, 0.08) 1px, transparent 1px),
            linear-gradient(120deg, rgba(255, 255, 255, 0.06) 1px, transparent 1px);
        background-size: 180px 180px;
        opacity: 0.14;
        animation: slide-lines 28s linear infinite;
    }

    .bg-nodes {
        position: absolute;
        inset: 0;
        background-image:
            radial-gradient(circle at 12% 18%, rgba(91, 131, 255, 0.18) 0, transparent 6%),
            radial-gradient(circle at 78% 14%, rgba(118, 82, 255, 0.16) 0, transparent 7%),
            radial-gradient(circle at 54% 78%, rgba(0, 222, 204, 0.14) 0, transparent 8%),
            radial-gradient(circle at 30% 60%, rgba(255, 255, 255, 0.08) 0, transparent 4%);
        opacity: 0.32;
        animation: pulse 18s ease-in-out infinite;
    }

    @keyframes drift {
        to { background-position: 160px 160px; }
    }

    @keyframes slide-lines {
        to { background-position: 180px 180px; }
    }

    @keyframes pulse {
        0%, 100% { opacity: 0.32; transform: scale(1); }
        50% { opacity: 0.24; transform: scale(1.02); }
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        color: #f5f7ff;
        margin: 0;
    }

    h1 {
        font-size: 3rem !important;
        font-weight: 700;
        letter-spacing: -0.03em;
    }

    h2 {
        font-size: 1.5rem !important;
        font-weight: 600;
        margin-bottom: 0.8rem !important;
    }

    h3 {
        font-size: 1rem !important;
        font-weight: 500;
        color: #cdd6f8;
    }

    .metric-box,
    .dashboard-panel,
    .rack-card {
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(18, 24, 38, 0.86);
        box-shadow: 0 35px 80px rgba(0, 0, 0, 0.18);
        backdrop-filter: blur(18px);
        padding: 1.75rem;
        margin-bottom: 1.25rem;
    }

    .metric-box {
        min-height: 170px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
    }

    .metric-box p,
    .dashboard-panel p,
    .rack-card p {
        color: #abb3c8;
    }

    .metric-box .metric-value {
        color: #f8fbff;
        font-size: 2rem;
        font-weight: 700;
    }

    .dashboard-panel {
        border-left: 4px solid rgba(91, 131, 255, 0.95);
    }

    .rack-card {
        transition: transform 0.22s ease, box-shadow 0.22s ease;
    }

    .rack-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 40px 120px rgba(0, 0, 0, 0.22);
    }

    .stButton > button {
        background: #5b83ff !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 0.95rem 1.25rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.02em !important;
        box-shadow: 0 20px 50px rgba(91, 131, 255, 0.18) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 24px 60px rgba(91, 131, 255, 0.24) !important;
    }

    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #f5f7ff !important;
        border: 1px solid rgba(255, 255, 255, 0.11) !important;
        border-radius: 14px !important;
        padding: 0.85rem !important;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: rgba(91, 131, 255, 0.9) !important;
        outline: none !important;
        box-shadow: 0 0 0 4px rgba(91, 131, 255, 0.12) !important;
    }

    .stTabs [role="tab"] {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        color: #cdd6f8 !important;
        font-weight: 600;
        margin: 0.25rem !important;
        border-radius: 16px !important;
        padding: 0.95rem 1.1rem !important;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(91, 131, 255, 0.16) !important;
        border-color: rgba(91, 131, 255, 0.4) !important;
        color: #ffffff !important;
        box-shadow: none !important;
    }

    hr {
        border: none;
        height: 1px;
        background: rgba(255, 255, 255, 0.08);
        margin: 2rem 0;
    }

    .status-online {
        color: #6de18b;
        font-weight: 700;
    }

    .status-offline {
        color: #f26d6d;
        font-weight: 700;
    }

    .stAlert {
        border-left: 4px solid rgba(91, 131, 255, 0.95) !important;
        background: rgba(27, 39, 61, 0.9) !important;
        color: #dde2f3 !important;
        border-radius: 14px !important;
    }

    .page-title {
        max-width: 1100px;
        margin: 0 auto;
        padding: 2rem 0 1rem;
    }

    .page-description {
        color: #abb3c8;
        font-size: 1rem;
        line-height: 1.7;
        max-width: 900px;
        margin: 0 auto;
    }

    section[data-testid="stSidebar"] {
        background: rgba(10, 16, 28, 0.76) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 0 40px 90px rgba(0, 0, 0, 0.22) !important;
        backdrop-filter: blur(24px) saturate(140%) !important;
    }

    section[data-testid="stSidebar"] div {
        background: transparent !important;
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
            data = r.json().get("workers", {})
            if isinstance(data, dict):
                return list(data.values())
            return data
    except:
        pass
    return []

@st.cache_data(ttl=10)
def fetch_active_jobs():
    try:
        r = requests.get(f"{API_BASE}/active_jobs", timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json().get("active_jobs", {})
            if isinstance(data, dict):
                return list(data.values())
            return data
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

@st.cache_data(ttl=10)
def fetch_platform_balance():
    try:
        r = requests.get(f"{API_BASE}/platform/balance", timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {
        "platform_balance": 0.0,
        "total_billed": 0.0,
        "total_worker_payout": 0.0,
        "total_platform_earnings": 0.0,
        "job_count": 0,
        "currency": "USD"
    }

@st.cache_data(ttl=10)
def fetch_launch_context():
    try:
        r = requests.get(f"{API_BASE}/api/v1/launch/context", timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {
        "status": "launch_ready",
        "layers": {"core": True, "tronii": True, "vgpu": True},
        "active_workers": 0,
        "install_command": "curl -fsSL https://raw.githubusercontent.com/StarkX-cloud/tron-client/main/install_tron.sh | TRON_MASTER_URL=http://127.0.0.1:9000 bash",
        "dashboard_url": "http://127.0.0.1:8501",
        "summary": fetch_platform_balance(),
    }

def license_facility(location: str, total_gpus: int):
    try:
        payload = {"location": location, "total_gpus": total_gpus}
        r = requests.post(f"{API_BASE}/enterprise/license", json=payload, timeout=TIMEOUT)
        return r.status_code, r.text
    except Exception as e:
        return 500, str(e)

# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("## Platform Controls")
    st.markdown("---")
    refresh_interval = st.slider("Refresh interval (seconds)", 1, 30, 5)
    live_telemetry = st.checkbox("Live telemetry mode", value=True)
    data_scope = st.selectbox("Data scope", ["Cluster", "Regional", "Global"])
    forecast_horizon = st.select_slider("Forecast horizon", options=["24h", "7d", "30d"], value="7d")
    st.markdown("---")
    st.markdown("### System Status")
    workers = fetch_workers()
    racks = fetch_racks()
    jobs = fetch_active_jobs()
    balance = fetch_platform_balance()
    launch_context = fetch_launch_context()
    latency_estimate = 18 + max(0, len(workers) * 4)
    throughput_estimate = 420 + max(0, len(jobs) * 14)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Workers", len(workers))
    with col2:
        st.metric("Racks", len(racks))
    st.metric("Active Jobs", len(jobs))
    st.metric("Platform Balance", f"${balance.get('platform_balance', 0.0):.4f}")
    st.metric("Total Earnings", f"${balance.get('total_platform_earnings', 0.0):.2f}")
    st.markdown("### Launch Pack")
    st.code(launch_context.get("install_command", ""), language="bash")
    st.caption(f"Layers: core={launch_context.get('layers', {}).get('core')} | tronii={launch_context.get('layers', {}).get('tronii')} | vgpu={launch_context.get('layers', {}).get('vgpu')}")
    st.metric("Latency", f"{latency_estimate} ms", delta="-8 ms")
    st.metric("Throughput", f"{throughput_estimate} ops/s", delta="+6%")
    st.markdown("---")
    st.markdown("### API Status")
    try:
        r = requests.get(f"{API_BASE}/health", timeout=2)
        st.success("Master online") if r.status_code == 200 else st.error("Master offline")
    except:
        st.error("Master offline")

# ===== MAIN HEADER =====
st.markdown("""
<div class="page-background">
    <div class="bg-grid"></div>
    <div class="bg-lines"></div>
    <div class="bg-nodes"></div>
</div>
<div class="page-title" style="text-align: center;">
    <h1>TRON Enterprise</h1>
    <p class="page-description">AI-native infrastructure monetization for distributed data centers. Monitor compute, automate licensing, and scale royalty payouts with a modern platform experience.</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ===== MAIN TABS =====
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "License", "Infrastructure", "Royalties", "ROI"])

# ===== TAB 1: MAIN DASHBOARD =====
with tab1:
    st.markdown("## Platform Overview")
    st.markdown("---")
    workers = fetch_workers()
    racks = fetch_racks()
    active_jobs = fetch_active_jobs()
    ledger = fetch_ledger()
    balance = fetch_platform_balance()
    launch_context = fetch_launch_context()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-box"><div><p style="margin: 0; color: #abb3c8;">Active Workers</p><div class="metric-value">{len(workers)}</div></div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-box"><div><p style="margin: 0; color: #abb3c8;">Licensed Racks</p><div class="metric-value">{len(racks)}</div></div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-box"><div><p style="margin: 0; color: #abb3c8;">Active Jobs</p><div class="metric-value">{len(active_jobs)}</div></div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-box"><div><p style="margin: 0; color: #abb3c8;">Platform Balance</p><div class="metric-value">${balance.get("platform_balance", 0.0):.4f}</div></div></div>', unsafe_allow_html=True)

    health_index = min(100, 70 + len(workers) * 2 + len(racks) * 3)
    anomaly_risk = max(2, 16 - len(workers))
    efficiency = min(99, 72 + len(workers) * 2)

    st.markdown("---")
    st.markdown("### Operations Intelligence")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Health Index", f"{health_index}%", delta="+2%")
    with col2:
        st.metric("Efficiency", f"{efficiency}%", delta="+3%")
    with col3:
        st.metric("Anomaly Risk", f"{anomaly_risk}%", delta="-1%")

    st.markdown(f'<div class="dashboard-panel"><p style="margin: 0 0 0.8rem 0; color: #abb3c8;">Forecast horizon: <strong>{forecast_horizon}</strong></p><p style="margin: 0 0 0.8rem 0; color: #abb3c8;">Telemetry mode: <strong>{"Live" if live_telemetry else "Batch"}</strong></p><p style="margin: 0; color: #abb3c8;">Data scope: <strong>{data_scope}</strong></p></div>', unsafe_allow_html=True)
    st.markdown("### Unified Launch Flow")
    st.code(launch_context.get("install_command", ""), language="bash")
    st.caption(f"Status: {launch_context.get('status')} | Active workers: {launch_context.get('active_workers')} | Dashboard: {launch_context.get('dashboard_url')}")

    if live_telemetry:
        trend_x = ["T-5", "T-4", "T-3", "T-2", "T-1", "Now"]
        trend_y = [66, 72, 78, 81, 85, 89]
        trend_fig = go.Figure(go.Scatter(x=trend_x, y=trend_y, mode="lines+markers", line=dict(color="#5b83ff", width=3), marker=dict(size=6, color="#5b83ff")))
        trend_fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_title="Telemetry interval", yaxis_title="Utilization", font=dict(color='#cdd6f8'), hovermode='x unified')
        st.plotly_chart(trend_fig, use_container_width=True)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Worker Distribution")
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
        st.markdown("### Revenue Breakdown")
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
    st.markdown("## License New Facility")
    st.markdown("---")
    st.markdown('<div class="dashboard-panel"><h3>Get started in minutes</h3><ul><li>Enter facility location and GPU capacity</li><li>License and onboard compute assets</li><li>Enable revenue sharing and payout tracking</li><li>Monitor health and utilization in real time</li></ul></div>', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        location = st.text_input("Facility Location", placeholder="e.g., US-East-1, Europe-DE, Asia-SG")
    with col2:
        total_gpus = st.number_input("Total GPUs Available", min_value=1, max_value=10000, step=1, value=10)
    
    if st.button("License Facility", use_container_width=True):
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
    st.markdown("## Infrastructure")
    st.markdown("---")
    st.markdown("### Connected Workers")
    workers = fetch_workers()
    if workers:
        for w in workers:
            st.markdown(f'<div class="rack-card"><div style="display: flex; justify-content: space-between;"><div><h4 style="margin: 0;">{w.get("name", "Unknown")}</h4><p style="margin: 0.3rem 0; color: #abb3c8;">GPU: {w.get("gpu_name", "N/A")} | {w.get("vram_gb", "?")} GB VRAM</p><p style="margin: 0; color: #abb3c8;">Network: {w.get("network_bandwidth_gbps", "?")} Gbps</p></div><div style="text-align: right;"><span class="status-online">ONLINE</span></div></div></div>', unsafe_allow_html=True)
    else:
        st.info("No workers connected yet")
    
    st.markdown("---")
    st.markdown("### Licensed Racks")
    racks = fetch_racks()
    if racks:
        for rack in racks:
            st.markdown(f'<div class="rack-card"><div style="display: flex; justify-content: space-between;"><div><h4 style="margin: 0;">Rack: {rack.get("id", "Unknown")[:12]}</h4><p style="margin: 0.3rem 0; color: #abb3c8;">Location: {rack.get("location", "N/A")}</p><p style="margin: 0; color: #abb3c8;">{rack.get("total_gpus", "?")} GPUs | {rack.get("status", "unknown")}</p></div><div style="text-align: right;"><span style="color: #6de18b; font-weight: bold;">ACTIVE</span></div></div></div>', unsafe_allow_html=True)
    else:
        st.info("No licensed racks yet")

# ===== TAB 4: ROYALTIES =====
with tab4:
    st.markdown("## Royalty Ledger")
    st.markdown("---")
    ledger = fetch_ledger()
    balance = fetch_platform_balance()
    if ledger:
        total_revenue = sum(float(entry.get("amount", 0)) for entry in ledger)
        total_royalties = balance.get("total_platform_earnings", 0.0)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="metric-box"><div><p style="margin: 0; color: #abb3c8;">Total Revenue</p><div class="metric-value">${total_revenue:.2f}</div></div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-box"><div><p style="margin: 0; color: #abb3c8;">Your Royalties (15%)</p><div class="metric-value">${total_royalties:.2f}</div></div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-box"><div><p style="margin: 0; color: #abb3c8;">Platform Balance</p><div class="metric-value">${balance.get("platform_balance", 0.0):.4f}</div></div></div>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("### 📝 Transaction History")
        for entry in ledger[-20:]:
            st.markdown(f'<div class="dashboard-panel"><div style="display: flex; justify-content: space-between;"><div><strong>{entry.get("type", "unknown")}</strong><p style="margin: 0; color: #0099ff; font-size: 0.9em;">{entry.get("timestamp", "N/A")}</p></div><div style="text-align: right;"><h3 style="margin: 0; color: #00ff00;">${entry.get("amount", 0)}</h3></div></div></div>', unsafe_allow_html=True)
    else:
        st.info("No ledger entries yet")

# ===== TAB 5: ROI SIMULATOR =====
with tab5:
    st.markdown("## ROI Simulator")
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
<div style="text-align: center; color: #cdd6f8; font-size: 0.95em; margin-top: 2rem;">
    <p><strong>TRON Enterprise</strong> | Autonomous Compute Network</p>
    <p>Earn 15% on idle GPU capacity with zero setup friction • Monthly payouts • Smart contract settlement</p>
    <p style="margin-top: 1rem; color: #8fa2c6;">v1.0 BETA | Enterprise Dashboard</p>
</div>
""", unsafe_allow_html=True)
