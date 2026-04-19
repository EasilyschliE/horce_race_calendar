import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="JRA レース検索", layout="wide")
st.title("JRA レース検索ツール")

@st.cache_data
def load_data(file_hash): # 引数を追加
    files = glob.glob("data/race_data_*.csv")
    if not files: return pd.DataFrame()
    
    df_list = [pd.read_csv(f) for f in files]
    df_all = pd.concat(df_list, ignore_index=True)
    df_all = df_all.sort_values(["date", "location", "race_num"], ascending=[True, True, True])
    
    # 日付変換エラーを避けるため errors='coerce' を入れるのが安全です
    df_all["month"] = pd.to_datetime(df_all["date"], errors='coerce').dt.strftime("%Y-%m")
    return df_all.fillna("")

# 呼び出し側を修正
# dataフォルダ内の全ファイルの「最終更新日時」を合計したものをハッシュとして渡す
data_files = glob.glob("data/race_data_*.csv")
file_hash = sum([os.path.getmtime(f) for f in data_files]) if data_files else 0
df = load_data(file_hash)
st.markdown("""<style>[data-testid="stElementToolbar"] { display: none; }</style>""", unsafe_allow_html=True)

try:
    df = load_data(file_hash)
    if df.empty:
        st.warning("データがありません。")
    else:
        # --- ここから追加：データ期間の表示 ---
        min_month = df["month"].min().replace("-", "年") + "月"
        max_month = df["month"].max().replace("-", "年") + "月"
        st.info(f"📊 現在インポートされているデータ期間: {min_month} 〜 {max_month}")

        # --- メイン画面上部の免責事項（折り畳み） ---
        with st.expander("⚠️ 本アプリのデータと免責事項について"):
            st.caption("""
            - 本アプリは個人が作成した非公式のツールであり、JRA（日本中央競馬会）とは一切関係ありません。
            - 表示されるデータは公式サイトの番組表を参照して入力したものですが、正確性を保証するものではありません。
            - 開催の変更や最新の出馬表については、必ず[JRA公式サイト](https://www.jra.go.jp/)をご確認ください。
            - 本アプリの利用により生じた損害について、制作者は一切の責任を負いません。
            """)

        # --- サイドバー UI ---
        st.sidebar.header("検索フィルタ")

        LOCATION_ORDER = ["札幌", "函館", "福島", "新潟", "中山", "東京", "中京", "京都", "阪神", "小倉"]

        # データの抽出部分を修正
        with st.sidebar.expander("開催日時・場所", expanded=True):
            month_list = sorted(list(df["month"].unique()))
            selected_months = st.multiselect("開催月", month_list, placeholder="全期間")
            
            # ▼ ここを修正 ▼
            # データに含まれる競馬場を取得
            raw_loc_list = df["location"].unique()
            # LOCATION_ORDER にある順序でソートし、リストにないものは後ろに回す
            loc_list = sorted(raw_loc_list, key=lambda x: LOCATION_ORDER.index(x) if x in LOCATION_ORDER else 99)
            selected_locations = st.multiselect("競馬場", loc_list, placeholder="全競馬場")
            
        # グループ2: レース条件
        with st.sidebar.expander("レース条件", expanded=True):
            min_d, max_d = int(df["distance"].min()), int(df["distance"].max())
            dist_range = st.slider("距離 (m)", min_d, max_d, (min_d, max_d), step=100)

            # 性別と種別を1行にまとめるか、マルチセレクト化
            selected_gen = st.checkbox("牝馬限定のみ表示") # radioよりチェックボックスの方が直感的
            
            selected_surf = st.multiselect("馬場", ["芝", "ダート"], placeholder="すべて")

            CLASS_ORDER = ["G1", "G2", "G3", "L", "OP", "3勝", "2勝", "1勝", "新馬", "未勝利", "その他"]
            available_classes = [c for c in CLASS_ORDER if c in df["class"].unique()]
            selected_classes = st.multiselect("クラス", available_classes, placeholder="全クラス")

            age_list = sorted([a for a in df["age_condition"].unique() if a != ""])
            selected_ages = st.multiselect("年齢条件", age_list, placeholder="全年齢")

        # グループ3: コース・重量
        with st.sidebar.expander("詳細条件", expanded=False): # ここは初期状態で閉じておくとスッキリ

            selected_obs = st.multiselect("レース種別", ["平地", "障害"], placeholder="すべて")

            weight_list = ["定量", "ハンデ", "別定", "馬齢"]
            avail_weights = [w for w in weight_list if w in df["weight_type"].unique()]
            selected_weights = st.multiselect("重量種別", avail_weights, placeholder="すべて")
            
            track_opts = ["内", "外", "直"] # 「すべて」をリストから除外
            selected_tracks = st.multiselect("コース詳細", track_opts, placeholder="すべて")

        # --- フィルタリング実行 ---
        f_df = df.copy()

        # 1. 開催月 & 競馬場 (multiselect)
        if selected_months:
            f_df = f_df[f_df["month"].isin(selected_months)]
        if selected_locations:
            f_df = f_df[f_df["location"].isin(selected_locations)]

        # 2. 種別 (multiselect化に対応)
        if selected_obs:
            f_df = f_df[f_df["is_obstacle"].isin(selected_obs)]

        # 3. 性別 (checkboxに対応)
        if selected_gen:
            f_df = f_df[f_df["gender"] == "牝馬限定"]

        # 4. 馬場 (multiselect化に対応)
        if selected_surf:
            f_df = f_df[f_df["surface"].isin(selected_surf)]

        # 5. クラス & 年齢条件 (multiselect)
        if selected_classes:
            f_df = f_df[f_df["class"].isin(selected_classes)]
        if selected_ages:
            f_df = f_df[f_df["age_condition"].isin(selected_ages)]

        # 6. 重量種別 (multiselectに対応。変数が selected_weights になっている点に注意)
        if selected_weights:
            f_df = f_df[f_df["weight_type"].isin(selected_weights)]

        # 7. コース詳細 (multiselectに対応)
        if selected_tracks:
            f_df = f_df[f_df["track_detail"].isin(selected_tracks)]

        # 8. 距離 (スライダー)
        f_df = f_df[(f_df["distance"] >= dist_range[0]) & (f_df["distance"] <= dist_range[1])]

        # 初期状態（何も選ばれていない状態）かどうかをチェック
        is_filter_applied = any([
            selected_months, 
            selected_locations, 
            selected_obs, 
            selected_gen, 
            selected_surf, 
            selected_classes, 
            selected_ages, 
            selected_weights, 
            selected_tracks,
            dist_range != (min_d, max_d)  # 距離が動かされているか
        ])

        # --- 表示ロジック（データがない時の処理含む） ---
        if not is_filter_applied:
            # 【重要】何も選ばれていない時は案内だけ出す
            st.info("👈 左側のサイドバーから検索条件（月、競馬場、クラスなど）を指定してください。")
            
        elif f_df.empty:
            st.warning("条件に一致するレースが見つかりませんでした。検索条件を緩めてみてください。")
            
        else:
            st.subheader(f"該当レース: {len(f_df)} 件")

            # --- ここから追加：スマホ用スッキリ表示トグル ---
            # デフォルトをTrueにしておき、スマホユーザーがすぐ見やすいようにする
            is_mobile = st.toggle("📱 スマホ向け短縮表示", value=True, help="列を結合して横スクロールを減らします")

            if is_mobile:
                for index, row in f_df.iterrows():
                    header_text = f"{row['date']} ｜ {row['race_name']} ({row['location']}{row['race_num']}R)"
                    
                    with st.expander(header_text):
                        # 展開した中身（2列にして無駄な縦スクロールも防ぐ）
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"**クラス:** {row['class']}")
                            st.markdown(f"**年齢条件:** {row['age_condition']}")
                            st.markdown(f"**制限:** {row['gender']}")
                        with c2:
                            st.markdown(f"**コース:** {row['surface']}{row['distance']}m")
                            st.markdown(f"**馬場詳細:** {row['track_detail']}")
                            st.markdown(f"**重量:** {row['weight_type']}")
                            
            else:
                # --- PC用：従来の全列表示 ---
                display_columns = [
                    "date", "location", "race_num", "race_name", "class", 
                    "is_obstacle", "age_condition", "surface", "distance", 
                    "track_detail", "gender", "weight_type"
                ]
                show_df = f_df[[c for c in display_columns if c in f_df.columns]]

                st.dataframe(
                    show_df,
                    use_container_width=True,
                    hide_index=True,
                    height=600,
                    column_config={
                        "date": "日付", 
                        "location": "場所", 
                        "race_num": st.column_config.NumberColumn("R", format="%dR"),
                        "race_name": st.column_config.TextColumn("レース名", width="medium"),
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