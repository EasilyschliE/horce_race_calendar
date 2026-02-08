import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="JRA レース検索", layout="wide")
st.title("JRA レース検索ツール")

@st.cache_data
def load_data():
    files = glob.glob("data/race_data_*.csv")
    if not files: return pd.DataFrame()
    
    df_list = [pd.read_csv(f) for f in files]
    df_all = pd.concat(df_list, ignore_index=True)
    # 日付、場所、Rの順でソート
    df_all = df_all.sort_values(["date", "location", "race_num"], ascending=[True, True, True])
    
    df_all["month"] = pd.to_datetime(df_all["date"]).dt.strftime("%Y-%m")
    return df_all.fillna("")

st.markdown("""<style>[data-testid="stElementToolbar"] { display: none; }</style>""", unsafe_allow_html=True)

try:
    df = load_data()
    if df.empty:
        st.warning("データがありません。")
    else:
        # --- サイドバー UI ---
        st.sidebar.header("検索フィルタ")

        # グループ1: 開催情報
        with st.sidebar.expander("開催日時・場所", expanded=True):
            month_list = sorted(list(df["month"].unique()))
            selected_months = st.multiselect("開催月", month_list)
            
            loc_list = sorted(list(df["location"].unique()))
            selected_locations = st.multiselect("競馬場", loc_list)

        # グループ2: レース詳細（条件・コース・重量を統合）
        with st.sidebar.expander("レース詳細", expanded=True):
            # 種別 & 性別
            col1, col2 = st.columns(2)
            with col1:
                selected_obs = st.radio("種別", ["すべて", "平地", "障害"])
            with col2:
                selected_gen = st.radio("性別", ["すべて", "牝馬限定"])
            
            # 馬場
            selected_surf = st.radio("馬場", ["すべて", "芝", "ダート"], horizontal=True)

            # クラス
            CLASS_ORDER = ["G1", "G2", "G3", "L", "OP", "3勝", "2勝", "1勝", "新馬", "未勝利", "その他"]
            available_classes = [c for c in CLASS_ORDER if c in df["class"].unique()]
            selected_classes = st.multiselect("クラス", available_classes)

            # 年齢条件
            age_list = sorted([a for a in df["age_condition"].unique() if a != ""])
            selected_ages = st.multiselect("年齢条件", age_list)
            
            # コース詳細
            track_opts = ["すべて", "通常", "内", "外", "直"]
            selected_tracks = st.multiselect("コース詳細", track_opts, default="すべて")
            
            # 距離（スライダー）
            min_d, max_d = int(df["distance"].min()), int(df["distance"].max())
            dist_range = st.slider("距離 (m)", min_d, max_d, (min_d, max_d), step=100)
            
            # 重量
            weight_list = ["定量", "ハンデ", "別定", "馬齢"]
            avail_weights = [w for w in weight_list if w in df["weight_type"].unique()]
            selected_weight = st.selectbox("重量種別", ["すべて"] + avail_weights)

        # --- フィルタリング実行 ---
        f_df = df.copy()
        if selected_months: f_df = f_df[f_df["month"].isin(selected_months)]
        if selected_locations: f_df = f_df[f_df["location"].isin(selected_locations)]
        if selected_obs != "すべて": f_df = f_df[f_df["is_obstacle"] == selected_obs]
        if selected_ages: f_df = f_df[f_df["age_condition"].isin(selected_ages)]
        if selected_classes: f_df = f_df[f_df["class"].isin(selected_classes)]
        if selected_surf != "すべて": f_df = f_df[f_df["surface"] == selected_surf]
        if selected_gen == "牝馬限定": f_df = f_df[f_df["gender"] == "牝馬限定"]
        if "すべて" not in selected_tracks and selected_tracks: f_df = f_df[f_df["track_detail"].isin(selected_tracks)]
        if selected_weight != "すべて": f_df = f_df[f_df["weight_type"] == selected_weight]
        f_df = f_df[(f_df["distance"] >= dist_range[0]) & (f_df["distance"] <= dist_range[1])]

        # --- カラムの表示順定義 ---
        display_columns = [
            "date",
            "location",
            "race_num",
            "race_name",
            "class",
            "is_obstacle",
            "age_condition",
            "surface",
            "distance",
            "track_detail",
            "gender",
            "weight_type"
        ]
        
        f_df = f_df[[c for c in display_columns if c in f_df.columns]]

        # --- 表示 ---
        st.subheader(f"該当レース: {len(f_df)} 件")
        st.dataframe(
            f_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "date": "日付", 
                "location": "場所", 
                "race_num": st.column_config.NumberColumn("R", format="%dR"),
                "race_name": "レース名",
                "class": "クラス",
                "is_obstacle": "種別", 
                "age_condition": "年齢", 
                "surface": "馬場", 
                "distance": st.column_config.NumberColumn("距離", format="%d m"),
                "track_detail": "詳細",
                "gender": "制限", 
                "weight_type": "重量"
            }
        )

except Exception as e:
    st.error(f"Error: {e}")