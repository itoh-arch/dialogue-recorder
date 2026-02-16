import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# --- 設定 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1sP0brv-0dIPTwAI39KYuxslTdbZSBqfFGj-RuwMiiFI/edit?gid=664518608#gid=664518608"
# GASのURL（最新のデプロイURLであることを確認してください）
GAS_URL = "https://script.google.com/macros/s/AKfycbwXXRpMvNFRH-YRwgGtg_Wg7hY0zUd4dpBVBVH7fRs1Oba2SxS2J2ULhNAKhUOKiPIv/exec"

def get_csv_url(url):
    try:
        sid = url.split("/d/")[1].split("/")[0]
        gid = url.split("gid=")[1].split("#")[0].split("&")[0] if "gid=" in url else "0"
        return f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}"
    except:
        return None

st.set_page_config(page_title="対話収録システム", layout="wide")

# CSSでデザイン調整（フォントを少し小さく、スッキリさせました）
st.markdown("""
    <style>
    .goal-box { background-color: #fff3cd; padding: 15px; border-radius: 10px; border: 1px solid #ffeeba; margin-bottom: 20px; font-size: 18px; line-height: 1.4; }
    .utterance-row { padding: 10px; margin: 5px 0; border-radius: 8px; font-size: 22px; line-height: 1.5; }
    .speaker-label { font-weight: bold; margin-right: 8px; }
    </style>
    """, unsafe_allow_html=True)

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
    t_id = st.sidebar.selectbox("収録IDを選択", df['dialogue_id'].unique())
    scn = df[df['dialogue_id'] == t_id].sort_values('turn_id').reset_index(drop=True)
    
    sk = f'idx_{t_id}'
    if sk not in st.session_state:
        st.session_state[sk] = 0
    idx = st.session_state[sk]

    goal = scn['goal_description'].iloc[0] if 'goal_description' in scn.columns else "目的の記載なし"
    st.markdown(f"<div class='goal-box'><b>【この対話の目的】</b><br>{goal}</div>", unsafe_allow_html=True)
    
    u_col = 'utterrancs' if 'utterrancs' in scn.columns else 'utterance'

    for i, r in scn.iterrows():
        is_current = (i == idx)
        prefix = "👉" if is_current else "&nbsp;&nbsp;"
        color = "#1E90FF" if r['speaker'] == "USER" else "#2E8B57"
        bg_color = "#f0f2f6" if is_current else "transparent"
        
        display_text = f"{prefix} <span class='speaker-label'>{int(r['turn_id'])}. [{r['speaker']}]</span> {r[u_col]}"
        
        st.markdown(f"""
            <div class='utterance-row' style='background-color: {bg_color}; color: {color}; border-left: 6px solid {color if is_current else "transparent"};'>
                {display_text}
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    if idx < len(scn):
        curr = scn.iloc[idx]
        current_speaker = curr['speaker']
        current_turn_id = int(curr['turn_id'])
        
        st.markdown(f"### 次の発話: <span style='color:{('#1E90FF' if current_speaker=='USER' else '#2E8B57')}; font-size: 24px;'>{current_speaker} (Turn ID: {current_turn_id})</span>", unsafe_allow_html=True)
        
        col_u, col_s, col_back, col_reset = st.columns([1, 1, 0.5, 0.5])
        
        def send_log(speaker_name, turn_id_val):
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            payload = {
                "dialogue_id": str(t_id),
                "line_id": turn_id_val,
                "speaker": speaker_name,
                "timestamp": now
            }
            try:
                # 送信と結果のキャッチを強化
                res = requests.post(GAS_URL, json=payload, timeout=10)
                if res.status_code == 200:
                    st.toast(f"記録完了: {now}")
                else:
                    st.error(f"書き込みエラー (HTTP {res.status_code})")
            except Exception as e:
                st.error(f"接続エラー: {e}")
            
            st.session_state[sk] += 1
            st.rerun()

        with col_u:
            u_style = "primary" if current_speaker == "USER" else "secondary"
            if st.button("🙋 USER 終了", use_container_width=True, type=u_style, key=f"u_{idx}"):
                if current_speaker == "USER": send_log("USER", current_turn_id)
                else: st.warning("次はSYSTEMです")

        with col_s:
            s_style = "primary" if current_speaker == "SYSTEM" else "secondary"
            if st.button("🤖 SYSTEM 終了", use_container_width=True, type=s_style, key=f"s_{idx}"):
                if current_speaker == "SYSTEM": send_log("SYSTEM", current_turn_id)
                else: st.warning("次はUSERです")
        
        with col_back:
            if st.button("↩️ 戻る", use_container_width=True):
                st.session_state[sk] = max(0, idx - 1)
                st.rerun()
        with col_reset:
            if st.button("🔄 最初", use_container_width=True):
                st.session_state[sk] = 0
                st.rerun()
    else:
        st.success("✅ 収録完了")
        if st.button("最初から"):
            st.session_state[sk] = 0
            st.rerun()
