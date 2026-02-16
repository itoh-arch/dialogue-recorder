import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# --- 設定 ---
# 1. スプレッドシートのURL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1Dl1toHnKeAkwD55h5zsrHLkvrp3ml0x8hS0IPMAEJos/edit?gid=1940633540#gid=1940633540"
# 2. 先ほど取得したGASのURL（ここに貼り付け）
GAS_URL = "https://script.google.com/macros/s/XXXXX/exec"

# --- URLの変換ロジック ---
def get_csv_url(url):
    sheet_id = url.split("/d/")[1].split("/")[0]
    if "gid=" in url:
        gid = url.split("gid=")[1].split("#")[0].split("&")[0]
    else:
        gid = "0"
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

CSV_URL = get_csv_url(SHEET_URL)

st.set_page_config(page_title="対話収録システム", layout="wide")

# データの読み込み
@st.cache_data(ttl=5)
def load_scenario():
    try:
        df = pd.read_csv(CSV_URL)
        return df
    except Exception as e:
        st.error(f"スプレッドシートの読み込みに失敗しました。")
        return None

df = load_scenario()

# --- メイン画面表示 ---
if df is not None:
    expected_cols = ['dialogue_id', 'speaker', 'utterance']
    if not all(col in df.columns for col in expected_cols):
        st.warning(f"列名を確認してください: {expected_cols}")
    else:
        st.title("🎙️ 対話収録システム")

        # サイドバーで収録対象を選択
        ids = df['dialogue_id'].unique()
        target_id = st.sidebar.selectbox("収録IDを選択", ids)
        current_scenario = df[df['dialogue_id'] == target_id].reset_index(drop=True)

        # 進行状況の管理
        state_key = f'index_{target_id}'
        if state_key not in st.session_state:
            st.session_state[state_key] = 0
        idx = st.session_state[state_key]

        st.subheader(f"シナリオID: {target_id}")

        # シナリオ全行表示
        for i, row in current_scenario.iterrows():
            if i == idx:
                st.info(f"👉 **{i+1}. [{row['speaker']}]** {row['utterance']}")
            else:
                st.write(f"&nbsp;&nbsp;&nbsp;&nbsp; {i+1}. [{row['speaker']}] {row['utterance']}")

        st.divider()

        # 操作ボタン
        if idx < len(current_scenario):
            curr_row = current_scenario.iloc[idx]
            st.markdown(f"### 次の発話: **{curr_row['speaker']}**")
            
            col1, col2, col3 = st.columns([2,1,1])
            with col1:
                # ★エラーが出ていた箇所：インデントを正確に修正しました
                button_label = f"✅ {curr_row['speaker']} 発話終了"
                if st.button(button_label, type="primary", use_container_width=True):
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                    
                    log_payload = {
                        "dialogue_id": str(target_id),
                        "line_id": int(idx + 1),
                        "speaker": str(curr_row['speaker']),
                        "timestamp": now
                    }
                    
                    # GASへ送信
                    try:
                        requests.post(GAS_URL, json=log_payload, timeout=5)
                        st.toast(f"記録完了: {now}")
                    except:
                        st.error("スプレッドシートへの書き込みに失敗しました（GASのURLを確認してください）")
                    
                    st.session_state[state_key] += 1
                    st.rerun()
            
            with col2:
                if st.button("↩️ 戻る"):
                    st.session_state[state_key] = max(0, idx - 1)
                    st.rerun()
            with col3:
                if st.button("🔄 リセット"):
                    st.session_state[state_key] = 0
                    st.rerun()
        else:
            st.success("収録完了！")
            if st.button("最初からやり直す"):
                st.session_state[state_key] = 0
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

