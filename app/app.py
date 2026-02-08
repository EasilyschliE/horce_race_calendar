import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="JRA レース検索", layout="wide")
st.title("JRA レース検索ツール")

@st.cache_data
def load_data():
    # data/ フォルダ内の全ての race_data_*.csv を取得
    files = glob.glob("data/race_data_*.csv")
    if not files:
        return pd.DataFrame()
    
    # 全てのCSVを読み込んで結合
    df_list = [pd.read_csv(f) for f in files]
    df_all = pd.concat(df_list, ignore_index=True)
    
    # 日付順に並び替え
    df_all = df_all.sort_values("date", ascending=True)
    # NaN(欠損値)を空文字に変換して表示を綺麗にする
    df_all = df_all.fillna("")
    return df_all

try:
    df = load_data()

    if df.empty:
        st.warning("データが見つかりません。text_to_csv.pyを実行してデータを登録してください。")
    else:
        # --- サイドバーの検索フィルタ ---
        st.sidebar.header("検索フィルタ")
        
        # 1. クラス選択 (並び順を固定)
        CLASS_ORDER = ["G1", "G2", "G3", "OP", "3勝", "2勝", "1勝", "新馬", "未勝利", "その他"]
        existing_classes = [c for c in CLASS_ORDER if c in df["class"].unique()]
        other_classes = [c for c in df["class"].unique() if c not in CLASS_ORDER]
        available_classes = existing_classes + other_classes

        # defaultを指定しないことで未選択状態にする
        selected_classes = st.sidebar.multiselect("クラス選択", available_classes)
        
        # 2. ラジオボタンによる絞り込み
        selected_surface = st.sidebar.radio("馬場種類", ["すべて", "芝", "ダート"])
        selected_gender = st.sidebar.radio("性別制限", ["すべて", "牝馬限定"])
        
        # 実際にデータに存在する重量種別を動的に取得
        weight_options = ["すべて"] + [w for w in ["定量", "ハンデ", "別定", "馬齢"] if w in df["weight_type"].unique() or w == ""]
        selected_weight = st.sidebar.radio("重量種別", weight_options)

        # --- フィルタリング実行 ---
        filtered_df = df.copy()

        # クラス：選択されている場合のみ絞り込む（未選択なら全表示）
        if selected_classes:
            filtered_df = filtered_df[filtered_df["class"].isin(selected_classes)]

        # 馬場
        if selected_surface != "すべて":
            filtered_df = filtered_df[filtered_df["surface"] == selected_surface]
        
        # 性別
        if selected_gender == "牝馬限定":
            filtered_df = filtered_df[filtered_df["gender"] == "牝馬限定"]
            
        # 重量
        if selected_weight != "すべて":
            filtered_df = filtered_df[filtered_df["weight_type"] == selected_weight]

        # --- 結果表示 ---
        st.subheader(f"該当レース: {len(filtered_df)} 件")
        
        # テーブル表示のカスタマイズ
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "date": "日付",
                "location": "場所",
                "race_num": "R",
                "race_name": "レース名",
                "class": "クラス",
                "distance": st.column_config.NumberColumn("距離", format="%d m"),
                "surface": "馬場",
                "gender": "制限",
                "weight_type": "重量"
            }
        )

except Exception as e:
    st.error(f"エラーが発生しました: {e}")