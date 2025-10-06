# src/sheets/writer.py

import gspread
from typing import Dict, List

def get_header_row() -> List[str]:
    """スプレッドシートに書き込むヘッダー行のリストを返します。"""
    return [
        # メタデータ
        "区名", "学校名", "学校フォルダURL", "PDFファイルURL",
        
        # 要約
        "要約_簡潔な説明", "要約_ルールカテゴリ",
        
        # 一般
        "見直しプロセス_規定", "見直しプロセス_根拠",
        
        # 制服
        "標準服_指定", "標準服_根拠",
        "標準服_タイプ", "標準服_タイプ_根拠",
        "LGBTQへの配慮", "LGBTQへの配慮_根拠",
        "衣替え移行期間", "衣替え移行期間_根拠",
        "体操服登校", "体操服登校_根拠",
        
        # 衣類項目 - シャツ・ブラウス
        "シャツ・ブラウス_色指定", "シャツ・ブラウス_色指定_根拠",
        "シャツ・ブラウス_着用方法_指定", "シャツ・ブラウス_着用方法_詳細", "シャツ・ブラウス_着用方法_根拠",
        "シャツ腕まくり禁止", "シャツ腕まくり禁止_根拠",
        
        # 衣類項目 - 下着
        "下着_着用義務", "下着_着用義務_根拠",
        "下着_色指定", "下着_色指定_根拠",
        "下着_柄指定", "下着_柄指定_根拠",
        
        # 衣類項目 - スラックス・スカート
        "スラックス・スカート_丈の指定", "スラックス・スカート_丈の指定_根拠",
        "ベルト_着用義務", "ベルト_着用義務_根拠",
        "ベルト_色指定", "ベルト_色指定_根拠",
        "ベルト_デザイン指定", "ベルト_デザイン指定_根拠",
        
        # 衣類項目 - タイツ
        "タイツ_着用禁止", "タイツ_着用禁止_根拠",
        "タイツ_色指定", "タイツ_色指定_根拠",
        
        # 衣類項目 - 防寒着(屋内)
        "防寒着(屋内)_色指定", "防寒着(屋内)_色指定_根拠",
        "防寒着(屋内)_種類制限", "防寒着(屋内)_種類制限_根拠",
        "防寒着(屋内)_柄指定", "防寒着(屋内)_柄指定_根拠",
        "カーディガン_着用禁止", "カーディガン_着用禁止_根拠",
        "トレーナー_着用禁止", "トレーナー_着用禁止_根拠",
        
        # 衣類項目 - 防寒着(屋外)
        "防寒着(屋外)_学校指定", "防寒着(屋外)_学校指定_根拠",
        "防寒着(屋外)_色指定", "防寒着(屋外)_色指定_根拠",
        "防寒着(屋外)_デザイン指定", "防寒着(屋外)_デザイン指定_根拠",
        
        # 衣類項目 - その他
        "マフラー・手袋_着用", "マフラー・手袋_着用_根拠",
        "耳あて_使用禁止", "耳あて_使用禁止_根拠",
        "靴下_デザイン指定", "靴下_デザイン指定_根拠",
        "靴下_長さ指定", "靴下_長さ指定_根拠",
        
        # 外見 - 頭髪
        "頭髪_男女別の長さ指定", "頭髪_男女別の長さ指定_根拠",
        "頭髪_男女別ルール", "頭髪_男女別ルール_根拠",
        "頭髪_前髪・襟足の長さ指定", "頭髪_前髪・襟足の長さ指定_根拠",
        "前髪_指定", "前髪_指定_詳細", "前髪_指定_根拠",
        "頭髪_結束義務", "頭髪_結束義務_根拠",
        "肩にかかったら結ぶ義務", "肩にかかったら結ぶ義務_根拠",
        "頭髪_禁止の髪型・加工", "頭髪_禁止の髪型・加工_項目", "頭髪_禁止の髪型・加工_根拠",
        "流行の髪型禁止", "流行の髪型禁止_根拠",
        "頭髪_抽象的な表現での指定", "頭髪_抽象的な表現での指定_根拠",
        "髪飾り_指定", "髪飾り_指定_詳細", "髪飾り_指定_根拠",
        "髪ゴム_色指定", "髪ゴム_色指定_根拠",
        "アメリカピン_使用禁止", "アメリカピン_使用禁止_根拠",
        "整髪料_使用禁止", "整髪料_使用禁止_根拠",
        
        # 外見 - 顔
        "化粧禁止", "化粧禁止_根拠",
        "眉毛加工の禁止", "眉毛加工の禁止_根拠",
        "色付きリップ_使用禁止", "色付きリップ_使用禁止_根拠",
        
        # 外見 - 検査
        "頭髪検査", "頭髪検査_根拠",
        
        # 持ち物 - 通学カバン
        "通学カバン_学校指定", "通学カバン_学校指定_根拠",
        "通学カバン_デザイン指定", "通学カバン_デザイン指定_根拠",
        "通学カバン_アクセサリー制限", "通学カバン_アクセサリー制限_根拠",
        "キーホルダー_指定", "キーホルダー_指定_根拠",
        
        # 持ち物 - ケア用品
        "ケア用品_持ち込み", "ケア用品_持ち込み_根拠",
        "特定用品の持ち込み制限", "特定用品の持ち込み制限_根拠",
        "制汗剤_使用禁止", "制汗剤_使用禁止_根拠",
        "香り付きケア用品_使用禁止", "香り付きケア用品_使用禁止_根拠",
        
        # 持ち物 - 水筒
        "水筒_規制", "水筒_規制_根拠",
        "水筒_中身指定", "水筒_中身指定_詳細", "水筒_中身指定_根拠",
        
        # 持ち物 - 時計
        "腕時計_着用禁止", "腕時計_着用禁止_根拠",
        "スマートウォッチ_着用禁止", "スマートウォッチ_着用禁止_根拠",
        
        # 持ち物 - スマートフォン
        "スマートフォン_持ち込み禁止", "スマートフォン_持ち込み禁止_根拠",
        "スマートフォン_条件付き許可", "スマートフォン_条件", "スマートフォン_条件付き許可_根拠",
        
        # 持ち物 - 漫画
        "漫画_持ち込み禁止", "漫画_持ち込み禁止_根拠",
        
        # 学校生活
        "5分前着席", "5分前着席_根拠",
        "他クラス立ち入り禁止", "他クラス立ち入り禁止_根拠",
        
        # 学校外生活
        "寄り道禁止", "寄り道禁止_根拠",
        "買い食い禁止", "買い食い禁止_根拠",
        "特定施設への立ち入り禁止", "特定施設への立ち入り禁止_詳細", "特定施設への立ち入り禁止_根拠",
        "公共の場での集まり禁止", "公共の場での集まり禁止_根拠",
        "友達外泊禁止", "友達外泊禁止_根拠",
        "SNS規制", "SNS規制_根拠",
        "SNS21時以降禁止", "SNS21時以降禁止_根拠",
        
        # 家庭での責任
        "家の手伝い指示", "家の手伝い指示_根拠"
    ]

