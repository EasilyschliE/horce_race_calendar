import streamlit as st
import pandas as pd

st.set_page_config(page_title="JRA レース検索", layout="wide")
st.title("JRA レース検索ツール")

@st.cache_data
def load_data():
    # 実際にはここにJRAからコピーしたデータを保存したCSVを指定します
    return pd.read_csv("race_data.csv")

try:
    df = load_data()

    # サイドバーに検索条件を配置
    st.sidebar.header("検索フィルタ")
    
    # 1. クラス選択
    classes = st.sidebar.multiselect("クラス選択", df["class"].unique(), default=["3勝"])
    
    # 2. 馬場選択
    surfaces = st.sidebar.multiselect("馬場種類", df["surface"].unique(), default=["芝"])
    
    # 3. 距離選択（スライダーで範囲指定も可能）
    min_dist, max_dist = st.sidebar.select_slider(
        "距離範囲 (m)",
        options=sorted(df["distance"].unique()),
        value=(min(df["distance"]), max(df["distance"]))
    )

    # フィルタリング実行
    filtered_df = df[
        (df["class"].isin(classes)) &
        (df["surface"].isin(surfaces)) &
        (df["distance"].between(min_dist, max_dist))
    ]

    # 結果表示
    st.subheader(f"該当レース: {len(filtered_df)} 件")
    st.dataframe(filtered_df, use_container_width=True)

except FileNotFoundError:
    st.warning("race_data.csvをフォルダ内に作成してください。")