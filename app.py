import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests

# --- 設定 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1sP0brv-0dIPTwAI39KYuxslTdbZSBqfFGj-RuwMiiFI/edit?gid=664518608#gid=664518608"
GAS_URL = "https://script.google.com/macros/s/AKfycbwGSaJNCQKKPvNEy-lwk3GkMeY1tePPFgLc8jbH9IqkY7V_iMgSyiXXe0yuuH3MGNBd/exec"

def get_csv_url(url):
    try:
        sid = url.split("/d/")[1].split("/")[0]
        gid = url.split("gid=")[1].split("#")[0].split("&")[0] if "gid=" in url else "0"
        return f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}"
    except: return None

st.set_page_config(page_title="対話収録システム", layout="wide")

# CSS（フォントサイズを微調整：本文20px）
st.markdown("""
    <style>
    .goal-box { background-color: #fff3cd; padding: 12px; border-radius: 8px; font-size: 16px; margin-bottom: 15px; }
    .utterance-row { padding: 8px; margin: 4px 0; border-radius: 6px; font-size: 20px; line-height: 1.4; }
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
    st.title("🎙️ 対話収録システム")
    t_id = st.sidebar.selectbox("収録IDを選択", df['dialogue_id'].unique())
    scn = df[df['dialogue_id'] == t_id].sort_values('turn_id').reset_index(drop=True)
    
    # 進行管理
    sk = f'idx_{t_id}'
    if sk not in st.session_state: st.session_state[sk] = 0
    idx = st.session_state[sk]

    # ログの一時保存（ブラウザ内）
    log_key = f'logs_{t_id}'
    if log_key not in st.session_state: st.session_state[log_key] = []

    # 目的
    goal = scn['goal_description'].iloc[0] if 'goal_description' in scn.columns else "なし"
    st.markdown(f"<div class='goal-box'><b>【目的】</b> {goal}</div>", unsafe_allow_html=True)
    
    u_col = 'utterrancs' if 'utterrancs' in scn.columns else 'utterance'

    # シナリオ表示
    for i, r in scn.iterrows():
        is_current = (i == idx)
        color = "#1E90FF" if r['speaker'] == "USER" else "#2E8B57"
        bg = "#f0f2f6" if is_current else "transparent"
        prefix = "👉" if is_current else "&nbsp;&nbsp;"
        st.markdown(f"<div class='utterance-row' style='background-color: {bg}; color: {color}; border-left: 5px solid {color if is_current else 'transparent'};'>{prefix} <span class='speaker-label'>{int(r['turn_id'])}. [{r['speaker']}]</span> {r[u_col]}</div>", unsafe_allow_html=True)

    st.divider()

    if idx < len(scn):
        curr = scn.iloc[idx]
        st.markdown(f"### 次: <span style='color:{('#1E90FF' if curr['speaker']=='USER' else '#2E8B57')};'>{curr['speaker']}</span>")
        
        c1, c2, c3, c4 = st.columns([1, 1, 0.5, 0.5])
        
        def add_log(spk, tid):
            # 日本時間でミリ秒まで取得
            jst = timezone(timedelta(hours=9))
            now = datetime.now(jst)
            # .strftime("%Y-%m-%d %H:%M:%S.%f") の末尾3桁を消してミリ秒にする
            ts = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            st.session_state[log_key].append({
                "dialogue_id": str(t_id),
                "line_id": int(tid),
                "speaker": spk,
                "timestamp": ts
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
            if st.button("↩️ 戻る"):
                if st.session_state[log_key]: st.session_state[log_key].pop()
                st.session_state[sk] = max(0, idx - 1); st.rerun()
        with c4:
            if st.button("🔄 終了"):
                st.session_state[sk] = len(scn); st.rerun()
    else:
        st.success("✅ 収録完了！ログを保存してください。")
        if st.button("📤 スプレッドシートに保存", type="primary", use_container_width=True):
            if st.session_state[log_key]:
                try:
                    # まとめて送信
                    res = requests.post(GAS_URL, json=st.session_state[log_key], timeout=15)
                    if res.status_code == 200:
                        st.balloons()
                        st.success("保存成功！スプレッドシートを確認してください。")
                        st.session_state[log_key] = [] # 空にする
                    else: st.error(f"保存失敗 (Status: {res.status_code})")
                except Exception as e: st.error(f"エラー: {e}")
        if st.button("最初からやり直す"):
            st.session_state[sk] = 0; st.session_state[log_key] = []; st.rerun()
