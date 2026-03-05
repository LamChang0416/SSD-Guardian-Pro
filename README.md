# 🛡️ SSD Guardian Pro: AI-Driven Reliability Forecasting

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📖 專案簡介
**SSD Guardian Pro** 是一款專為數據中心與企業級伺服器設計的**預測性維護 (Predictive Maintenance)** 視覺化工具。 

身為可靠度工程師 (RE)，我們深知硬碟故障對系統可用性的影響。本專案透過 Python 整合 Windows 底層硬體指令，並利用線性回歸模型分析 `Percentage Used` 指標，提供精確的硬碟壽命終點 (EOL) 預測，協助運維團隊在故障發生前完成備品採購與更換。



---

## 🚀 核心功能
* **多裝置自動偵測**：透過 PowerShell `Get-PhysicalDisk` 接口，動態識別系統內所有實體 SSD/HDD 裝置。
* **AI 壽命預測曲線**：利用 Scikit-learn 線性回歸演算法，計算每日平均磨損率並預估 EOL 日期。
* **動態預警系統**：可自定義健康度門檻（Warning/Critical），當磨損超標時介面會自動切換預警狀態。
* **專業可靠度報告**：自動生成包含磨損斜率（Slope）與剩餘壽命（Days Remaining）的分析摘要。

---

## 🛠️ 技術棧
* **語言**: Python 3.11
* **Web 框架**: Streamlit
* **數據科學**: Pandas, NumPy, Scikit-learn
* **圖表視覺化**: Plotly (動態互動式圖表)
* **系統介面**: Windows PowerShell API

---

## 🔬 可靠度分析模型
本系統採用線性退化模型來模擬 NAND Flash 的損耗情況：

$$y = \beta_1 x + \beta_0$$

其中：
* $y$: 預計磨損百分比 (Percentage Used)
* $\beta_1$: 每日平均磨損速率 (Daily Wear Rate)
* $x$: 觀測天數
* $\beta_0$: 初始狀態偏差

當 $y \ge 100$ 時，系統將判定該組件達到設計壽命極限。

---

## 💻 快速開始
1. **建立環境**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
