import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# --- 設定 ---
# 1. 新しいスプレッドシートのURL（gid=664518608を反映）
SHEET_URL = "https://docs.google.com/spreadsheets/d/1sP0brv-0dIPTwAI39KYuxslTdbZSBqfFGj-RuwMiiFI/edit?gid=664518608#gid=664518608"
# 2. 新しいGASのURL
GAS_URL = "https://script.google.com/macros/s/AKfycbwXXRpMvNFRH-YRwgGtg_Wg7hY0zUd4dpBVBVH7fRs1Oba2SxS2J2ULhNAKhUOKiPIv/exec"

def get_csv_url(url):
    try:
        sid = url.split("/d/")[1].split("/")[0]
        gid = url.split("gid=")[1].split("#")[0].split("&")[0] if "gid=" in url else "0"
        return f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}"
    except:
        return None

st.set_page_config(page_title="対話収録システム", layout="wide")

# CSSでデザインとフォントサイズを調整（さらに見やすく）
st.markdown("""
    <style>
    .goal-box { background-color: #fff3cd; padding: 18px; border-radius: 12px; border: 1px solid #ffeeba; margin-bottom: 25px; font-size: 20px; line-height: 1.5; }
    .utterance-row { padding: 15px; margin: 10px 0; border-radius: 10px; font-size: 26px; line-height: 1.6; transition: 0.3s; }
    .speaker-label { font-weight: bold; margin-right: 10px; }
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
    
    # サイドバー：収録対象の選択
    t_id = st.sidebar.selectbox("収録IDを選択", df['dialogue_id'].unique())
    # turn_id順に並び替え
    scn = df[df['dialogue_id'] == t_id].sort_values('turn_id').reset_index(drop=True)
    
    # セッション管理
    sk = f'idx_{t_id}'
    if sk not in st.session_state:
        st.session_state[sk] = 0
    idx = st.session_state[sk]

    # --- 対話の目的（goal_description）を表示 ---
    goal = scn['goal_description'].iloc[0] if 'goal_description' in scn.columns else "目的の記載なし"
    st.markdown(f"<div class='goal-box'><b>【この対話の目的】</b><br>{goal}</div>", unsafe_allow_html=True)
    
    st.subheader(f"シナリオID: {t_id}")
    
    # 列名の判定（utterrancs という綴りに対応）
    u_col = 'utterrancs' if 'utterrancs' in scn.columns else 'utterance'

    # --- シナリオ表示（色分け・フォント大） ---
    for i, r in scn.iterrows():
        is_current = (i == idx)
        prefix = "👉" if is_current else "&nbsp;&nbsp;"
        
        # 色の設定（USER:青 / SYSTEM:緑）
        color = "#1E90FF" if r['speaker'] == "USER" else "#2E8B57"
        bg_color = "#f0f2f6" if is_current else "transparent"
        border_style = f"border-left: 10px solid {color};" if is_current else "border-left: 10px solid transparent;"
        
        # turn_id, speaker, utteranceを表示
        display_text = f"{prefix} <span class='speaker-label'>{int(r['turn_id'])}. [{r['speaker']}]</span> {r[u_col]}"
        
        st.markdown(f"""
            <div class='utterance-row' style='background-color: {bg_color}; color: {color}; {border_style}'>
                {display_text}
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # --- 操作エリア ---
    if idx < len(scn):
        curr = scn.iloc[idx]
        current_speaker = curr['speaker']
        current_turn_id = int(curr['turn_id'])
        
        st.markdown(f"### 次の発話担当: <span style='color:{('#1E90FF' if current_speaker=='USER' else '#2E8B57')}; font-size: 30px;'>{current_speaker} (Turn ID: {current_turn_id})</span>", unsafe_allow_html=True)
        
        col_u, col_s, col_back, col_reset = st.columns([1.2, 1.2, 0.6, 0.6])
        
        # ログ送信関数（line_idにturn_idを使用）
        def send_log(speaker_name, turn_id_val):
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            payload = {
                "dialogue_id": str(t_id),
                "line_id": turn_id_val,  # 選択された行のturn_idを送信
                "speaker": speaker_name,
                "timestamp": now
            }
            try:
                response = requests.post(GAS_URL, json=payload, timeout=10)
                if response.status_code == 200:
                    st.toast(f"記録完了 (Turn {turn_id_val}): {now}")
                else:
                    st.error("GASへの送信でエラーが発生しました。")
            except:
                st.error("通信エラーが発生しました。")
            
            st.session_state[sk] += 1
            st.rerun()

        with col_u:
            u_style = "primary" if current_speaker == "USER" else "secondary"
            if st.button("🙋 USER 発話終了", use_container_width=True, type=u_style, key=f"u_{idx}"):
                if current_speaker == "USER":
                    send_log("USER", current_turn_id)
                else:
                    st.warning("現在はSYSTEMの番です")

        with col_s:
            s_style = "primary" if current_speaker == "SYSTEM" else "secondary"
            if st.button("🤖 SYSTEM 発話終了", use_container_width=True, type=s_style, key=f"s_{idx}"):
                if current_speaker == "SYSTEM":
                    send_log("SYSTEM", current_turn_id)
                else:
                    st.warning("現在はUSERの番です")
        
        with col_back:
            if st.button("↩️ 戻る", use_container_width=True):
                st.session_state[sk] = max(0, idx - 1)
                st.rerun()
        with col_reset:
            if st.button("🔄 終了", use_container_width=True):
                st.session_state[sk] = len(scn)
                st.rerun()
    else:
        st.success("✅ 全ての収録が完了しました！")
        if st.button("もう一度最初から収録する"):
            st.session_state[sk] = 0
            st.rerun()
else:
    st.error("データの読み込みに失敗しました。URLと共有設定を再確認してください。")
