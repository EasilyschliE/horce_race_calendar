import re
import pandas as pd
import os

# JRAの番組表テキストをここに貼り付け
raw_text = """
2026年5月31日（日曜）　競馬番組

という感じでコピペする

"""

def extract_date(text):
    """テキストから日付を抽出して YYYY-MM-DD 形式で返す"""
    date_match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
    if date_match:
        return f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"
    return None

def parse_jra_text(text):
    date_str = extract_date(text)
    if not date_str:
        print("エラー: 日付が見つかりませんでした。")
        return pd.DataFrame()

    races = []
    # 競馬場(1回中山1日など)で分割
    chunks = re.split(r"(\d+回[^\d\s]+\d+日)", text)
    
    current_location = ""
    for i in range(len(chunks)):
        chunk = chunks[i]
        loc_match = re.search(r"\d+回(.*?)\d+日", chunk)
        if loc_match:
            current_location = loc_match.group(1).strip()
            continue
        
        if not current_location: continue

        # レース情報の抽出
        # パターンを微調整して馬場詳細(芝・外など)をグループとして抽出
        pattern = r"(\d+)\s*レース\s*([\s\S]*?)\s*([\d,]+)（(芝|ダ)(.*?)）([\s\S]*?)(\d+時\d+分)"
        matches = re.findall(pattern, chunk)

        for m in matches:
            race_no = int(m[0])
            condition_raw = m[1].replace("\n", " ").strip()
            
            # --- コース詳細（内・外・直） ---
            track_detail_raw = m[4] # 「・外」や「・内」が入る
            track_detail = ""
            if "外" in track_detail_raw: track_detail = "外"
            elif "内" in track_detail_raw: track_detail = "内"
            elif "直" in track_detail_raw: track_detail = "直"

            # 障害レース判定
            is_obstacle = "障害" if "障害" in condition_raw else "平地"
            
            # 年齢条件
            age_match = re.search(r"(\d歳以上|\d歳)", condition_raw)
            age_condition = age_match.group(1) if age_match else "不明"
            
            # --- クラス判定（L をここに統合） ---
            race_class = "その他"
            if any(x in condition_raw for x in ["GⅢ", "G3"]): race_class = "G3"
            elif any(x in condition_raw for x in ["GⅡ", "G2"]): race_class = "G2"
            elif any(x in condition_raw for x in ["GⅠ", "G1"]): race_class = "G1"
            elif "（L）" in condition_raw or "(L)" in condition_raw: race_class = "L" # リステッド
            elif "オープン" in condition_raw: race_class = "OP"
            elif "3勝" in condition_raw: race_class = "3勝"
            elif "2勝" in condition_raw: race_class = "2勝"
            elif "1勝" in condition_raw: race_class = "1勝"
            elif "未勝利" in condition_raw: race_class = "未勝利"
            elif "新馬" in condition_raw: race_class = "新馬"

            # レース名の抽出とクリーンアップ
            parts = re.split(r'\s{2,}', condition_raw)
            race_name = parts[0] if len(parts) > 0 else condition_raw
            # 名称から（L）を削って綺麗にする
            race_name = race_name.replace("（L）", "").replace("(L)", "").strip()
            
            distance = m[2].replace(",", "")
            surface = "芝" if "芝" in m[3] else "ダート"
            extra_raw = m[5].replace("\n", " ").strip()

            # 性別制限
            gender = "牝馬限定" if "（牝）" in condition_raw or "（牝）" in extra_raw else ""
            
            # 重量種別
            weight = ""
            for w in ["ハンデ", "定量", "別定", "馬齢"]:
                if w in extra_raw or w in condition_raw:
                    weight = w
                    break

            races.append({
                "date": date_str,
                "location": current_location,
                "race_num": race_no,
                "is_obstacle": is_obstacle,
                "age_condition": age_condition,
                "race_name": race_name,
                "class": race_class,      # ここに L が入る
                "track_detail": track_detail,
                "surface": surface,
                "distance": int(distance),
                "gender": gender,
                "weight_type": weight
            })

    return pd.DataFrame(races)

if __name__ == "__main__":
    df_new = parse_jra_text(raw_text)
    
    if not df_new.empty:
        date_val = df_new['date'].iloc[0]
        year_month = date_val[:7].replace("-", "_")
        output_path = f"data/race_data_{year_month}.csv"
        
        os.makedirs("data", exist_ok=True)

        if os.path.exists(output_path):
            df_old = pd.read_csv(output_path)
            df_combined = pd.concat([df_old, df_new], ignore_index=True)
            df_combined = df_combined.drop_duplicates(
                subset=["date", "location", "race_num"],
                keep='last'
            )
            df_combined.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"データを更新しました: {output_path} (合計: {len(df_combined)} 件)")
        else:
            df_new.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"新規作成しました: {output_path} (件数: {len(df_new)} 件)")
    else:
        print("追加するデータが見つかりませんでした。")