"""
Google Drive クライアントの単体テスト

実際のGoogle Drive環境でのテストを実施
"""

import sys
from pathlib import Path
import pytest

# srcディレクトリをパスに追加
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from config.settings import settings
from drive.client import DriveClient, create_drive_client


class TestDriveClient:
    """DriveClient の単体テスト"""
    
    @classmethod
    def setup_class(cls):
        """テストクラスの初期化"""
        cls.client = create_drive_client()
        
        # テスト用の検証データ
        cls.expected_urls = {
            "練馬東": "https://drive.google.com/drive/folders/1nAjsLuI2pWZfUbZSBpqeCdjLw1nvrzD3",
            "北町": "https://drive.google.com/drive/folders/1cRMK9nzL7i6foEUOrhmKsvnKKahk0arY"
        }
        
        # テスト用フォルダID（練馬区フォルダのID）
        cls.ward_folder_id = settings.ward_folder_id
        
        print(f"テスト開始: ward_folder_id = {cls.ward_folder_id}")
    
    def test_client_initialization(self):
        """DriveClient の初期化テスト"""
        assert self.client is not None
        assert self.client.service is not None
        print("✓ DriveClient 初期化成功")
    
    def test_authentication(self):
        """認証テスト"""
        # 認証が成功していることを確認
        assert settings.google_application_credentials is not None
        assert self.client.service is not None
        print("✓ Google Drive API 認証成功")
    
    def test_list_folders_ward_level(self):
        """区レベルのフォルダ一覧取得テスト"""
        folders = self.client.list_folders(self.ward_folder_id)
        
        assert isinstance(folders, list)
        assert len(folders) > 0
        
        # フォルダ名を取得
        folder_names = [folder['name'] for folder in folders]
        print(f"取得したフォルダ: {folder_names}")
        
        # 期待するフォルダが含まれているかチェック
        expected_schools = ["練馬東", "北町"]
        found_schools = []
        
        for school in expected_schools:
            if school in folder_names:
                found_schools.append(school)
        
        assert len(found_schools) > 0, f"期待する学校フォルダが見つかりません: {expected_schools}"
        print(f"✓ 学校フォルダ発見: {found_schools}")
    
    def test_folder_ids_and_urls(self):
        """フォルダIDとURL生成のテスト"""
        folders = self.client.list_folders(self.ward_folder_id)
        
        url_validation_results = {}
        
        for folder in folders:
            folder_name = folder['name']
            folder_id = folder['id']
            
            # URLを生成
            generated_url = f"https://drive.google.com/drive/folders/{folder_id}"
            
            # 検証データと比較
            if folder_name in self.expected_urls:
                expected_url = self.expected_urls[folder_name]
                url_validation_results[folder_name] = {
                    'folder_id': folder_id,
                    'generated_url': generated_url,
                    'expected_url': expected_url,
                    'match': generated_url == expected_url
                }
        
        # 結果を表示
        for school, result in url_validation_results.items():
            print(f"\n--- {school} ---")
            print(f"フォルダID: {result['folder_id']}")
            print(f"生成URL: {result['generated_url']}")
            print(f"期待URL: {result['expected_url']}")
            print(f"一致: {'✓' if result['match'] else '✗'}")
            
            # URLが一致することを確認
            assert result['match'], f"{school}のURL生成が期待値と一致しません"
        
        print(f"\n✓ 全URLの生成と検証が成功: {len(url_validation_results)}件")
    
    def test_list_files_in_school_folder(self):
        """学校フォルダ内のファイル一覧取得テスト"""
        folders = self.client.list_folders(self.ward_folder_id)
        
        # 最初に見つかった学校フォルダでテスト
        if folders:
            test_folder = folders[0]
            folder_id = test_folder['id']
            folder_name = test_folder['name']
            
            print(f"テスト対象フォルダ: {folder_name} (ID: {folder_id})")
            
            # フォルダ内の全ファイルを取得
            all_files = self.client.list_files(folder_id)
            print(f"全ファイル数: {len(all_files)}")
            
            # PDFファイルのみを取得
            pdf_files = self.client.list_files(folder_id, mime_type='application/pdf')
            print(f"PDFファイル数: {len(pdf_files)}")
            
            # ファイル情報の確認
            for pdf_file in pdf_files[:3]:  # 最初の3件のみ表示
                print(f"  - {pdf_file['name']} ({pdf_file['size_mb']} MB)")
            
            assert isinstance(all_files, list)
            assert isinstance(pdf_files, list)
            print("✓ ファイル一覧取得成功")
    
    def test_get_file_info(self):
        """ファイル情報取得テスト"""
        # 区フォルダの情報を取得してテスト
        file_info = self.client.get_file_info(self.ward_folder_id)
        
        assert isinstance(file_info, dict)
        assert 'id' in file_info
        assert 'name' in file_info
        assert file_info['id'] == self.ward_folder_id
        
        print(f"✓ ファイル情報取得成功: {file_info['name']}")


if __name__ == "__main__":
    # 直接実行時のテスト
    test_client = TestDriveClient()
    test_client.setup_class()
    
    print("=== Google Drive Client 単体テスト ===\n")
    
    try:
        test_client.test_client_initialization()
        test_client.test_authentication()
        test_client.test_list_folders_ward_level()
        test_client.test_folder_ids_and_urls()
        test_client.test_list_files_in_school_folder()
        test_client.test_get_file_info()
        
        print("\n" + "="*50)
        print("✓ 全テストが成功しました！")
        print("="*50)
        
    except Exception as e:
        print(f"\n✗ テスト失敗: {str(e)}")
        raise