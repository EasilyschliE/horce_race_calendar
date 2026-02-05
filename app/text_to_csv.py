import re
import pandas as pd
import os

# JRAの番組表テキストをここに貼り付け
raw_text = """
2026年1月4日（日曜）　競馬番組
表内の略称 戻る
日曜日の競馬番組
月曜日の競馬番組
このページの情報は、事前に発表した春季・夏季・秋季の各競馬番組の内容（予定）です。最新の情報は、通常木曜日16時頃に発表する「競馬メニュー」の「出馬表」でご確認ください。

注記：	当該週の出馬投票の結果や当日の天候によって、レース番号（レース順序）、馬場、距離、発走時刻などの変更や、レースの中止・延期といった追加・変更情報が発生する場合があります。
1回中山1日
レース
番号
レース名・条件	発走時刻
1
レース
3歳未勝利

1,200（ダ）（牝）

10時05分
2
レース
3歳未勝利

1,800（ダ）

10時35分
3
レース
3歳新馬

1,200（ダ）

11時05分
4
レース
3歳未勝利

1,800（ダ）

11時35分
5
レース
3歳未勝利

1,600（芝・外）

12時25分
6
レース
3歳新馬

2,000（芝）

12時55分
7
レース
4歳以上1勝クラス

1,800（ダ）定量

13時25分
8
レース
4歳以上1勝クラス

1,200（ダ）（牝）定量

13時55分
9
レース
招福ステークス

4歳以上3勝クラス

1,800（ダ）定量

14時30分
10
レース
ジュニアカップ（L）

3歳オープン

1,600（芝・外）別定

15時05分
11
レース
第75回 日刊スポーツ賞
中山金杯（GⅢ）

4歳以上オープン

2,000（芝）ハンデ

15時45分
12
レース
4歳以上2勝クラス

1,200（ダ）定量

16時25分
 
1回京都1日
レース
番号
レース名・条件	発走時刻
1
レース
3歳未勝利

1,200（ダ）

9時50分
2
レース
3歳未勝利

1,800（ダ）

10時20分
3
レース
3歳未勝利

1,400（ダ）

10時50分
4
レース
3歳新馬

1,800（ダ）

11時20分
5
レース
3歳新馬

1,800（芝・外）

12時10分
6
レース
3歳1勝クラス

2,000（芝）

12時40分
7
レース
4歳以上1勝クラス

1,800（ダ）（牝）定量

13時10分
8
レース
4歳以上1勝クラス

1,200（ダ）定量

13時40分
9
レース
天ケ瀬特別

4歳以上2勝クラス

1,800（ダ）定量

14時15分
10
レース
寿ステークス

4歳以上3勝クラス

2,000（芝）定量

14時50分
11
レース
第64回 スポーツニッポン賞
京都金杯（GⅢ）

4歳以上オープン

1,600（芝・外）ハンデ

15時30分
12
レース
4歳以上2勝クラス

1,400（芝・外）定量

16時10分
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

            gender = "牝馬限定" if "（牝）" in condition_raw or "（牝）" in extra_raw else "混合"
            
            weight = "不明"
            for w in ["ハンデ", "定量", "別定", "馬齢"]:
                if w in extra_raw or w in condition_raw:
                    weight = w
                    break

            race_class = "その他"
            if any(x in condition_raw for x in ["GⅢ", "G3"]): race_class = "G3"
            elif "3勝" in condition_raw: race_class = "3勝"
            elif "2勝" in condition_raw: race_class = "2勝"
            elif "1勝" in condition_raw: race_class = "1勝"
            elif "オープン" in condition_raw: race_class = "OP"
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
        # 新規作成（既存は上書きまたは削除済み想定）
        df_new.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"成功: {len(df_new)}件を新規登録しました。")