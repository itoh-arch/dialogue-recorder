import streamlit as st
import pandas as pd
from datetime import datetime, timedelta  # timedeltaを追加
import requests

# --- 設定 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1sP0brv-0dIPTwAI39KYuxslTdbZSBqfFGj-RuwMiiFI/edit?gid=664518608#gid=664518608"
GAS_URL = "https://script.google.com/macros/s/AKfycbwXXRpMvNFRH-YRwgGtg_Wg7hY0zUd4dpBVBVH7fRs1Oba2SxS2J2ULhNAKhUOKiPIv/exec"

def get_csv_url(url):
    try:
        sid = url.split("/d/")[1].split("/")[0]
        gid = url.split("gid=")[1].split("#")[0].split("&")[0] if "gid=" in url else "0"
        return f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}"
    except:
        return None

st.set_page_config(page_title="対話収録システム", layout="wide")

# CSS（フォントサイズを少し抑えめに調整）
st.markdown("""
    <style>
    .goal-box { background-color: #fff3cd; padding: 15px; border-radius: 10px; border: 1px solid #ffeeba; margin-bottom: 20px; font-size: 18px; }
    .utterance-row { padding: 10px; margin: 5px 0; border-radius: 8px; font-size: 20px; line-height: 1.5; }
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
            """, unsafe_allow_html
