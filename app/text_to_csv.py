import re
import pandas as pd
import os

# JRAの番組表テキストをここに貼り付け
raw_text = """
2026年1月31日（土曜）　競馬番組
表内の略称 戻る
土曜日の競馬番組
日曜日の競馬番組
このページの情報は、事前に発表した春季・夏季・秋季の各競馬番組の内容（予定）です。最新の情報は、通常木曜日16時頃に発表する「競馬メニュー」の「出馬表」でご確認ください。

注記：	当該週の出馬投票の結果や当日の天候によって、レース番号（レース順序）、馬場、距離、発走時刻などの変更や、レースの中止・延期といった追加・変更情報が発生する場合があります。
1回東京1日
レース
番号
レース名・条件	発走時刻
1
レース
3歳未勝利

1,400（ダ）（牝）

10時05分
2
レース
4歳以上1勝クラス

2,100（ダ）定量

10時35分
3
レース
3歳未勝利

1,600（ダ）

11時05分
4
レース
3歳新馬

1,400（ダ）

11時35分
5
レース
3歳新馬

1,800（芝）

12時25分
6
レース
3歳未勝利

1,600（芝）

13時00分
7
レース
3歳1勝クラス

1,600（ダ）

13時30分
8
レース
4歳以上2勝クラス

1,400（ダ）定量

14時00分
9
レース
白嶺ステークス

4歳以上3勝クラス

1,600（ダ）ハンデ

14時30分
10
レース
クロッカスステークス（L）

3歳オープン

1,400（芝）別定

15時05分
11
レース
白富士ステークス（L）

4歳以上オープン

2,000（芝）別定

15時45分
12
レース
4歳以上1勝クラス

1,800（芝）定量

16時25分
 
2回京都1日
レース
番号
レース名・条件	発走時刻
1
レース
3歳未勝利

1,200（ダ）（牝）

9時55分
2
レース
3歳未勝利

1,800（ダ）

10時25分
3
レース
3歳未勝利

1,400（ダ）

10時55分
4
レース
3歳未勝利

1,800（ダ）

11時25分
5
レース
3歳新馬

2,000（芝）

12時15分
6
レース
3歳未勝利

1,600（芝）

12時50分
7
レース
3歳1勝クラス

1,800（ダ）

13時20分
8
レース
4歳以上1勝クラス

1,900（ダ）定量

13時50分
9
レース
長浜特別

4歳以上2勝クラス

1,400（ダ）定量

14時20分
10
レース
許波多特別

4歳以上2勝クラス

2,400（芝・外）ハンデ

14時55分
11
レース
舞鶴ステークス

4歳以上3勝クラス

1,800（ダ）（牝）定量

15時30分
12
レース
4歳以上1勝クラス

1,600（芝・外）定量

16時10分
 
1回小倉3日
レース
番号
レース名・条件	発走時刻
1
レース
3歳未勝利

1,000（ダ）

9時45分
2
レース
3歳未勝利

2,000（芝）（牝）

10時15分
3
レース
4歳以上1勝クラス

1,700（ダ）定量

10時45分
4
レース
障害4歳以上未勝利

2,860（芝）定量

11時15分
5
レース
障害4歳以上オープン

2,860（芝）別定

12時05分
6
レース
3歳未勝利

1,200（芝）（若手騎手）

12時40分
7
レース
3歳未勝利

1,800（芝）

13時10分
8
レース
4歳以上1勝クラス

1,200（芝）定量

13時40分
9
レース
有田特別

4歳以上2勝クラス

1,000（ダ）定量

14時10分
10
レース
平尾台特別

4歳以上2勝クラス

1,700（ダ）（牝）定量

14時45分
11
レース
巌流島ステークス

4歳以上3勝クラス

1,200（芝）ハンデ

15時20分
12
レース
4歳以上1勝クラス

2,000（芝）定量

16時00分


"""

def extract_date(text):
    date_match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
    if date_match:
        return f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"
    return None

def parse_jra_text(text):
    date_str = extract_date(text)
    if not date_str:
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

        # レース情報の抽出（改行を跨ぐデータに対応）
        pattern = r"(\d+)\s*レース\s*([\s\S]*?)\s*([\d,]+)（(芝|ダ).*?）([\s\S]*?)(\d+時\d+分)"
        matches = re.findall(pattern, chunk)

        for m in matches:
            # 取得した文字列の掃除
            condition_raw = m[1].replace("\n", " ").strip()
            # 「中山金杯（GⅢ）」のように名称がある場合、条件名と分離する
            # 連続する空白で区切られていることが多い
            parts = re.split(r'\s{2,}', condition_raw)
            race_name = parts[0] if len(parts) > 0 else condition_raw
            
            distance = m[2].replace(",", "")
            surface = "芝" if "芝" in m[3] else "ダート"
            extra_raw = m[4].replace("\n", " ").strip()

            gender = "牝馬限定" if "（牝）" in condition_raw or "（牝）" in extra_raw else ""
            
            weight = ""
            for w in ["ハンデ", "定量", "別定", "馬齢"]:
                if w in extra_raw or w in condition_raw:
                    weight = w
                    break

            race_class = "その他"
            if any(x in condition_raw for x in ["GⅢ", "G3"]): race_class = "G3"
            elif any(x in condition_raw for x in ["GⅡ", "G2"]): race_class = "G2"
            elif any(x in condition_raw for x in ["GⅠ", "G1"]): race_class = "G1"
            elif "オープン" in condition_raw: race_class = "OP"
            elif "3勝" in condition_raw: race_class = "3勝"
            elif "2勝" in condition_raw: race_class = "2勝"
            elif "1勝" in condition_raw: race_class = "1勝"
            elif "未勝利" in condition_raw: race_class = "未勝利"
            elif "新馬" in condition_raw: race_class = "新馬"

            races.append({
                "date": date_str,
                "location": current_location,
                "race_name": race_name,
                "class": race_class,
                "distance": int(distance),
                "surface": surface,
                "gender": gender,
                "weight_type": weight
            })

    return pd.DataFrame(races)

if __name__ == "__main__":
    df_new = parse_jra_text(raw_text)
    
    if not df_new.empty:
        output_path = "data/race_data.csv"
        os.makedirs("data", exist_ok=True)

        # すでにCSVが存在する場合
        if os.path.exists(output_path):
            # 1. 既存のデータを読み込む
            df_old = pd.read_csv(output_path)
            
            # 2. 新しいデータを結合する
            df_combined = pd.concat([df_old, df_new], ignore_index=True)
            
            # 3. 重複したレースを削除する（日付、場所、名前、距離、馬場が一致する場合）
            # これにより、同じテキストを2回実行してもデータが増えすぎません
            df_combined = df_combined.drop_duplicates(
                subset=["date", "location", "race_name", "distance", "surface"],
                keep='last' # 重複した場合は、新しく抽出した方を優先する
            )
            
            # 4. 保存
            df_combined.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"データを更新しました。現在の合計: {len(df_combined)} 件")
            
        else:
            # CSVが存在しない場合は新規作成
            df_new.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"新規作成しました。登録件数: {len(df_new)} 件")
    else:
        print("追加するデータが見つかりませんでした。")