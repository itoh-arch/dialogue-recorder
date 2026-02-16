import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests

# --- 設定 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1sP0brv-0dIPTwAI39KYuxslTdbZSBqfFGj-RuwMiiFI/edit?gid=664518608#gid=664518608"
GAS_URL = "https://script.google.com/macros/s/AKfycbwXXRpMvNFRH-YRwgGtg_Wg7hY0zUd4dpBVBVH7fRs1Oba2SxS2J2ULhNAKhUOKiPIv/exec"

def get_csv_url(url):
    try:
        sid = url.split("/d/")[1].split("/")[0]
        gid = url.split("gid=")[1].split("#")[0].split("&")[0] if "gid=" in url else "0"
        return f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}"
    except: return None

st.set_page_config(page_title="対話収録システム", layout="wide")

# --- CSS: 操作パネルの固定とデザイン ---
st.markdown("""
    <style>
    /* 上部操作パネルを固定 */
    .stApp header { z-index: 100; }
    .fixed-panel {
        position: fixed;
        top: 50px;
        left: 0;
        width: 100%;
        background-color: white;
        z-index: 1000;
        padding: 10px 20px;
        border-bottom: 2px solid #ddd;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    /* 本文がパネルに隠れないように余白を作る */
    .main-content { margin-top: 250px; }
    
    .goal-box { background-color: #fff3cd; padding: 10px; border-radius: 8px; font-size: 15px; margin-bottom: 10px; }
    .utterance-row { padding: 8px; margin: 4px 0; border-radius: 6px; font-size: 16px; line-height: 1.2; }
    .speaker-label { font-weight: bold; margin-right: 6px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=5)
def load_data():
    url = get_csv_url(SHEET_URL)
    if url:
        try: return pd.read_csv(url)
        except: return None
    return None

df = load_data()

if df is not None:
    # サイドバーはそのまま
    t_id = st.sidebar.selectbox("収録IDを選択", df['dialogue_id'].unique())
    scn = df[df['dialogue_id'] == t_id].sort_values('turn_id').reset_index(drop=True)
    
    sk = f'idx_{t_id}'
    if sk not in st.session_state: st.session_state[sk] = 0
    idx = st.session_state[sk]

    log_key = f'logs_{t_id}'
    if log_key not in st.session_state: st.session_state[log_key] = []

    # --- 固定操作パネル ---
    with st.container():
        # HTMLの構造を使って「浮いたパネル」を模倣
        st.markdown(f"### シナリオ: {t_id}")
        
        goal = scn['goal_description'].iloc[0] if 'goal_description' in scn.columns else "なし"
        st.markdown(f"<div class='goal-box'><b>目的:</b> {goal}</div>", unsafe_allow_html=True)

        if idx < len(scn):
            curr = scn.iloc[idx]
            color = "#1E90FF" if curr['speaker']=="USER" else "#2E8B57"
            
            # 次の発話者を表示
            st.markdown(f"#### 次: <span style='color:{color};'>{curr['speaker']}</span> (Turn:{int(curr['turn_id'])})", unsafe_allow_html=True)
            
            # ボタンを横一列に配置
            c1, c2, c3, c4 = st.columns([1, 1, 0.5, 0.5])
            
            def add_log(spk, tid):
                jst = timezone(timedelta(hours=9))
                now = datetime.now(jst)
                ts = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                st.session_state[log_key].append({
                    "dialogue_id": str(t_id), "line_id": int(tid), "speaker": spk, "timestamp": ts
                })
                st.session_state[sk] += 1
                st.rerun()

            with c1:
                if st.button("🙋 USER 終了", use_container_width=True, type="primary" if curr['speaker']=="USER" else "secondary"):
                    if curr['speaker']=="USER": add_log("USER", curr['turn_id'])
            with c2:
                if st.button("🤖 SYSTEM 終了", use_container_width=True, type="primary" if curr['speaker']=="SYSTEM" else "secondary"):
                    if curr['speaker']=="SYSTEM": add_log("SYSTEM", curr['turn_id'])
            with c3:
                if st.button("↩️ 戻る", use_container_width=True):
                    if st.session_state[log_key]: st.session_state[log_key].pop()
                    st.session_state[sk] = max(0, idx - 1); st.rerun()
            with c4:
                if st.button("🔄 終了", use_container_width=True):
                    st.session_state[sk] = len(scn); st.rerun()
        else:
            st.success("✅ 収録完了")
            col_save, col_retry = st.columns([1, 1])
            with col_save:
                if st.button("📤 スプレッドシートに保存", type="primary", use_container_width=True):
                    if st.session_state[log_key]:
                        res = requests.post(GAS_URL, json=st.session_state[log_key], timeout=15)
                        if res.status_code == 200:
                            st.balloons(); st.success("保存成功！"); st.session_state[log_key] = []
                        else: st.error("保存失敗")
            with col_retry:
                if st.button("最初からやり直す", use_container_width=True):
                    st.session_state[sk] = 0; st.session_state[log_key] = []; st.rerun()

    st.divider()

    # --- シナリオ表示エリア（ここはスクロールする） ---
    u_col = 'utterrancs' if 'utterrancs' in scn.columns else 'utterance'
    for i, r in scn.iterrows():
        is_current = (i == idx)
        color = "#1E90FF" if r['speaker'] == "USER" else "#2E8B57"
        bg = "#f0f2f6" if is_current else "transparent"
        prefix = "👉" if is_current else "&nbsp;&nbsp;"
        st.markdown(f"<div class='utterance-row' style='background-color: {bg}; color: {color}; border-left: 5px solid {color if is_current else 'transparent'};'>{prefix} <span class='speaker-label'>{int(r['turn_id'])}. [{r['speaker']}]</span> {r[u_col]}</div>", unsafe_allow_html=True)

else:
    st.error("データ読み込み失敗")
