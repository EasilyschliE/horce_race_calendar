import streamlit as st
import pandas as pd

st.set_page_config(page_title="JRA レース検索ツール")
st.title("JRA レース検索ツール")

st.info("ここにJRAから取得したレースデータを表示します。")

# 検索条件のサンプル（UIのみ先行して作成）
st.sidebar.header("検索条件")
race_type = st.sidebar.selectbox("条件", ["芝2000m", "芝1600m", "ダ1200m"])
race_class = st.sidebar.multiselect("クラス", ["G1", "G2", "G3", "3勝", "2勝", "1勝"], default=["3勝"])

st.write(f"現在の選択条件: {race_type} / {race_class}")