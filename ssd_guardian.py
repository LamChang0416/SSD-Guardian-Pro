import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
import subprocess
import json
import platform  # 用於偵測作業系統

# --- 頁面設定 ---
st.set_page_config(page_title="SSD Guardian Pro | Reliability Engineering", layout="wide")

# --- 1. 具備環境覺知的硬體偵測函式 ---
def get_physical_disks():
    current_os = platform.system() # 偵測當前作業系統
    
    # 情況 A：在 Windows 本地執行
    if current_os == "Windows":
        try:
            # 透過 PowerShell 抓取實體磁碟資訊
            cmd = "Get-PhysicalDisk | Select-Object DeviceId, FriendlyName, MediaType, Size | ConvertTo-Json"
            result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, timeout=5)
            
            if result.stdout.strip():
                disks = json.loads(result.stdout)
                return [disks] if isinstance(disks, dict) else disks
        except Exception:
            pass # 若 Windows 指令失敗則進入模擬模式

    # 情況 B：在 Streamlit Cloud (Linux) 或指令失敗時，提供專業 Demo 數據
    return [
        {"DeviceId": "V-01", "FriendlyName": "Enterprise SSD - Samsung PM9A3 (Demo)", "MediaType": "SSD"},
        {"DeviceId": "V-02", "FriendlyName": "Data Center SSD - Micron 7450 (Demo)", "MediaType": "SSD"},
        {"DeviceId": "V-03", "FriendlyName": "Cloud Storage - Intel P5510 (Demo)", "MediaType": "SSD"}
    ]

# --- 2. 模擬數據生成 (依據 DeviceID 確保趨勢一致) ---
def generate_wear_data(seed_id):
    # 使用 Hash 確保同一個硬碟名稱會產生固定的模擬數據
    seed = sum(ord(c) for c in str(seed_id))
    np.random.seed(seed)
    
    dates = pd.date_range(end=datetime.now(), periods=100)
    start_wear = np.random.uniform(10, 50)
    slope = np.random.uniform(0.08, 0.25)
    
    wear_data = start_wear + (np.arange(100) * slope) + np.random.normal(0, 0.4, 100)
    wear_data = np.clip(wear_data, 0, 100)
    return pd.DataFrame({'Date': dates, 'Wear_Level': wear_data})

# --- 側邊欄：裝置管理 ---
st.sidebar.title("🛡️ 裝置控制面板")
disk_list = get_physical_disks()

# 建立選單
options_map = {f"{d['FriendlyName']} (ID: {d['DeviceId']})": d['DeviceId'] for d in disk_list}
selected_label = st.sidebar.selectbox("請選擇監控對象", list(options_map.keys()))
target_id = options_map[selected_label]

if "Demo" in selected_label or platform.system() != "Windows":
    st.sidebar.info("☁️ 目前運行於展示模式 (Demo Mode)")
else:
    st.sidebar.success("💻 已連線至本地實體硬體")

st.sidebar.divider()
warn_val = st.sidebar.slider("警告門檻 (%)", 50, 80, 70)
crit_val = st.sidebar.slider("危險門檻 (%)", 81, 100, 90)

# --- 主畫面佈局 ---
st.title("SSD 預測性維護儀表板")
st.markdown(f"**當前監控裝置：** `{selected_label}`")

# 獲取並處理數據
df = generate_wear_data(target_id)
df['Days_Passed'] = (df['Date'] - df['Date'].min()).dt.days
X = df[['Days_Passed']].values
y = df['Wear_Level'].values

# 機器學習預測
model = LinearRegression()
model.fit(X, y)

slope = model.coef_[0]
intercept = model.intercept_
current_wear = y[-1]

# 預測 EOL
days_to_eol = (100 - intercept) / slope
eol_date = df['Date'].min() + timedelta(days=int(days_to_eol))
days_remaining = (eol_date - datetime.now()).days

# --- 視覺化 KPI ---
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("當前磨損率", f"{current_wear:.2f} %", delta=f"{slope:.4f} %/天", delta_color="inverse")
with m2:
    if current_wear >= crit_val:
        st.error("狀態：危險 (Critical)")
    elif current_wear >= warn_val:
        st.warning("狀態：警告 (Warning)")
    else:
        st.success("狀態：健康 (Healthy)")
with m3:
    st.metric("預計失效日期", eol_date.strftime('%Y-%m-%d'), f"剩餘 {max(0, days_remaining)} 天")

# --- 趨勢圖表 ---
predict_days = np.linspace(0, days_to_eol, 200).reshape(-1, 1)
predict_wear = model.predict(predict_days)
predict_dates = [df['Date'].min() + timedelta(days=int(d)) for d in predict_days.flatten()]

fig = go.Figure()
fig.add_trace(go.Scatter(x=df['Date'], y=df['Wear_Level'], mode='markers', name='觀測數據'))
fig.add_trace(go.Scatter(x=predict_dates, y=predict_wear, mode='lines', name='AI 預測趨勢', line=dict(dash='dash', color='red')))
fig.add_hline(y=100, line_dash="dot", line_color="black", annotation_text="EOL (100%)")
fig.update_layout(height=450, xaxis_title="日期", yaxis_title="磨損度 (%)", template="plotly_white")
st.plotly_chart(fig, use_container_width=True)

# --- RE 專業分析報告 ---
with st.expander("📋 可靠度工程分析簡報"):
    st.write(f"""
    **分析結論：**
    1. 該裝置平均磨損速率為每日 **{slope:.4f}%**，處於線性損耗階段。
    2. 基於線性回歸模型 $y = {slope:.4f}x + {intercept:.2f}$，預測組件將於 **{days_remaining}** 天後達到壽命終點。
    3. **建議**：建議於磨損率達到 {warn_val}% 前完成數據遷移或備品更換。
    """)

st.caption("Developed by Lam | Reliability Engineering Suite v1.0")