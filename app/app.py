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
    
    # --- 1. クラス選択の並び順を定義 ---
    # JRAの一般的な昇格順に並べるためのリスト
    CLASS_ORDER = ["G1", "G2", "G3", "OP", "3勝", "2勝", "1勝", "新馬", "未勝利", "その他"]
    
    # 実際にデータ内にあるクラスのみを取り出し、上記の順序でソート
    existing_classes = [c for c in CLASS_ORDER if c in df["class"].unique()]
    # もしリストにないクラスがデータにあれば、それも末尾に追加
    other_classes = [c for c in df["class"].unique() if c not in CLASS_ORDER]
    available_classes = existing_classes + other_classes

    # multiselectの初期値（default）を空にすると、最初は何も選ばれていない状態になります
    selected_classes = st.sidebar.multiselect("クラス選択", available_classes)
    
    # --- 2. ラジオボタンの設定 ---
    surface_opt = ["すべて", "芝", "ダート"]
    selected_surface = st.sidebar.radio("馬場種類", surface_opt)
    
    gender_opt = ["すべて", "牝馬限定"]
    selected_gender = st.sidebar.radio("性別制限", gender_opt)
    
    weight_opt = ["すべて", "定量", "ハンデ", "別定", "馬齢"]
    selected_weight = st.sidebar.radio("重量種別", weight_opt)

    # --- 3. フィルタリングロジックの適用 ---
    filtered_df = df.copy()

    # クラス：何も選択されていない場合は全件、選択されている場合はその値で絞り込み
    if selected_classes:
        filtered_df = filtered_df[filtered_df["class"].isin(selected_classes)]

    # その他のフィルタ
    if selected_surface != "すべて":
        filtered_df = filtered_df[filtered_df["surface"] == selected_surface]
    
    if selected_gender == "牝馬限定":
        filtered_df = filtered_df[filtered_df["gender"] == "牝馬限定"]
        
    if selected_weight != "すべて":
        filtered_df = filtered_df[filtered_df["weight_type"] == selected_weight]

    # --- 4. 結果表示 ---
    st.subheader(f"該当レース: {len(filtered_df)} 件")
    st.dataframe(filtered_df, use_container_width=True)

except FileNotFoundError:
    st.error("データファイルが見つかりません。text_to_csv.pyを実行してください。")