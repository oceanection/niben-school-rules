# tests/sheets/test_writer_integration.py

import pytest
import datetime
import gspread
from src.config.settings import settings
from src.sheets.client import SpreadsheetClient
from src.sheets.writer import write_data, convert_json_to_row, get_header_row

# テストで使用する固定のシート名
TEST_WORKSHEET_NAME = "test"

@pytest.fixture(scope="module")
def client():
    """テスト用のSpreadsheetClientインスタンスを生成するフィクスチャ"""
    if not settings.google_application_credentials:
        pytest.fail("GOOGLE_APPLICATION_CREDENTIALSが設定されていません。")

    client_instance = SpreadsheetClient(settings.google_application_credentials)
    if not client_instance.client:
        pytest.fail("SpreadsheetClientの初期化に失敗しました。認証情報を確認してください。")

    return client_instance


def test_setup_and_get_worksheet(client: SpreadsheetClient):
    """
    client.pyの動作確認：
    "test"シートが存在することを確認し、なければ作成する。
    """
    print(f"\n--- ワークシート '{TEST_WORKSHEET_NAME}' の準備 ---")
    
    if not settings.spreadsheet_id:
        pytest.fail("SPREADSHEET_IDが設定されていません。")

    try:
        spreadsheet = client.client.open_by_key(settings.spreadsheet_id)
        # "test"シートの取得を試みる
        worksheet = spreadsheet.worksheet(TEST_WORKSHEET_NAME)
        print(f"✔ 既存のワークシート '{TEST_WORKSHEET_NAME}' を取得しました。")

    except gspread.exceptions.WorksheetNotFound:
        # シートが存在しない場合は新規作成
        print(f"ワークシート '{TEST_WORKSHEET_NAME}' が存在しないため、新規作成します。")
        worksheet = spreadsheet.add_worksheet(title=TEST_WORKSHEET_NAME, rows=100, cols=100)
        print(f"✔ ワークシート '{TEST_WORKSHEET_NAME}' を作成しました。")
    
    except Exception as e:
        pytest.fail(f"ワークシートの準備中に予期せぬエラーが発生しました: {e}")

    assert worksheet is not None, f"ワークシート '{TEST_WORKSHEET_NAME}' の準備に失敗しました。"


def test_write_to_sheet(client: SpreadsheetClient):
    """
    writer.pyの動作確認：
    "test"シートにサンプルデータを書き込み、正しく書き込まれたか検証する。
    """
    print(f"\n--- ワークシート '{TEST_WORKSHEET_NAME}' への書き込みテスト ---")
    
    # 1. 書き込み対象のワークシートを取得
    worksheet = client.get_worksheet(settings.spreadsheet_id, TEST_WORKSHEET_NAME)
    assert worksheet is not None, f"テストシート '{TEST_WORKSHEET_NAME}' の取得に失敗しました。"

    # 2. 書き込むサンプルJSONデータを作成
    timestamp = datetime.datetime.now().isoformat()
    sample_data = {
        "general": {
            "revision_process": { "status": "規定あり", "evidence": f"Test at {timestamp}" }
        },
        "uniform": {
            "lgbtq_consideration": { "status": "配慮あり", "evidence": "スラックス選択可" }
        },
        "appearance": {
            "hair": {
                "prohibited_styles_modifications": {
                    "status": "特定の髪型・加工の禁止あり",
                    "items": ["ツーブロック", "染色"],
                    "evidence": "生徒心得 p.3"
                }
            }
        },
    }

    # 3. writer.pyの関数を呼び出して書き込みを実行
    is_success = write_data(worksheet, sample_data)
    assert is_success is True, "write_data関数がFalseを返しました。"
    print("✔ write_data関数が正常に実行されました。")

    # 4. 書き込み結果の検証
    #    実際にスプレッドシートから最終行を読み出し、
    #    書き込もうとしたデータと一致するか確認する
    expected_row = convert_json_to_row(sample_data)
    
    # APIからデータを取得
    all_values = worksheet.get_all_values()
    
    # ヘッダー行が存在することを確認
    if all_values:
        header = get_header_row()
        assert all_values[0] == header, "ヘッダー行が正しく書き込まれていません。"

    # 書き込んだ最終行を取得
    last_row = all_values[-1]
    
    assert last_row == expected_row, f"書き込まれたデータが期待値と異なります。\n期待値: {expected_row}\n実際値: {last_row}"
    print("✔ 書き込まれた内容の検証に成功しました。")