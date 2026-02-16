import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# --- 設定 ---
# 共有いただいたURL（gidが含まれているもの）
SHEET_URL = "https://docs.google.com/spreadsheets/d/1Dl1toHnKeAkwD55h5zsrHLkvrp3ml0x8hS0IPMAEJos/edit?gid=1940633540#gid=1940633540"

# --- URLの変換ロジック ---
def get_csv_url(url):
    # スプレッドシートIDを抽出
    sheet_id = url.split("/d/")[1].split("/")[0]
    # gidを抽出（見つからない場合は0にする）
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
        # 変換したCSV URLを使って読み込み
        df = pd.read_csv(CSV_URL)
        return df
    except Exception as e:
        st.error(f"読み込み失敗。スプレッドシートの[共有]が「リンクを知っている全員」になっているか再確認してください。")
        st.info(f"Debug info: {e}")
        return None

df = load_scenario()

# --- メイン画面表示 ---
if df is not None:
    # 列名のチェック（dialogue_id, speaker, utterance があるか）
    expected_cols = ['dialogue_id', 'speaker', 'utterance']
    if not all(col in df.columns for col in expected_cols):
        st.warning(f"スプレッドシートの列名を確認してください。必要な列: {expected_cols}")
        st.write("現在の列名:", df.columns.tolist())
    else:
        st.title("🎙️ 対話収録システム")

        # サイドバーで収録対象を選択
        ids = df['dialogue_id'].unique()
        target_id = st.sidebar.selectbox("収録IDを選択", ids)
        current_scenario = df[df['dialogue_id'] == target_id].reset_index(drop=True)

        if f'index_{target_id}' not in st.session_state:
            st.session_state[f'index_{target_id}'] = 0
        idx = st.session_state[f'index_{target_id}']

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
                if st.button(f"✅ {curr_row['speaker']} 発話終了", type="primary", use_container_width=True):
                    # ※ここに以前お伝えしたGASの送信処理を追加できます
                    st.session_state[f'index_{target_id}'] += 1
                    st.rerun()
            with col2:
                if st.button("↩️ 戻る"):
                    st.session_state[f'index_{target_id}'] = max(0, idx - 1)
                    st.rerun()
            with col3:
                if st.button("🔄 リセット"):
                    st.session_state[f'index_{target_id}'] = 0
                    st.rerun()
        else:
            st.success("収録完了！")
            if st.button("最初から"):
                st.session_state[f'index_{target_id}'] = 0
                st.rerun()
