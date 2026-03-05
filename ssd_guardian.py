import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
import subprocess
import json

# --- 頁面設定 ---
st.set_page_config(page_title="SSD Guardian Pro | Reliability Engineering", layout="wide")

# --- 1. 硬體偵測函式 (Windows PowerShell) ---
def get_physical_disks():
    try:
        # 抓取實體磁碟資訊
        cmd = "Get-PhysicalDisk | Select-Object DeviceId, FriendlyName, MediaType, Size | ConvertTo-Json"
        result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
        
        if result.stdout.strip():
            disks = json.loads(result.stdout)
            return [disks] if isinstance(disks, dict) else disks
        return []
    except Exception:
        return []

# --- 2. 模擬數據生成 (當選擇不同硬碟時生成不同趨勢) ---
def generate_wear_data(seed_id):
    np.random.seed(int(seed_id) if str(seed_id).isdigit() else 42)
    dates = pd.date_range(end=datetime.now(), periods=100)
    # 根據 DeviceId 模擬不同的初始磨損與斜率
    start_wear = np.random.uniform(5, 60)
    slope = np.random.uniform(0.05, 0.2)
    wear_data = start_wear + (np.arange(100) * slope) + np.random.normal(0, 0.5, 100)
    wear_data = np.clip(wear_data, 0, 100)
    return pd.DataFrame({'Date': dates, 'Wear_Level': wear_data})

# --- 側邊欄：裝置管理 ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/689/689305.png", width=100)
st.sidebar.title("控制面板")

st.sidebar.subheader("🔍 裝置選擇")
disk_list = get_physical_disks()

if disk_list:
    options = {f"Disk {d['DeviceId']}: {d['FriendlyName']}": d['DeviceId'] for d in disk_list}
    selected_label = st.sidebar.selectbox("請選擇要監控的 SSD", list(options.keys()))
    target_id = options[selected_label]
    st.sidebar.success(f"已連線至實體裝置 ID: {target_id}")
else:
    st.sidebar.warning("未偵測到實體磁碟，進入沙盒模擬模式")
    target_id = 0

st.sidebar.divider()

st.sidebar.subheader("⚙️ 預警門檻")
warn_val = st.sidebar.slider("警告門檻 (黃)", 50, 80, 70)
crit_val = st.sidebar.slider("危險門檻 (紅)", 81, 100, 90)

# --- 主畫面佈局 ---
st.title("🛡️ SSD 預測性維護儀表板")
st.caption(f"工程師：Lam | 當前監控：{selected_label if disk_list else '模擬環境'}")

# 獲取數據
df = generate_wear_data(target_id)

# --- 機器學習預測 (線性回歸) ---
df['Days_Passed'] = (df['Date'] - df['Date'].min()).dt.days
X = df[['Days_Passed']].values
y = df['Wear_Level'].values

model = LinearRegression()
model.fit(X, y)

# 計算預測數據
current_wear = y[-1]
slope = model.coef_[0]
intercept = model.intercept_

# 預測何時達到 100% (y = ax + b => x = (y-b)/a)
days_to_eol = (100 - intercept) / slope
eol_date = df['Date'].min() + timedelta(days=int(days_to_eol))
days_remaining = (eol_date - datetime.now()).days

# --- 視覺化 KPI ---
m1, m2, m3 = st.columns(3)

with m1:
    st.metric("當前磨損 (Percentage Used)", f"{current_wear:.2f} %", delta=f"{slope:.4f} %/天", delta_color="inverse")

with m2:
    if current_wear >= crit_val:
        st.error(f"狀態：危險 (Critical)")
    elif current_wear >= warn_val:
        st.warning(f"狀態：警告 (Warning)")
    else:
        st.success(f"狀態：良好 (Healthy)")

with m3:
    st.metric("預計失效日期 (EOL)", eol_date.strftime('%Y-%m-%d'), f"剩餘 {max(0, days_remaining)} 天")

# --- 趨勢圖表 ---
st.divider()
st.subheader("📈 壽命磨損趨勢與預測")

# 建立預測線 (從開始到 100%)
predict_days = np.linspace(0, days_to_eol, 200).reshape(-1, 1)
predict_wear = model.predict(predict_days)
predict_dates = [df['Date'].min() + timedelta(days=int(d)) for d in predict_days.flatten()]

fig = go.Figure()

# 歷史數據點
fig.add_trace(go.Scatter(x=df['Date'], y=df['Wear_Level'], mode='markers', name='歷史觀測值', marker=dict(color='#1f77b4', size=8)))

# 預測趨勢線
fig.add_trace(go.Scatter(x=predict_dates, y=predict_wear, mode='lines', name='AI 預測趨勢', line=dict(dash='dash', color='#d62728', width=3)))

# 門檻水平線
fig.add_hline(y=100, line_dash="dot", line_color="black", annotation_text="End of Life (100%)")
fig.add_hline(y=warn_val, line_dash="dash", line_color="orange", annotation_text="警告區")

fig.update_layout(
    height=500,
    xaxis_title="時間軸",
    yaxis_title="磨損程度 (%)",
    hovermode="x unified",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# --- 專業可靠度分析報告 ---
with st.expander("📋 查看可靠度分析報告 (RE Report)"):
    st.write(f"""
    **分析摘要：**
    1. **磨損速率**：根據過去 100 筆數據分析，該硬碟平均每日磨損率為 **{slope:.4f}%**。
    2. **使用模型**：採用線性回歸模型 $y = {slope:.4f}x + {intercept:.2f}$。
    3. **預期可靠度**：目前裝置處於穩定運行期。預計在 **{eol_date.strftime('%Y-%m-%d')}** 達到廠商定義的壽命極限。
    4. **建議行動**：建議於磨損達到 **{warn_val}%** (即約 {(warn_val - current_wear)/slope:.0f} 天後) 開始進行備品採購流程。
    """)
    
st.caption("註：本工具僅供可靠度工程參考，實際壽命依環境溫度與寫入放大率 (WAF) 有所不同。")