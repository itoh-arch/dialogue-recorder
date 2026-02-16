import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# --- 設定 ---
# ご共有いただいたスプレッドシートのURL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1Dl1toHnKeAkwD55h5zsrHLkvrp3ml0x8hS0IPMAEJos/edit?gid=1940633540#gid=1940633540"
# GASのURL（取得済みであればここに貼り付けてください）
GAS_URL = "ここにGASのデプロイURLを貼り付けてください"

st.set_page_config(page_title="対話収録システム", layout="wide")

# スプレッドシートIDを抽出してCSVエクスポート用URLに変換
try:
    sheet_id = SHEET_URL.split("/d/")[1].split("/")[0]
    CSV_URL = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
except Exception as e:
    st.error(f"URLの解析に失敗しました: {e}")
    st.stop()

# データの読み込み
@st.cache_data(ttl=10) # 10秒キャッシュ
def load_scenario():
    try:
        # スプレッドシートから読み込み
        df = pd.read_csv(CSV_URL)
        return df
    except Exception as e:
        st.error(f"スプレッドシートの読み込みに失敗しました。共有設定を確認してください。\nError: {e}")
        return None

df = load_scenario()

if df is not None:
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

    # テーブル形式で全行を表示（今の行をハイライト）
    for i, row in current_scenario.iterrows():
        if i == idx:
            st.info(f"👉 **{i+1}. [{row['speaker']}]** {row['utterance']}")
        else:
            st.write(f"&nbsp;&nbsp;&nbsp;&nbsp; {i+1}. [{row['speaker']}] {row['utterance']}")

    st.divider()

    # --- 操作ボタン ---
    if idx < len(current_scenario):
        curr_row = current_scenario.iloc[idx]
        st.markdown(f"### 次の発話者: **{curr_row['speaker']}**")
        
        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            if st.button(f"✅ {curr_row['speaker']} 発話終了（記録）", type="primary", use_container_width=True):
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                
                # ログ送信用のデータ
                log_data = {
                    "dialogue_id": target_id,
                    "line_id": int(idx + 1),
                    "speaker": curr_row['speaker'],
                    "timestamp": now
                }
                
                # GASに送信（GAS_URLが設定されている場合のみ）
                if "script.google.com" in GAS_URL:
                    try:
                        requests.post(GAS_URL, json=log_data)
                        st.toast("スプレッドシートに記録しました！")
                    except:
                        st.error("GASへの送信に失敗しました。")
                else:
                    st.warning("GASのURLが設定されていないため、スプレッドシートには保存されません。")
                
                # 次の行へ
                st.session_state[f'index_{target_id}'] += 1
                st.rerun()
        
        with col2:
            if st.button("↩️ 1行戻る"):
                st.session_state[f'index_{target_id}'] = max(0, idx - 1)
                st.rerun()
        with col3:
            if st.button("🔄 最初から"):
                st.session_state[f'index_{target_id}'] = 0
                st.rerun()
    else:
        st.success("全てのセリフが終了しました！")
        if st.button("次のシナリオへ / 最初から"):
            st.session_state[f'index_{target_id}'] = 0
            st.rerun()

# デバッグ用：読み込んだデータのプレビュー（サイドバー下部）
if st.sidebar.checkbox("元データのプレビューを表示"):
    st.sidebar.write(df)
