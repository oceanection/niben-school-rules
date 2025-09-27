# src/sheets/writer.py

import gspread
from typing import Dict, List

def get_header_row() -> List[str]:
    """スプレッドシートに書き込むヘッダー行のリストを返します。"""
    return [
        "見直しプロセス_規定", "見直しプロセス_根拠", "標準服_指定", "標準服_根拠",
        "LGBTQへの配慮", "LGBTQへの配慮_根拠", "衣替え移行期間", "衣替え移行期間_根拠",
        "シャツ・ブラウス_色指定", "シャツ・ブラウス_色指定_根拠", "シャツ・ブラウス_着用方法_指定",
        "シャツ・ブラウス_着用方法_詳細", "シャツ・ブラウス_着用方法_根拠", "下着_着用義務",
        "下着_着用義務_根拠", "下着_色指定", "下着_色指定_根拠", "下着_柄指定", "下着_柄指定_根拠",
        "スラックス・スカート_丈の指定", "スラックス・スカート_丈の指定_根拠", "ベルト_着用義務",
        "ベルト_着用義務_根拠", "ベルト_色指定", "ベルト_色指定_根拠", "ベルト_デザイン指定",
        "ベルト_デザイン指定_根拠", "防寒着(屋内)_色指定", "防寒着(屋内)_色指定_根拠",
        "防寒着(屋内)_種類制限", "防寒着(屋内)_種類制限_根拠", "防寒着(屋内)_柄指定",
        "防寒着(屋内)_柄指定_根拠", "防寒着(屋外)_学校指定", "防寒着(屋外)_学校指定_根拠",
        "防寒着(屋外)_色指定", "防寒着(屋外)_色指定_根拠", "防寒着(屋外)_デザイン指定",
        "防寒着(屋外)_デザイン指定_根拠", "マフラー・手袋_着用", "マフラー・手袋_着用_根拠",
        "靴下_デザイン指定", "靴下_デザイン指定_根拠", "靴下_長さ指定", "靴下_長さ指定_根拠",
        "頭髪_男女別の長さ指定", "頭髪_男女別の長さ指定_根拠", "頭髪_前髪・襟足の長さ指定",
        "頭髪_前髪・襟足の長さ指定_根拠", "頭髪_結束義務", "頭髪_結束義務_根拠", "頭髪_禁止の髪型・加工",
        "頭髪_禁止の髪型・加工_項目", "頭髪_禁止の髪型・加工_根拠", "頭髪_抽象的な表現での指定",
        "頭髪_抽象的な表現での指定_根拠", "髪飾り_指定", "髪飾り_指定_詳細", "髪飾り_指定_根拠",
        "化粧禁止", "化粧禁止_根拠", "眉毛加工の禁止", "眉毛加工の禁止_根拠", "頭髪検査", "頭髪検査_根拠",
        "通学カバン_学校指定", "通学カバン_学校指定_根拠", "通学カバン_デザイン指定",
        "通学カバン_デザイン指定_根拠", "通学カバン_アクセサリー制限", "通学カバン_アクセサリー制限_根拠",
        "ケア用品_持ち込み", "ケア用品_持ち込み_根拠", "特定用品の持ち込み制限",
        "特定用品の持ち込み制限_根拠", "寄り道禁止", "寄り道禁止_根拠", "特定施設への立ち入り禁止",
        "特定施設への立ち入り禁止_詳細", "特定施設への立ち入り禁止_根拠", "公共の場での集まり禁止",
        "公共の場での集まり禁止_根拠"
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
        _get(data, "general", "revision_process", "status"),
        _get(data, "general", "revision_process", "evidence"),
        _get(data, "uniform", "standard_uniform", "status"),
        _get(data, "uniform", "standard_uniform", "evidence"),
        _get(data, "uniform", "lgbtq_consideration", "status"),
        _get(data, "uniform", "lgbtq_consideration", "evidence"),
        _get(data, "uniform", "seasonal_transition_period", "status"),
        _get(data, "uniform", "seasonal_transition_period", "evidence"),
        _get(data, "clothing_items", "shirts_blouses", "color_specification", "status"),
        _get(data, "clothing_items", "shirts_blouses", "color_specification", "evidence"),
        _get(data, "clothing_items", "shirts_blouses", "wearing_method", "status"),
        _get(data, "clothing_items", "shirts_blouses", "wearing_method", "details"),
        _get(data, "clothing_items", "shirts_blouses", "wearing_method", "evidence"),
        _get(data, "clothing_items", "underwear", "obligation_to_wear", "status"),
        _get(data, "clothing_items", "underwear", "obligation_to_wear", "evidence"),
        _get(data, "clothing_items", "underwear", "color_specification", "status"),
        _get(data, "clothing_items", "underwear", "color_specification", "evidence"),
        _get(data, "clothing_items", "underwear", "pattern_specification", "status"),
        _get(data, "clothing_items", "underwear", "pattern_specification", "evidence"),
        _get(data, "clothing_items", "slacks_skirts", "length_specification", "status"),
        _get(data, "clothing_items", "slacks_skirts", "length_specification", "evidence"),
        _get(data, "clothing_items", "slacks_skirts", "belt_obligation", "status"),
        _get(data, "clothing_items", "slacks_skirts", "belt_obligation", "evidence"),
        _get(data, "clothing_items", "slacks_skirts", "belt_color_specification", "status"),
        _get(data, "clothing_items", "slacks_skirts", "belt_color_specification", "evidence"),
        _get(data, "clothing_items", "slacks_skirts", "belt_design_specification", "status"),
        _get(data, "clothing_items", "slacks_skirts", "belt_design_specification", "evidence"),
        _get(data, "clothing_items", "indoor_outerwear", "color_specification", "status"),
        _get(data, "clothing_items", "indoor_outerwear", "color_specification", "evidence"),
        _get(data, "clothing_items", "indoor_outerwear", "type_restriction", "status"),
        _get(data, "clothing_items", "indoor_outerwear", "type_restriction", "evidence"),
        _get(data, "clothing_items", "indoor_outerwear", "pattern_specification", "status"),
        _get(data, "clothing_items", "indoor_outerwear", "pattern_specification", "evidence"),
        _get(data, "clothing_items", "outdoor_outerwear", "school_designated", "status"),
        _get(data, "clothing_items", "outdoor_outerwear", "school_designated", "evidence"),
        _get(data, "clothing_items", "outdoor_outerwear", "color_specification", "status"),
        _get(data, "clothing_items", "outdoor_outerwear", "color_specification", "evidence"),
        _get(data, "clothing_items", "outdoor_outerwear", "design_specification", "status"),
        _get(data, "clothing_items", "outdoor_outerwear", "design_specification", "evidence"),
        _get(data, "clothing_items", "scarves_gloves", "status"),
        _get(data, "clothing_items", "scarves_gloves", "evidence"),
        _get(data, "clothing_items", "socks", "design_specification", "status"),
        _get(data, "clothing_items", "socks", "design_specification", "evidence"),
        _get(data, "clothing_items", "socks", "length_specification", "status"),
        _get(data, "clothing_items", "socks", "length_specification", "evidence"),
        _get(data, "appearance", "hair", "gender_specific_length", "status"),
        _get(data, "appearance", "hair", "gender_specific_length", "evidence"),
        _get(data, "appearance", "hair", "fringe_neck_length", "status"),
        _get(data, "appearance", "hair", "fringe_neck_length", "evidence"),
        _get(data, "appearance", "hair", "tying_obligation", "status"),
        _get(data, "appearance", "hair", "tying_obligation", "evidence"),
        _get(data, "appearance", "hair", "prohibited_styles_modifications", "status"),
        ", ".join(_get(data, "appearance", "hair", "prohibited_styles_modifications", "items", default=[])),
        _get(data, "appearance", "hair", "prohibited_styles_modifications", "evidence"),
        _get(data, "appearance", "hair", "abstract_expressions", "status"),
        _get(data, "appearance", "hair", "abstract_expressions", "evidence"),
        _get(data, "appearance", "hair", "hair_accessories", "status"),
        _get(data, "appearance", "hair", "hair_accessories", "details"),
        _get(data, "appearance", "hair", "hair_accessories", "evidence"),
        _get(data, "appearance", "face", "makeup_prohibition", "status"),
        _get(data, "appearance", "face", "makeup_prohibition", "evidence"),
        _get(data, "appearance", "face", "eyebrow_modification_prohibition", "status"),
        _get(data, "appearance", "face", "eyebrow_modification_prohibition", "evidence"),
        _get(data, "appearance", "inspections", "hair_inspection", "status"),
        _get(data, "appearance", "inspections", "hair_inspection", "evidence"),
        _get(data, "belongings", "school_bag", "school_designated", "status"),
        _get(data, "belongings", "school_bag", "school_designated", "evidence"),
        _get(data, "belongings", "school_bag", "design_specification", "status"),
        _get(data, "belongings", "school_bag", "design_specification", "evidence"),
        _get(data, "belongings", "school_bag", "accessory_restriction", "status"),
        _get(data, "belongings", "school_bag", "accessory_restriction", "evidence"),
        _get(data, "belongings", "care_products", "carrying_prohibited", "status"),
        _get(data, "belongings", "care_products", "carrying_prohibited", "evidence"),
        _get(data, "belongings", "care_products", "specific_item_restriction", "status"),
        _get(data, "belongings", "care_products", "specific_item_restriction", "evidence"),
        _get(data, "school_life_outside", "loitering_prohibition", "status"),
        _get(data, "school_life_outside", "loitering_prohibition", "evidence"),
        _get(data, "school_life_outside", "facility_entry_prohibition", "status"),
        _get(data, "school_life_outside", "facility_entry_prohibition", "details"),
        _get(data, "school_life_outside", "facility_entry_prohibition", "evidence"),
        _get(data, "school_life_outside", "gathering_in_public_prohibition", "status"),
        _get(data, "school_life_outside", "gathering_in_public_prohibition", "evidence"),
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
        # get_all_values()よりも効率的
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


if __name__ == '__main__':
    # --- このスクリプトを直接実行した際のサンプルコード ---
    from config.settings import settings
    from src.sheets.client import SpreadsheetClient

    print("--- writer.pyのサンプル実行 ---")

    # 1. クライアントの準備
    client = SpreadsheetClient(settings.google_application_credentials)
    if not client.client:
        print("クライアントの初期化に失敗しました。")
    else:
        # 2. ワークシートの取得
        # .envに設定したシート名（例: integration_test_sheet）を取得
        worksheet = client.get_worksheet(settings.spreadsheet_id, settings.worksheet_name)

        if worksheet:
            print(f"ワークシート '{settings.worksheet_name}' を取得しました。")
            # 3. サンプルのJSONデータ
            sample_data = {
                "general": {
                    "revision_process": {
                        "status": "規定あり",
                        "evidence": "生徒手帳 p.1"
                    }
                },
                "uniform": {
                    "standard_uniform": {
                        "status": "指定あり",
                        "evidence": "入学案内"
                    },
                    "lgbtq_consideration": {
                        "status": "配慮あり",
                        "evidence": "制服選択制"
                    }
                },
                # ... 他のデータは省略 ...
            }

            # 4. 書き込み関数の実行
            success = write_data(worksheet, sample_data)
            if success:
                print("サンプルデータの書き込みに成功しました。")
            else:
                print("サンプルデータの書き込みに失敗しました。")
        else:
            print(f"ワークシート '{settings.worksheet_name}' の取得に失敗しました。")