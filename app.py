import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# --- 設定 ---
# 1. スプレッドシートのURL（gidを確認済み）
SHEET_URL = "https://docs.google.com/spreadsheets/d/1Dl1toHnKeAkwD55h5zsrHLkvrp3ml0x8hS0IPMAEJos/edit?gid=1940633540#gid=1940633540"
# 2. ご提示いただいたGASのURL
GAS_URL = "https://script.google.com/macros/s/AKfycbxaahHoBJw_t74INs9_A7JNSwJaroK9M05HfMuDmCCaiD04gboAfZcA5e0CER3Gm8-rqg/exec"

def get_csv_url(url):
    try:
        sid = url.split("/d/")[1].split("/")[0]
        gid = url.split("gid=")[1].split("#")[0].split("&")[0] if "gid=" in url else "0"
        return f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}"
    except:
        return None

st.set_page_config(page_title="対話収録システム", layout="wide")

@st.cache_data(ttl=5)
def load_data():
    url = get_csv_url(SHEET_URL)
    if url:
        try:
            return pd.read_csv(url)
        except:
            return None
    return None

df = load_data()

if df is not None:
    st.title("🎙️ 対話収録システム")
    
    # サイドバー：収録対象の選択
    t_id = st.sidebar.selectbox("収録IDを選択", df['dialogue_id'].unique())
    scn = df[df['dialogue_id'] == t_id].reset_index(drop=True)
    
    # セッション管理（各IDの進行度を保持）
    sk = f'idx_{t_id}'
    if sk not in st.session_state:
        st.session_state[sk] = 0
    idx = st.session_state[sk]

    st.subheader(f"シナリオID: {t_id}")
    
    # --- シナリオ表示（USER:青 / SYSTEM:緑） ---
    for i, r in scn.iterrows():
        is_current = (i == idx)
        prefix = "👉" if is_current else "&nbsp;&nbsp;&nbsp;&nbsp;"
        
        # 色の設定
        color = "#1E90FF" if r['speaker'] == "USER" else "#2E8B57"
        speaker_label = f"<span style='color:{color}; font-weight:bold;'>[{r['speaker']}]</span>"
        
        if is_current:
            st.markdown(f"<div style='background-color: #f0f2f6; padding: 12px; border-radius: 8px; border-left: 5px solid {color};'>{prefix} {speaker_label} {r['utterance']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div>{prefix} {speaker_label} <span style='color: #666;'>{r['utterance']}</span></div>", unsafe_allow_html=True)

    st.divider()

    # --- 操作エリア ---
    if idx < len(scn):
        curr = scn.iloc[idx]
        st.markdown(f"### 次の発話担当: <span style='color:{('#1E90FF' if curr['speaker']=='USER' else '#2E8B57')};'>{curr['speaker']}</span>", unsafe_allow_html=True)
        
        col_u, col_s, col_back, col_reset = st.columns([1.2, 1.2, 0.6, 0.6])
        
        # タイムスタンプ送信共通関数
        def send_log(speaker_name):
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            payload = {
                "dialogue_id": str(t_id),
                "line_id": int(idx + 1),
                "speaker": speaker_name,
                "timestamp": now
            }
            try:
                response = requests.post(GAS_URL, json=payload, timeout=10)
                if response.status_code == 200:
                    st.toast(f"{speaker_name}の記録に成功しました")
                else:
                    st.error(f"エラーが発生しました (Code: {response.status_code})")
            except Exception as e:
                st.error(f"送信失敗: {e}")
            
            st.session_state[sk] += 1
            st.rerun()

        with col_u:
            # USERが話す番の時はボタンを強調
            u_style = "primary" if curr['speaker'] == "USER" else "secondary"
            if st.button("🙋 USER 発話終了", use_container_width=True, type=u_style):
                send_log("USER")

        with col_s:
            # SYSTEMが話す番の時はボタンを強調
            s_style = "primary" if curr['speaker'] == "SYSTEM" else "secondary"
            if st.button("🤖 SYSTEM 発話終了", use_container_width=True, type=s_style):
                send_log("SYSTEM")
        
        with col_back:
            if st.button("↩️ 1行戻る", use_container_width=True):
                st.session_state[sk] = max(0, idx - 1)
                st.rerun()
        with col_reset:
            if st.button("🔄 リセット", use_container_width=True):
                st.session_state[sk] = 0
                st.rerun()
    else:
        st.success("✅ このシナリオの全発話が終了し、ログが保存されました。")
        if st.button("もう一度最初から収録する"):
            st.session_state[sk] = 0
            st.rerun()

else:
    st.error("データの読み込みに失敗しました。スプレッドシートのURLまたは共有設定を確認してください。")