def convert_json_to_row(data: Dict) -> List:
    """
    ネストされたJSONデータをスプレッドシートの1行に対応するリストに変換します。
    get_header_row()の順序と一致させる必要があります。
    """
    # 各項目を安全に取得するためのヘルパー関数
    def _get(d, *keys, default=""):
        for key in keys:
            if isinstance(d, dict):
                d = d.get(key)
            else:
                return default
        # dがNoneの場合もdefault値を返すように修正
        return d if d is not None else default

    row = [
        # メタデータ
        _get(data, "_metadata", "ward"),
        _get(data, "_metadata", "school"),
        _get(data, "_metadata", "school_folder_url"),
        _get(data, "_metadata", "web_view_link"),
        
        # 要約
        _get(data, "summary", "brief_description"),
        _get(data, "summary", "rule_categories"),
        
        # 一般
        _get(data, "general", "revision_process", "status"),
        _get(data, "general", "revision_process", "evidence"),
        
        # 制服
        _get(data, "uniform", "standard_uniform", "status"),
        _get(data, "uniform", "standard_uniform", "evidence"),
        _get(data, "uniform", "uniform_type", "status"),
        _get(data, "uniform", "uniform_type", "evidence"),
        _get(data, "uniform", "lgbtq_consideration", "status"),
        _get(data, "uniform", "lgbtq_consideration", "evidence"),
        _get(data, "uniform", "seasonal_transition_period", "status"),
        _get(data, "uniform", "seasonal_transition_period", "evidence"),
        _get(data, "uniform", "gym_wear_commuting", "status"),
        _get(data, "uniform", "gym_wear_commuting", "evidence"),
        
        # 衣類項目 - シャツ・ブラウス
        _get(data, "clothing_items", "shirts_blouses", "color_specification", "status"),
        _get(data, "clothing_items", "shirts_blouses", "color_specification", "evidence"),
        _get(data, "clothing_items", "shirts_blouses", "wearing_method", "status"),
        _get(data, "clothing_items", "shirts_blouses", "wearing_method", "details"),
        _get(data, "clothing_items", "shirts_blouses", "wearing_method", "evidence"),
        _get(data, "clothing_items", "shirts_blouses", "sleeves_rolling_prohibition", "status"),
        _get(data, "clothing_items", "shirts_blouses", "sleeves_rolling_prohibition", "evidence"),
        
        # 衣類項目 - 下着
        _get(data, "clothing_items", "underwear", "obligation_to_wear", "status"),
        _get(data, "clothing_items", "underwear", "obligation_to_wear", "evidence"),
        _get(data, "clothing_items", "underwear", "color_specification", "status"),
        _get(data, "clothing_items", "underwear", "color_specification", "evidence"),
        _get(data, "clothing_items", "underwear", "pattern_specification", "status"),
        _get(data, "clothing_items", "underwear", "pattern_specification", "evidence"),
        
        # 衣類項目 - スラックス・スカート
        _get(data, "clothing_items", "slacks_skirts", "length_specification", "status"),
        _get(data, "clothing_items", "slacks_skirts", "length_specification", "evidence"),
        _get(data, "clothing_items", "slacks_skirts", "belt_obligation", "status"),
        _get(data, "clothing_items", "slacks_skirts", "belt_obligation", "evidence"),
        _get(data, "clothing_items", "slacks_skirts", "belt_color_specification", "status"),
        _get(data, "clothing_items", "slacks_skirts", "belt_color_specification", "evidence"),
        _get(data, "clothing_items", "slacks_skirts", "belt_design_specification", "status"),
        _get(data, "clothing_items", "slacks_skirts", "belt_design_specification", "evidence"),
        
        # 衣類項目 - タイツ
        _get(data, "clothing_items", "tights", "wearing_prohibition", "status"),
        _get(data, "clothing_items", "tights", "wearing_prohibition", "evidence"),
        _get(data, "clothing_items", "tights", "color_specification", "status"),
        _get(data, "clothing_items", "tights", "color_specification", "evidence"),
        
        # 衣類項目 - 防寒着(屋内)
        _get(data, "clothing_items", "indoor_outerwear", "color_specification", "status"),
        _get(data, "clothing_items", "indoor_outerwear", "color_specification", "evidence"),
        _get(data, "clothing_items", "indoor_outerwear", "type_restriction", "status"),
        _get(data, "clothing_items", "indoor_outerwear", "type_restriction", "evidence"),
        _get(data, "clothing_items", "indoor_outerwear", "pattern_specification", "status"),
        _get(data, "clothing_items", "indoor_outerwear", "pattern_specification", "evidence"),
        _get(data, "clothing_items", "indoor_outerwear", "cardigan_prohibition", "status"),
        _get(data, "clothing_items", "indoor_outerwear", "cardigan_prohibition", "evidence"),
        _get(data, "clothing_items", "indoor_outerwear", "sweatshirt_prohibition", "status"),
        _get(data, "clothing_items", "indoor_outerwear", "sweatshirt_prohibition", "evidence"),
        
        # 衣類項目 - 防寒着(屋外)
        _get(data, "clothing_items", "outdoor_outerwear", "school_designated", "status"),
        _get(data, "clothing_items", "outdoor_outerwear", "school_designated", "evidence"),
        _get(data, "clothing_items", "outdoor_outerwear", "color_specification", "status"),
        _get(data, "clothing_items", "outdoor_outerwear", "color_specification", "evidence"),
        _get(data, "clothing_items", "outdoor_outerwear", "design_specification", "status"),
        _get(data, "clothing_items", "outdoor_outerwear", "design_specification", "evidence"),
        
        # 衣類項目 - その他
        _get(data, "clothing_items", "scarves_gloves", "status"),
        _get(data, "clothing_items", "scarves_gloves", "evidence"),
        _get(data, "clothing_items", "ear_muffs", "status"),
        _get(data, "clothing_items", "ear_muffs", "evidence"),
        _get(data, "clothing_items", "socks", "design_specification", "status"),
        _get(data, "clothing_items", "socks", "design_specification", "evidence"),
        _get(data, "clothing_items", "socks", "length_specification", "status"),
        _get(data, "clothing_items", "socks", "length_specification", "evidence"),
        
        # 外見 - 頭髪
        _get(data, "appearance", "hair", "gender_specific_length", "status"),
        _get(data, "appearance", "hair", "gender_specific_length", "evidence"),
        _get(data, "appearance", "hair", "gender_specific_rules", "status"),
        _get(data, "appearance", "hair", "gender_specific_rules", "evidence"),
        _get(data, "appearance", "hair", "fringe_neck_length", "status"),
        _get(data, "appearance", "hair", "fringe_neck_length", "evidence"),
        _get(data, "appearance", "hair", "fringe_specification", "status"),
        _get(data, "appearance", "hair", "fringe_specification", "details"),
        _get(data, "appearance", "hair", "fringe_specification", "evidence"),
        _get(data, "appearance", "hair", "tying_obligation", "status"),
        _get(data, "appearance", "hair", "tying_obligation", "evidence"),
        _get(data, "appearance", "hair", "shoulder_length_tying", "status"),
        _get(data, "appearance", "hair", "shoulder_length_tying", "evidence"),
        _get(data, "appearance", "hair", "prohibited_styles_modifications", "status"),
        ", ".join(_get(data, "appearance", "hair", "prohibited_styles_modifications", "items", default=[])),
        _get(data, "appearance", "hair", "prohibited_styles_modifications", "evidence"),
        _get(data, "appearance", "hair", "trendy_hairstyle_prohibition", "status"),
        _get(data, "appearance", "hair", "trendy_hairstyle_prohibition", "evidence"),
        _get(data, "appearance", "hair", "abstract_expressions", "status"),
        _get(data, "appearance", "hair", "abstract_expressions", "evidence"),
        _get(data, "appearance", "hair", "hair_accessories", "status"),
        _get(data, "appearance", "hair", "hair_accessories", "details"),
        _get(data, "appearance", "hair", "hair_accessories", "evidence"),
        _get(data, "appearance", "hair", "hair_tie_color", "status"),
        _get(data, "appearance", "hair", "hair_tie_color", "evidence"),
        _get(data, "appearance", "hair", "bobby_pin_prohibition", "status"),
        _get(data, "appearance", "hair", "bobby_pin_prohibition", "evidence"),
        _get(data, "appearance", "hair", "hair_styling_product_prohibition", "status"),
        _get(data, "appearance", "hair", "hair_styling_product_prohibition", "evidence"),
        
        # 外見 - 顔
        _get(data, "appearance", "face", "makeup_prohibition", "status"),
        _get(data, "appearance", "face", "makeup_prohibition", "evidence"),
        _get(data, "appearance", "face", "eyebrow_modification_prohibition", "status"),
        _get(data, "appearance", "face", "eyebrow_modification_prohibition", "evidence"),
        _get(data, "appearance", "face", "tinted_lip_balm_prohibition", "status"),
        _get(data, "appearance", "face", "tinted_lip_balm_prohibition", "evidence"),
        
        # 外見 - 検査
        _get(data, "appearance", "inspections", "hair_inspection", "status"),
        _get(data, "appearance", "inspections", "hair_inspection", "evidence"),
        
        # 持ち物 - 通学カバン
        _get(data, "belongings", "school_bag", "school_designated", "status"),
        _get(data, "belongings", "school_bag", "school_designated", "evidence"),
        _get(data, "belongings", "school_bag", "design_specification", "status"),
        _get(data, "belongings", "school_bag", "design_specification", "evidence"),
        _get(data, "belongings", "school_bag", "accessory_restriction", "status"),
        _get(data, "belongings", "school_bag", "accessory_restriction", "evidence"),
        _get(data, "belongings", "school_bag", "keychain_specification", "status"),
        _get(data, "belongings", "school_bag", "keychain_specification", "evidence"),
        
        # 持ち物 - ケア用品
        _get(data, "belongings", "care_products", "carrying_prohibited", "status"),
        _get(data, "belongings", "care_products", "carrying_prohibited", "evidence"),
        _get(data, "belongings", "care_products", "specific_item_restriction", "status"),
        _get(data, "belongings", "care_products", "specific_item_restriction", "evidence"),
        _get(data, "belongings", "care_products", "deodorant_prohibition", "status"),
        _get(data, "belongings", "care_products", "deodorant_prohibition", "evidence"),
        _get(data, "belongings", "care_products", "scented_products_prohibition", "status"),
        _get(data, "belongings", "care_products", "scented_products_prohibition", "evidence"),
        
        # 持ち物 - 水筒
        _get(data, "belongings", "water_bottle", "regulation", "status"),
        _get(data, "belongings", "water_bottle", "regulation", "evidence"),
        _get(data, "belongings", "water_bottle", "content_specification", "status"),
        _get(data, "belongings", "water_bottle", "content_specification", "details"),
        _get(data, "belongings", "water_bottle", "content_specification", "evidence"),
        
        # 持ち物 - 時計
        _get(data, "belongings", "watch", "analog_watch_prohibition", "status"),
        _get(data, "belongings", "watch", "analog_watch_prohibition", "evidence"),
        _get(data, "belongings", "watch", "smart_watch_prohibition", "status"),
        _get(data, "belongings", "watch", "smart_watch_prohibition", "evidence"),
        
        # 持ち物 - スマートフォン
        _get(data, "belongings", "smartphone", "bringing_prohibition", "status"),
        _get(data, "belongings", "smartphone", "bringing_prohibition", "evidence"),
        _get(data, "belongings", "smartphone", "conditional_permission", "status"),
        _get(data, "belongings", "smartphone", "conditional_permission", "conditions"),
        _get(data, "belongings", "smartphone", "conditional_permission", "evidence"),
        
        # 持ち物 - 漫画
        _get(data, "belongings", "comics_magazines", "bringing_prohibition", "status"),
        _get(data, "belongings", "comics_magazines", "bringing_prohibition", "evidence"),
        
        # 学校生活
        _get(data, "school_life", "punctuality", "five_minutes_before_seating", "status"),
        _get(data, "school_life", "punctuality", "five_minutes_before_seating", "evidence"),
        _get(data, "school_life", "classroom_access", "other_class_entry_prohibition", "status"),
        _get(data, "school_life", "classroom_access", "other_class_entry_prohibition", "evidence"),
        
        # 学校外生活
        _get(data, "school_life_outside", "loitering_prohibition", "status"),
        _get(data, "school_life_outside", "loitering_prohibition", "evidence"),
        _get(data, "school_life_outside", "buying_food_prohibition", "status"),
        _get(data, "school_life_outside", "buying_food_prohibition", "evidence"),
        _get(data, "school_life_outside", "facility_entry_prohibition", "status"),
        _get(data, "school_life_outside", "facility_entry_prohibition", "details"),
        _get(data, "school_life_outside", "facility_entry_prohibition", "evidence"),
        _get(data, "school_life_outside", "gathering_in_public_prohibition", "status"),
        _get(data, "school_life_outside", "gathering_in_public_prohibition", "evidence"),
        _get(data, "school_life_outside", "sleepover_prohibition", "status"),
        _get(data, "school_life_outside", "sleepover_prohibition", "evidence"),
        _get(data, "school_life_outside", "sns_regulation", "status"),
        _get(data, "school_life_outside", "sns_regulation", "evidence"),
        _get(data, "school_life_outside", "sns_time_restriction", "status"),
        _get(data, "school_life_outside", "sns_time_restriction", "evidence"),
        
        # 家庭での責任
        _get(data, "family_responsibilities", "household_chores_instruction", "status"),
        _get(data, "family_responsibilities", "household_chores_instruction", "evidence"),
    ]
    return row

