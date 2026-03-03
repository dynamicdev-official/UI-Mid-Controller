import streamlit as st
import requests
import pandas as pd
import base64
from PIL import Image
import io
from datetime import datetime
import time
import os

# --- CONFIGURATION ---
# อ่าน Webhook URLs จาก Environment Variables (ตั้งใน .env หรือ docker-compose.yml)
# ไม่มีการ hardcode URL ใดๆ ในโค้ดนี้ → ปลอดภัยกว่า
WEBHOOK_URL    = os.getenv("WEBHOOK_URL", "")       # Webhook หลัก (ตั้งเองใน .env)
CHAT_WEBHOOK   = os.getenv("CHAT_WEBHOOK", "")      # Webhook สำหรับ AI Chat
MONITOR_WEBHOOK = os.getenv("MONITOR_WEBHOOK", "")  # Webhook ตรวจสอบสถานะ

st.set_page_config(
    page_title="dynamicdev_ Command Center",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (CYBERPUNK THEME) ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
        color: #ffffff;
    }
    
    /* Animated Background Grid */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(0, 255, 136, 0.03) 2px,
            rgba(0, 255, 136, 0.03) 4px
        );
        pointer-events: none;
        z-index: 0;
        opacity: 0.3;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: rgba(10, 14, 39, 0.95);
        border-right: 1px solid rgba(0, 255, 136, 0.2);
        backdrop-filter: blur(10px);
    }
    
    /* Headers */
    h1, h2, h3 {
        background: linear-gradient(90deg, #00ff88, #00d4ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    /* Metric Cards */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        background: linear-gradient(90deg, #00ff88, #00d4ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Status Cards */
    .status-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        border-left: 5px solid #00ff88;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 255, 136, 0.1);
        transition: all 0.3s ease;
    }
    
    .status-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0, 255, 136, 0.2);
    }
    
    .status-card.blue {
        border-left-color: #00d4ff;
    }
    
    .status-card.purple {
        border-left-color: #b624ff;
    }
    
    .status-card.orange {
        border-left-color: #ff6b35;
    }
    
    /* Buttons */
    .stButton>button {
        background: rgba(0, 255, 136, 0.1);
        color: #00ff88;
        border: 1px solid #00ff88;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0);
    }
    
    .stButton>button:hover {
        background: rgba(0, 255, 136, 0.2);
        box-shadow: 0 0 30px rgba(0, 255, 136, 0.4);
        transform: translateY(-2px);
    }
    
    /* Chat Messages */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        backdrop-filter: blur(10px);
    }
    
    .stChatMessage[data-testid="chat-message-user"] {
        background: rgba(0, 255, 136, 0.1);
        border-color: #00ff88;
    }
    
    /* Input Fields */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        color: #ffffff;
    }
    
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: #00ff88;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
    }
    
    /* Dataframe */
    .stDataFrame {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 12px 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #ffffff;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(0, 255, 136, 0.2);
        border-color: #00ff88;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
    }
    
    /* File Uploader */
    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.05);
        border: 2px dashed rgba(0, 255, 136, 0.3);
        border-radius: 10px;
        padding: 20px;
    }
    
    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #00ff88, #00d4ff);
    }
    
    /* Divider */
    hr {
        border-color: rgba(0, 255, 136, 0.2);
    }
    
    /* Glow Effect for Important Elements */
    .glow {
        animation: glow 2s ease-in-out infinite;
    }
    
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 20px rgba(0, 255, 136, 0.2); }
        50% { box-shadow: 0 0 40px rgba(0, 255, 136, 0.4); }
    }
    
    /* Status Dot Animation */
    .status-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #00ff88;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
    }
    
    ::-webkit-scrollbar-thumb {
        background: #00ff88;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #00d4ff;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR CONTROL CENTER ---
with st.sidebar:
    st.image("dynamicdev.png", width=120)
    
    st.markdown("### 🔐 System-Command Center")
    st.markdown("---")
    
    # แสดง Webhook URL ที่กำหนดไว้ (ถ้ามี)
    if WEBHOOK_URL or CHAT_WEBHOOK:
        st.markdown("""
        <div style="background: rgba(0, 255, 136, 0.1); padding: 10px; border-radius: 8px; border: 1px solid #00ff88; margin-bottom: 10px;">
            <div style="color: #00ff88; font-weight: 600; font-size: 12px;">✅ Webhook Configured</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(255, 107, 53, 0.1); padding: 10px; border-radius: 8px; border: 1px solid #ff6b35; margin-bottom: 10px;">
            <div style="color: #ff6b35; font-weight: 600; font-size: 12px;">⚠️ กรุณาตั้งค่า Webhook URL ใน .env</div>
        </div>
        """, unsafe_allow_html=True)
    
    # System Status Indicator
    st.markdown("""
    <div style="background: rgba(0, 255, 136, 0.1); padding: 15px; border-radius: 10px; border: 1px solid #00ff88;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span class="status-dot"></span>
            <span style="color: #00ff88; font-weight: 600;">System Online</span>
        </div>
        <div style="color: #b4b4b4; font-size: 12px; margin-top: 5px;">
            Last update: {}</div>
    </div>
    """.format(datetime.now().strftime("%H:%M:%S")), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick Action Buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Restart", use_container_width=True):
            with st.spinner("Restarting AI Engine..."):
                try:
                    # เรียก Webhook restart จาก env var
                    if MONITOR_WEBHOOK:
                        requests.post(f"{MONITOR_WEBHOOK.rstrip('/')}/restart-agent", timeout=5)
                        st.success("✅ Restarted!")
                    else:
                        st.warning("⚠️ MONITOR_WEBHOOK ยังไม่ได้ตั้งค่า")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    with col2:
        if st.button("🧹 Clear", use_container_width=True):
            st.session_state.messages = []
            st.success("✅ Memory Cleared!")
            time.sleep(0.5)
            st.rerun()
    
    st.markdown("---")
    
    # System Info
    st.markdown("### 📊 System Info")
    st.markdown(f"""
    <div style="font-size: 12px; color: #b4b4b4;">
        <div>🖥️ <b>Host:</b> agent.dynamicdev.exemple</div>
        <div>🌐 <b>Network:</b> cloudflare-Tunnel</div>
        <div>🐳 <b>Containers:</b> 10 Running</div>
        <div>⏰ <b>Uptime:</b> 5M 24h 15m</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Footer
    st.markdown("""
    <div style="text-align: center; color: #6b6b6b; font-size: 11px; margin-top: 30px;">
        ui-mid-controller v1.0<br>
        Powered by Python &amp; Streamlit
    </div>
    """, unsafe_allow_html=True)

# --- MAIN CONTENT ---
st.markdown("# 🔐 dynamicdev_ Command Center")
st.markdown("**Real-time System Monitoring & AI Control**")
st.markdown("---")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard Monitor", "🤖 AI Agent Chat", "🐳 Docker Control"])

# ================== TAB 1: DASHBOARD ==================
with tab1:
    st.markdown("## 🖥️ PC Real-time Monitoring")
    
    # Top Stats Cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="status-card">
            <div style="font-size: 12px; color: #b4b4b4; text-transform: uppercase; margin-bottom: 10px;">Cloudflare Tunnel</div>
            <div style="font-size: 32px; font-weight: bold; margin-bottom: 5px;">
                <span class="status-dot"></span>Online
            </div>
            <div style="color: #00ff88; font-size: 14px;">Target: agent.dynamicdev.example</div>
            <div style="background: rgba(0, 255, 136, 0.2); color: #00ff88; padding: 5px 12px; border-radius: 15px; display: inline-block; margin-top: 10px; font-size: 12px;">
                ✓ Stable
            </div>
            <div style="background: rgba(0, 212, 255, 0.2); color: #00d4ff; padding: 5px 12px; border-radius: 15px; display: inline-block; margin-top: 10px; font-size: 12px;">
                ▶ Tunnel Connected
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="status-card blue">
            <div style="font-size: 12px; color: #b4b4b4; text-transform: uppercase; margin-bottom: 10px;">Docker Status</div>
            <div style="font-size: 32px; font-weight: bold; margin-bottom: 5px;">21 Containers</div>
            <div style="color: #00d4ff; font-size: 14px;">n8n, Qdrant, DB,</div>
            <div style="background: rgba(0, 212, 255, 0.2); color: #00d4ff; padding: 5px 12px; border-radius: 15px; display: inline-block; margin-top: 10px; font-size: 12px;">
                ▶ Running
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="status-card orange">
            <div style="font-size: 12px; color: #b4b4b4; text-transform: uppercase; margin-bottom: 10px;">WireGuard VPN</div>
            <div style="font-size: 32px; font-weight: bold; margin-bottom: 5px;">Connected</div>
            <div style="color: #ff6b35; font-size: 14px;">Clients: 3 Devices</div>
            <div style="background: rgba(255, 107, 53, 0.2); color: #ff6b35; padding: 5px 12px; border-radius: 15px; display: inline-block; margin-top: 10px; font-size: 12px;">
                ⚡ Active
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Docker Container List
    st.markdown("### 🐳 Docker Container List")
    
    # Simulate real-time data (ในการใช้งานจริง ดึงจาก Webhook API)
    docker_data = pd.DataFrame([
        {"Container": "n8n-lastest", "Status": "Up 2h", "CPU": "1.2%", "Memory": "256MB", "Ports": "XXXX:5678"},
        {"Container": "agent-memory", "Status": "Up 5h", "CPU": "0.5%", "Memory": "128MB", "Ports": "XXXX:6333"},
        {"Container": "postgres-db", "Status": "Up 1d", "CPU": "0.8%", "Memory": "384MB", "Ports": "XXXX:5432"},
        {"Container": "redis-cache", "Status": "Up 1d", "CPU": "0.3%", "Memory": "64MB", "Ports": "XXXX:6379"}
    ])
    
    st.dataframe(
        docker_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Container": st.column_config.TextColumn("🐳 Container", width="medium"),
            "Status": st.column_config.TextColumn("📊 Status", width="small"),
            "CPU": st.column_config.TextColumn("⚡ CPU", width="small"),
            "Memory": st.column_config.TextColumn("💾 Memory", width="small"),
            "Ports": st.column_config.TextColumn("🔌 Ports", width="medium")
        }
    )
    
    # Real-time System Metrics
    st.markdown("---")
    st.markdown("### 📈 System Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Operating System", "linux", delta="SKA4G02", delta_color="inverse")
        
    with col2:
        st.metric("CPU Usage", "24.5%", delta="-2.3%", delta_color="inverse")

    with col3:
        st.metric("Memory", "11.2GB", delta="Available")
    
    with col4:
        st.metric("Network In", "1.7Gb/s", delta="+15 MB/s")
    
    with col5:
        st.metric("Network Out", "982Mb/s", delta="-5 MB/s", delta_color="inverse")

# ================== TAB 2: AI CHAT (Webhook Controller) ==================
with tab2:
    st.markdown("## 💬 AI Agent Command Interface")
    
    # แสดง Webhook URL ปัจจุบัน (ถ้า set แล้ว)
    if CHAT_WEBHOOK:
        st.success(f"✅ Chat Webhook: `{CHAT_WEBHOOK}`")
    else:
        st.warning("⚠️ กรุณาตั้งค่า `CHAT_WEBHOOK` ใน .env หรือ docker-compose.yml")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
                st.markdown(message["content"])
                
                # Display image if exists
                if "file" in message and message["file"]:
                    st.image(message["file"], width=400)
                
                # Timestamp
                if "timestamp" in message:
                    st.caption(f"🕐 {message['timestamp']}")
    
    # File uploader
    st.markdown("---")
    uploaded_file = st.file_uploader(
        "📎 Attach file for AI analysis",
        type=['png', 'jpg', 'jpeg', 'csv', 'txt', 'pdf'],
        help="Upload images, documents, or data files"
    )
    
    if uploaded_file:
        st.info(f"📄 File attached: **{uploaded_file.name}** ({uploaded_file.size} bytes)")
    
    # Chat input — ส่งไปยัง Webhook ที่กำหนดใน .env
    if prompt := st.chat_input("💭 Type your command or question..."):
        # กัน error ถ้ายังไม่ได้ตั้งค่า Webhook
        if not CHAT_WEBHOOK:
            st.error("❌ CHAT_WEBHOOK ยังไม่ได้ตั้งค่า กรุณาเพิ่มใน .env หรือ docker-compose.yml")
            st.stop()
        
        # Add user message
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": timestamp
        })
        
        # Display user message
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
            st.caption(f"🕐 {timestamp}")
        
        # Prepare payload
        payload = {
            "chatInput": prompt,
            "sessionId": "dynamicdev_root"
        }
        
        # Add file data if uploaded
        if uploaded_file:
            file_bytes = uploaded_file.read()
            payload["file_data"] = base64.b64encode(file_bytes).decode()
            payload["file_name"] = uploaded_file.name
            payload["file_type"] = uploaded_file.type
        
        # ส่งไปยัง CHAT_WEBHOOK (อ่านจาก env var)
        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()
            
            # Show typing indicator
            message_placeholder.markdown("🤔 *AI is thinking...*")
            
            try:
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "dynamicdev-Streamlit/1.0"
                }
                
                response = requests.post(
                    CHAT_WEBHOOK,
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result.get("output", "No response from AI")
                    
                    # Display AI response
                    message_placeholder.markdown(ai_response)
                    
                    # Add to chat history
                    ai_message = {
                        "role": "assistant",
                        "content": ai_response,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    }
                    
                    # Check if AI returned an image
                    if "ai_file" in result:
                        ai_message["file"] = result["ai_file"]
                        st.image(result["ai_file"], width=400)
                    
                    st.session_state.messages.append(ai_message)
                    st.caption(f"🕐 {ai_message['timestamp']}")
                    
                else:
                    error_msg = f"❌ Error {response.status_code}: {response.text}"
                    message_placeholder.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
            
            except requests.exceptions.Timeout:
                error_msg = "⏱️ Request timeout! Webhook didn't respond in 30 seconds."
                message_placeholder.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
            
            except Exception as e:
                error_msg = f"💥 Error: {str(e)}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })

# ================== TAB 3: DOCKER CONTROL ==================
with tab3:
    st.markdown("## 🐳 Docker Container Control")
    st.info("🔧 Advanced Docker management interface (Coming Soon)")
    
    st.markdown("### Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Restart All", use_container_width=True):
            st.warning("Restarting all containers...")
    
    with col2:
        if st.button("⏸️ Stop All", use_container_width=True):
            st.warning("Stopping all containers...")
    
    with col3:
        if st.button("▶️ Start All", use_container_width=True):
            st.success("Starting all containers...")
    
    with col4:
        if st.button("📊 View Logs", use_container_width=True):
            st.info("Opening logs viewer...")
    
    st.markdown("---")
    
    # Container details (expandable)
    for container in ["n8n-master", "agent-memory", "postgres-db", "redis-cache"]:
        with st.expander(f"🐳 {container}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Status:** Running")
                st.markdown("**Image:** latest")
                st.markdown("**Created:** 2 days ago")
            
            with col2:
                if st.button(f"⏸️ Stop", key=f"stop_{container}"):
                    st.warning(f"Stopping {container}...")
                
                if st.button(f"🔄 Restart", key=f"restart_{container}"):
                    st.info(f"Restarting {container}...")
                
                if st.button(f"📋 Logs", key=f"logs_{container}"):
                    st.code("Container logs will appear here...", language="log")

# --- AUTO REFRESH (Optional) ---
# Uncomment to enable auto-refresh every 5 seconds
# time.sleep(5)
# st.rerun()
