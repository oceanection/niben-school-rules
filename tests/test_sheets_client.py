"""
SpreadsheetClient の単体テスト

実際のGoogleスプレッドシート環境でのテストを実施
"""

import sys
from pathlib import Path
import pytest

# srcディレクトリをパスに追加
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from config.settings import settings
from sheets.client import SpreadsheetClient


class TestSpreadsheetClient:
    """SpreadsheetClient の単体テスト"""
    
    @classmethod
    def setup_class(cls):
        """テストクラスの初期化"""
        print(f"テスト開始:")
        print(f"  SPREADSHEET_ID: {settings.spreadsheet_id}")
        print(f"  WORKSHEET_NAME: {settings.worksheet_name}")
        print(f"  CREDENTIALS: {settings.google_application_credentials}")
        
        cls.client = SpreadsheetClient(settings.google_application_credentials)
    
    def test_client_initialization(self):
        """SpreadsheetClient の初期化テスト"""
        assert self.client is not None
        assert self.client.client is not None, "gspread クライアントの初期化に失敗"
        print("✓ SpreadsheetClient 初期化成功")
    
    def test_authentication(self):
        """Google Sheets API認証テスト"""
        assert settings.google_application_credentials is not None
        assert self.client.client is not None
        print("✓ Google Sheets API 認証成功")
    
    def test_get_worksheet(self):
        """ワークシート取得テスト"""
        worksheet = self.client.get_worksheet(
            settings.spreadsheet_id, 
            settings.worksheet_name
        )
        
        assert worksheet is not None, f"ワークシート '{settings.worksheet_name}' の取得に失敗"
        assert hasattr(worksheet, 'title'), "ワークシートオブジェクトが不正"
        
        print(f"✓ ワークシート取得成功: '{worksheet.title}'")
        print(f"  スプレッドシートURL: https://docs.google.com/spreadsheets/d/{settings.spreadsheet_id}")
        
        return worksheet
    
    def test_worksheet_basic_operations(self):
        """ワークシートの基本操作テスト"""
        worksheet = self.client.get_worksheet(
            settings.spreadsheet_id, 
            settings.worksheet_name
        )
        
        # A1セルの値を確認
        a1_value = worksheet.acell('A1').value
        print(f"A1セルの値: '{a1_value}'")
        
        # シートの基本情報を取得
        row_count = worksheet.row_count
        col_count = worksheet.col_count
        
        print(f"シート情報:")
        print(f"  行数: {row_count}")
        print(f"  列数: {col_count}")
        
        assert row_count > 0, "行数が0以下"
        assert col_count > 0, "列数が0以下"
        
        print("✓ ワークシート基本操作成功")
    
    def test_invalid_spreadsheet_id(self):
        """無効なスプレッドシートIDのテスト"""
        invalid_id = "invalid_spreadsheet_id_12345"
        
        worksheet = self.client.get_worksheet(invalid_id, settings.worksheet_name)
        
        assert worksheet is None, "無効なIDでもワークシートが取得されてしまった"
        print("✓ 無効なスプレッドシートID処理成功")
    
    def test_invalid_worksheet_name(self):
        """無効なワークシート名のテスト"""
        invalid_name = "存在しないシート名_12345"
        
        worksheet = self.client.get_worksheet(settings.spreadsheet_id, invalid_name)
        
        assert worksheet is None, "無効なシート名でもワークシートが取得されてしまった"
        print("✓ 無効なワークシート名処理成功")
    
    def test_permissions(self):
        """権限確認テスト"""
        worksheet = self.client.get_worksheet(
            settings.spreadsheet_id, 
            settings.worksheet_name
        )
        
        try:
            # 読み取り権限の確認
            all_values = worksheet.get_all_values()
            print(f"✓ 読み取り権限確認成功 (総セル数: {len(all_values)}行)")
            
            # 書き込み権限の確認（テスト用の簡単な書き込み）
            test_cell = f"テスト実行時刻: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 最後の行の次に書き込み（既存データを上書きしないように）
            last_row = len(all_values)
            next_row = last_row + 1
            
            worksheet.update_cell(next_row, 1, test_cell)
            print(f"✓ 書き込み権限確認成功 (行{next_row}に書き込み)")
            
            # 書き込んだ値を確認
            written_value = worksheet.cell(next_row, 1).value
            assert written_value == test_cell, "書き込んだ値が正しく読み取れない"
            print(f"✓ 書き込み内容確認成功: '{written_value}'")
            
        except Exception as e:
            pytest.fail(f"権限確認中にエラー: {e}")
        
        print("✓ 権限確認テスト成功")


if __name__ == "__main__":
    # 直接実行時のテスト
    test_client = TestSpreadsheetClient()
    test_client.setup_class()
    
    print("=== SpreadsheetClient 単体テスト ===\n")
    
    try:
        test_client.test_client_initialization()
        test_client.test_authentication()
        test_client.test_get_worksheet()
        test_client.test_worksheet_basic_operations()
        test_client.test_invalid_spreadsheet_id()
        test_client.test_invalid_worksheet_name()
        test_client.test_permissions()
        
        print("\n" + "="*50)
        print("✓ 全テストが成功しました！")
        print("="*50)
        
    except Exception as e:
        print(f"\n✗ テスト失敗: {str(e)}")
        raise