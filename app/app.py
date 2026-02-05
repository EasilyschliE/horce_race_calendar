import streamlit as st
import pandas as pd

st.set_page_config(page_title="JRA レース検索", layout="wide")
st.title("JRA レース検索ツール")

@st.cache_data
def load_data():
    return pd.read_csv("data/race_data.csv")

try:
    df = load_data()

    st.sidebar.header("検索フィルタ")
    
    # 1. 馬場種類（ラジオボタン）
    surface_opt = ["すべて", "芝", "ダート"]
    selected_surface = st.sidebar.radio("馬場種類", surface_opt)
    
    # 2. 性別制限（ラジオボタン）
    gender_opt = ["すべて", "混合", "牝馬限定"]
    selected_gender = st.sidebar.radio("性別制限", gender_opt)
    
    # 3. 重量種別（ラジオボタン）
    weight_opt = ["すべて", "定量", "ハンデ", "別定", "馬齢"]
    selected_weight = st.sidebar.radio("重量種別", weight_opt)

    # 4. クラス選択（ここは複数選択が便利なのでmultiselectのままにしています）
    classes = st.sidebar.multiselect("クラス", df["class"].unique(), default=list(df["class"].unique()))

    # フィルタリングロジック
    filtered_df = df.copy()
    if selected_surface != "すべて":
        filtered_df = filtered_df[filtered_df["surface"] == selected_surface]
    if selected_gender != "すべて":
        filtered_df = filtered_df[filtered_df["gender"] == selected_gender]
    if selected_weight != "すべて":
        filtered_df = filtered_df[filtered_df["weight_type"] == selected_weight]
    
    filtered_df = filtered_df[filtered_df["class"].isin(classes)]

    st.subheader(f"該当レース: {len(filtered_df)} 件")
    st.dataframe(filtered_df, use_container_width=True)

except FileNotFoundError:
    st.error("データファイルが見つかりません。text_to_csv.pyを実行してください。")