 
# tests/sheets/test_client_integration.py

import pytest
import datetime
from src.config.settings import settings
from src.sheets.client import SpreadsheetClient

# pytestフィクスチャを定義し、テスト全体で再利用可能なクライアントオブジェクトを作成
@pytest.fixture(scope="module")
def client():
    """テスト用のSpreadsheetClientインスタンスを生成するフィクスチャ"""
    if not settings.google_application_credentials:
        pytest.fail("GOOGLE_APPLICATION_CREDENTIALSが設定されていません。")
    
    client_instance = SpreadsheetClient(settings.google_application_credentials)
    if not client_instance.client:
        pytest.fail("SpreadsheetClientの初期化に失敗しました。認証情報を確認してください。")
        
    return client_instance

def test_connection_and_get_worksheet(client: SpreadsheetClient):
    """
    APIへの接続とワークシートの取得をテストする。
    シートが存在しない場合は、正しくNoneが返されることも確認。
    """
    print("--- ワークシート取得テスト開始 ---")
    
    # まず、テスト実行前にシートを削除しておく（もしあれば）
    try:
        spreadsheet = client.client.open_by_key(settings.spreadsheet_id)
        worksheet_to_delete = spreadsheet.worksheet(settings.worksheet_name)
        spreadsheet.del_worksheet(worksheet_to_delete)
        print(f"既存のシート '{settings.worksheet_name}' を削除しました。")
    except (gspread.exceptions.SpreadsheetNotFound, gspread.exceptions.WorksheetNotFound):
        pass # シートが存在しない場合は何もしない

    # 1. 存在しないシートを取得しようとしてNoneが返ることを確認
    worksheet = client.get_worksheet(settings.spreadsheet_id, settings.worksheet_name)
    assert worksheet is None, "存在するはずのないシートが取得できてしまいました。"
    print("✔ 存在しないシートの取得テストに成功しました。")

    # 2. シートを新規作成
    spreadsheet = client.client.open_by_key(settings.spreadsheet_id)
    spreadsheet.add_worksheet(title=settings.worksheet_name, rows=10, cols=10)
    print(f"テスト用にシート '{settings.worksheet_name}' を新規作成しました。")
    
    # 3. 作成したシートが正しく取得できることを確認
    worksheet = client.get_worksheet(settings.spreadsheet_id, settings.worksheet_name)
    assert worksheet is not None, "シートを作成したにも関わらず取得できませんでした。"
    assert worksheet.title == settings.worksheet_name
    print("✔ 新規作成したシートの取得テストに成功しました。")
    print("--- ワークシート取得テスト完了 ---")


def test_write_read_delete_flow(client: SpreadsheetClient):
    """
    データの書き込み、読み取り、削除の一連の流れをテストする。
    このテストは `test_connection_and_get_worksheet` の後に実行される想定。
    """
    print("\n--- データ操作（書き込み・読み取り・削除）テスト開始 ---")
    
    worksheet = client.get_worksheet(settings.spreadsheet_id, settings.worksheet_name)
    assert worksheet is not None, "テストシートの取得に失敗しました。前のテストが成功しているか確認してください。"
    
    # 1. 書き込みテスト
    timestamp = datetime.datetime.now().isoformat()
    test_data = ["test_id_001", "integration_test", timestamp]
    
    try:
        worksheet.append_row(test_data)
        print(f"書き込み成功: {test_data}")
    except Exception as e:
        pytest.fail(f"データの書き込み中にエラーが発生しました: {e}")

    # 2. 読み取りテスト
    # 書き込んだ最終行を読み取って内容を検証
    last_row = worksheet.get_all_values()[-1]
    assert last_row == test_data, f"読み取ったデータが書き込んだデータと一致しません。\n書き込み: {test_data}\n読み取り: {last_row}"
    print(f"✔ 読み取り検証成功: {last_row}")

    # 3. クリーンアップ（テストで追加した行とシートを削除）
    spreadsheet = client.client.open_by_key(settings.spreadsheet_id)
    spreadsheet.del_worksheet(worksheet)
    print(f"✔ テストシート '{settings.worksheet_name}' を削除しました。")
    print("--- データ操作テスト完了 ---")