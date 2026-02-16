import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# 1. スプレッドシートのURL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1Dl1toHnKeAkwD55h5zsrHLkvrp3ml0x8hS0IPMAEJos/edit?gid=1940633540#gid=1940633540"
# 2. GASのURLを貼り付けてください
GAS_URL = "https://script.google.com/macros/s/XXXXX/exec"

def get_csv_url(url):
    sid = url.split("/d/")[1].split("/")[0]
    gid = url.split("gid=")[1].split("#")[0].split("&")[0] if "gid=" in url else "0"
    return f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}"

st.set_page_config(page_title="対話収録システム", layout="wide")

@st.cache_data(ttl=5)
def load_data():
    return pd.read_csv(get_csv_url(SHEET_URL))

df = load_data()

if df is not None:
    st.title("🎙️ 対話収録システム")
    target_id = st.sidebar.selectbox("収録IDを選択", df['dialogue_id'].unique())
    scenario = df[df['dialogue_id'] == target_id].reset_index(drop=True)
    
    sk = f'idx_{target_id}'
    if sk not in st.session_state: st.session_state[sk] = 0
    idx = st.session_state[sk]

    st.subheader(f"シナリオ: {target_id}")
    for i, r in scenario.iterrows():
        if i == idx: st.info(f"👉 **{i+1}. [{r['speaker']}]** {r['utterance']}")
        else: st.write(f"&nbsp;&nbsp;&nbsp;&nbsp; {i+1}. [{r['speaker']}] {r['utterance']}")

    st.divider()
    if idx < len(scenario):
        curr = scenario.iloc[idx]
        st.markdown(f"### 次の発話: **{curr['speaker']}**")
        c1, c2, c3 = st.columns([2,1,1])
        with c1:
            if st.button(f"✅ {curr['speaker']} 発話終了", type="primary", use_container_width=True):
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                payload = {"dialogue_id": str(target_id), "line_id": int(idx + 1), "speaker": str(curr['speaker']), "timestamp": now}
                try:
                    requests.post(GAS_URL, json=payload, timeout=5)
                    st.toast("記録しました")
                except:
                    st.error("送信失敗")
                st.session_state[sk] += 1
                st.rerun()
        with c2:
            if st.button("↩️ 戻る"):
                st.session_state[sk] = max(0, idx - 1)
                st.rerun()
        with c3:
            if st.button("🔄 リセット"):
                st.session_state[sk] = 0
                st.rerun()
    else:
        st.success("完了！")
        if st.button("最初から"):
            st.session_state[sk] = 0
            st.rerun()

# --- 修正後のボタン処理部分 ---

# さきほどコピーしたGASのURLをここに貼り付け
GAS_URL = "https://script.google.com/macros/s/AKfycbxaahHoBJw_t74INs9_A7JNSwJaroK9M05HfMuDmCCaiD04gboAfZcA5e0CER3Gm8-rqg/exec"

# ... (中略) ...

        if st.button(f"✅ {curr_row['speaker']} 発話終了", type="primary", use_container_width=True):
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            
            # GASへ送信するデータ
            log_payload = {
                "dialogue_id": str(target_id),
                "line_id": int(idx + 1),
                "speaker": str(curr_row['speaker']),
                "timestamp": now
            }
            
            try:
                # タイムアウトを設定してGASに送信
                requests.post(GAS_URL, json=log_payload, timeout=5)
                st.toast(f"記録完了: {now}")
            except Exception as e:
                st.error(f"書き込み失敗: {e}")
            
            # 画面を次の行へ
            st.session_state[f'index_{target_id}'] += 1
            st.rerun()