def write_data(worksheet: gspread.Worksheet, json_data: Dict) -> bool:
    """
    gspread.WorksheetオブジェクトとJSONデータを受け取り、スプレッドシートに追記します。
    シートが空の場合は、ヘッダー行を先に追加します。

    Args:
        worksheet (gspread.Worksheet): 書き込み対象のワークシートオブジェクト。
        json_data (Dict): 書き込むJSONデータ（辞書形式）。

    Returns:
        bool: 書き込みが成功した場合はTrue、失敗した場合はFalse。
    """
    if not isinstance(worksheet, gspread.Worksheet):
        print("エラー: 有効なワークシートオブジェクトが渡されませんでした。")
        return False

    try:
        # シートが空かどうかを確認 (A1セルが空なら空とみなす)
        if worksheet.acell('A1').value is None:
            header_row = get_header_row()
            worksheet.append_row(header_row, value_input_option='USER_ENTERED')
            print(f"シート '{worksheet.title}' にヘッダー行を書き込みました。")

        # JSONデータをリスト形式に変換
        row_to_insert = convert_json_to_row(json_data)

        # データをスプレッドシートに追記
        worksheet.append_row(row_to_insert, value_input_option='USER_ENTERED')
        print(f"シート '{worksheet.title}' にデータを1行書き込みました。")
        return True

    except gspread.exceptions.APIError as e:
        print(f"エラー: スプレッドシートへの書き込み中にAPIエラーが発生しました: {e}")
        return False
    except Exception as e:
        print(f"エラー: 予期せぬエラーが発生しました: {e}")
        return False

