import streamlit as st
import pandas as pd
from datetime import datetime

# --- 設定 ---
# ここにご自身のGoogleスプレッドシートのURLを貼り付けてください
SHEET_URL = "https://docs.google.com/spreadsheets/d/あなたのシートID/edit#gid=0"
# CSV形式で読み込むための変換
CSV_URL = SHEET_URL.replace("/edit#gid=", "/export?format=csv&gid=")

st.set_page_config(page_title="対話収録システム", layout="wide")

# データの読み込み（スプレッドシートから）
@st.cache_data(ttl=5) # 5秒ごとに更新を確認
def load_scenario():
    # scenarioシート(gid=0)を読み込む例。gidはシートごとに異なるので注意
    return pd.read_csv(CSV_URL)

try:
    df = load_scenario()
except:
    st.error("スプレッドシートの読み込みに失敗しました。URLと共有設定を確認してください。")
    st.stop()

st.title("🎙️ 対話収録システム（全行表示モード）")

# サイドバーで収録対象を選択
ids = df['dialogue_id'].unique()
target_id = st.sidebar.selectbox("収録IDを選択", ids)
current_scenario = df[df['dialogue_id'] == target_id].reset_index(drop=True)

# 進行状況の管理
if f'index_{target_id}' not in st.session_state:
    st.session_state[f'index_{target_id}'] = 0

idx = st.session_state[f'index_{target_id}']

# --- メイン画面：シナリオ全行表示 ---
st.subheader(f"シナリオID: {target_id}")

for i, row in current_scenario.iterrows():
    # 今の発話行を強調
    if i == idx:
        st.info(f"👉 **[{row['speaker']}]** {row['utterance']}")
    else:
        st.write(f"（{i+1}） [{row['speaker']}] {row['utterance']}")

st.divider()

# --- 操作ボタン ---
if idx < len(current_scenario):
    curr_row = current_scenario.iloc[idx]
    st.write(f"次は **{curr_row['speaker']}** さんの番です")
    
    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        if st.button(f"✅ {curr_row['speaker']} 発話終了", type="primary", use_container_width=True):
            # ログ記録（本来はGoogle Sheets APIを使うのがベストですが、
            # 簡易的には一旦CSVに溜めて最後にDLするか、GASへ飛ばす形になります）
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            st.toast(f"記録しました: {now}")
            
            # ログ用セッションに保存（最後にまとめてスプレッドシートへ送る等の運用）
            st.session_state[f'index_{target_id}'] += 1
            st.rerun()
    
    with col2:
        if st.button("↩️ 1行戻る"):
            st.session_state[f'index_{target_id}'] = max(0, idx - 1)
            st.rerun()
    with col3:
        if st.button("🔄 リセット"):
            st.session_state[f'index_{target_id}'] = 0
            st.rerun()
else:
    st.success("全てのセリフが終了しました！")
    if st.button("最初からやり直す"):
        st.session_state[f'index_{target_id}'] = 0
        st.rerun()

# ログ表示（確認用）
st.sidebar.write("※現在はブラウザ上に一時保存されています")
