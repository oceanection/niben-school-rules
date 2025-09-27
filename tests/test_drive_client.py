"""
Google Drive API クライアントの単体テスト

実際のGoogle Driveの特定フォルダにアクセスしてテストを実行
"""

import pytest

from config.settings import settings
from src.drive.client import DriveClient, create_drive_client


class TestDriveClient:
    """DriveClient の単体テスト - 実際のGoogle Driveフォルダを使用"""
    
    @classmethod
    def setup_class(cls):
        """テストクラスのセットアップ"""
        # Google認証情報の確認
        if not settings.google_application_credentials:
            pytest.skip("Google認証情報が設定されていません")
        
        # DriveClientインスタンス作成
        cls.drive_client = create_drive_client()
        
        # テスト対象フォルダIDを設定
        cls.test_folder_id = cls._get_test_folder_id()
        
        print(f"テスト対象フォルダID: {cls.test_folder_id}")
        print(f"処理モード: {'一括処理' if settings.batch_mode else '個別処理'}")
    
    @classmethod
    def _get_test_folder_id(cls):
        """テスト用フォルダIDを.envから取得"""
        if settings.batch_mode and settings.root_folder_id:
            return settings.root_folder_id
        elif settings.ward_folder_id:
            return settings.ward_folder_id
        else:
            pytest.skip("ROOT_FOLDER_IDまたはWARD_FOLDER_IDが設定されていません")
    
    @property
    def TEST_FOLDER_ID(self):
        """テスト用フォルダIDを取得"""
        return self.__class__.test_folder_id
    
    def test_01_client_authentication(self):
        """認証テスト"""
        # DriveClientが正常に作成されることを確認
        assert self.drive_client is not None
        assert self.drive_client.service is not None
        
        # 認証確認のため簡単なAPI呼び出し
        try:
            about = self.drive_client.service.about().get(fields="user").execute()
            assert "user" in about
            print(f"✅ 認証成功: {about['user']['emailAddress']}")
        except Exception as e:
            pytest.fail(f"❌ 認証失敗: {str(e)}")
    
    def test_02_list_folders(self):
        """フォルダ一覧取得テスト"""
        folders = self.drive_client.list_folders(self.TEST_FOLDER_ID)
        
        assert isinstance(folders, list)
        
        # 結果をコンソールに表示
        print(f"📁 検出フォルダ数: {len(folders)}")
        for i, folder in enumerate(folders[:5]):  # 最初の5つのみ表示
            print(f"  {i+1}. {folder['name']} (ID: {folder['id']})")
        
        # 基本的な構造チェック
        if folders:
            folder = folders[0]
            assert "id" in folder
            assert "name" in folder
    
    def test_03_list_all_files(self):
        """全ファイル一覧取得テスト"""
        files = self.drive_client.list_files(self.TEST_FOLDER_ID)
        
        assert isinstance(files, list)
        
        # 結果をコンソールに表示
        print(f"📄 検出ファイル数: {len(files)}")
        for i, file in enumerate(files[:5]):  # 最初の5つのみ表示
            print(f"  {i+1}. {file['name']} ({file['size_mb']}MB, {file['mime_type']})")
        
        # 基本的な構造チェック
        if files:
            file = files[0]
            assert "id" in file
            assert "name" in file
            assert "size_mb" in file
    
    def test_04_list_pdf_files(self):
        """PDFファイル一覧取得テスト"""
        pdf_files = self.drive_client.list_files(
            self.TEST_FOLDER_ID, 
            mime_type='application/pdf'
        )
        
        assert isinstance(pdf_files, list)
        
        # 結果をコンソールに表示
        print(f"📋 検出PDFファイル数: {len(pdf_files)}")
        for i, pdf in enumerate(pdf_files):
            print(f"  {i+1}. {pdf['name']} ({pdf['size_mb']}MB)")
        
        # PDFファイルの検証
        for pdf_file in pdf_files:
            assert pdf_file["mime_type"] == "application/pdf"
            assert pdf_file["name"].lower().endswith(".pdf")
    
    def test_05_get_file_info(self):
        """ファイル情報取得テスト"""
        # まず対象フォルダ内のファイルを取得
        files = self.drive_client.list_files(self.TEST_FOLDER_ID)
        
        if not files:
            pytest.skip("テスト対象フォルダにファイルがありません")
        
        # 最初のファイルの詳細情報を取得
        test_file = files[0]
        file_info = self.drive_client.get_file_info(test_file['id'])
        
        assert isinstance(file_info, dict)
        assert file_info['id'] == test_file['id']
        
        # 結果をコンソールに表示
        print(f"📝 ファイル詳細情報:")
        print(f"  名前: {file_info['name']}")
        print(f"  サイズ: {file_info['size_mb']}MB")
        print(f"  種類: {file_info['mime_type']}")
        print(f"  作成日: {file_info.get('created_time', 'N/A')}")
    
    def test_06_download_small_file(self):
        """小サイズファイルダウンロードテスト"""
        # 小さなファイルを探す（1MB未満）
        files = self.drive_client.list_files(self.TEST_FOLDER_ID)
        small_files = [f for f in files if f['size_mb'] < 1.0 and f['size'] > 0]
        
        if not small_files:
            pytest.skip("1MB未満のファイルが見つかりません")
        
        # 最小ファイルをダウンロード
        target_file = min(small_files, key=lambda x: x['size'])
        
        print(f"📥 ダウンロード対象: {target_file['name']} ({target_file['size_mb']}MB)")
        
        file_content = self.drive_client.download_file_content(target_file['id'])
        
        assert isinstance(file_content, bytes)
        assert len(file_content) > 0
        assert len(file_content) == target_file['size']
        
        # 結果をコンソールに表示
        print(f"✅ ダウンロード成功: {len(file_content)} bytes")
    
        """フォルダ階層探索テスト"""
        # ルートフォルダ情報
        root_info = self.drive_client.get_file_info(self.TEST_FOLDER_ID)
        
        print(f"🗂️  ルートフォルダ: {root_info['name']}")
        
        # サブフォルダを探索（最大3階層まで）
        subfolders = self.drive_client.list_folders(self.TEST_FOLDER_ID)
        
        for i, folder in enumerate(subfolders[:3]):  # 最初の3フォルダのみ
            print(f"📁 [{i+1}] {folder['name']}")
            
            # フォルダ内のファイルを調査
            try:
                folder_files = self.drive_client.list_files(folder['id'])
                
                # PDFファイルを記録
                pdf_files = [f for f in folder_files if f['mime_type'] == 'application/pdf']
                
                print(f"    ファイル数: {len(folder_files)}, PDF数: {len(pdf_files)}")
                
            except Exception as e:
                print(f"    エラー: {str(e)}")
        
        print(f"✅ 階層探索完了: {len(subfolders)}個のサブフォルダ")
    
    def test_08_error_handling(self):
        """エラーハンドリングテスト"""
        print("🚫 エラーハンドリングテスト実行中...")
        
        fake_file_id = "non_existent_file_id_12345"
        
        # 存在しないファイルIDでのアクセステスト
        test_cases = [
            ("get_file_info", lambda: self.drive_client.get_file_info(fake_file_id)),
            ("download_file_content", lambda: self.drive_client.download_file_content(fake_file_id)),
            ("list_folders", lambda: self.drive_client.list_folders(fake_file_id))
        ]
        
        error_count = 0
        
        for test_name, test_func in test_cases:
            try:
                test_func()
                print(f"  ❌ {test_name}: 例外が発生しませんでした")
            except Exception as e:
                error_count += 1
                print(f"  ✅ {test_name}: 正常に例外発生 ({type(e).__name__})")
        
        # 少なくとも1つは例外が発生することを確認
        assert error_count > 0, "エラーハンドリングが機能していません"
    
    def _save_test_result(self, test_name: str, result: dict):
        """テスト結果をJSONファイルに保存"""
        filename = f"{self.timestamp}_{test_name}.json"
        filepath = self.test_output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"💾 結果保存: {filepath}")


if __name__ == "__main__":
    # テストを直接実行する前にフォルダIDを確認
    print("=" * 60)
    print("Google Drive API Client テスト")
    print("=" * 60)
    print(f"処理モード: {'一括処理' if settings.batch_mode else '個別処理'}")
    if settings.batch_mode:
        print(f"ルートフォルダID: {settings.root_folder_id}")
    else:
        print(f"区フォルダID: {settings.ward_folder_id}")
    print("注意: .envファイルで正しいフォルダIDが設定されていることを確認してください")
    print("=" * 60)
    
    # pytest実行
    pytest.main([__file__, "-v", "-s"])