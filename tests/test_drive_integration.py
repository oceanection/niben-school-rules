"""
Google Drive API と school_rules_collector の統合テスト

実際の .env 設定と Google Drive API を使用してテスト
"""

import pytest
import os
from typing import List

from src.config.settings import settings
from src.drive.client import create_drive_client, DriveClient
from src.drive.school_rules_collector import (
    create_school_rules_collector, 
    SchoolRulesCollector,
    SchoolRulePDF
)


class TestDriveIntegration:
    """Google Drive API との統合テスト"""
    
    def setup_method(self):
        """各テストメソッドの前処理"""
        # 基本的な設定確認のみ（スキップ条件を緩和）
        try:
            self.drive_client = create_drive_client()
            self.collector = create_school_rules_collector(self.drive_client)
        except Exception as e:
            pytest.skip(f"Drive接続に失敗しました: {str(e)}")
    
    def test_drive_client_authentication(self):
        """DriveClient の認証テスト"""
        # DriveClient が正常に初期化されていることを確認
        assert isinstance(self.drive_client, DriveClient)
        assert self.drive_client.service is not None
    
    def test_settings_configuration(self):
        """設定値の確認テスト"""
        # BATCH_MODE が false であることを確認
        print(f"BATCH_MODE: {settings.batch_mode}")
        print(f"WARD_FOLDER_ID: {settings.ward_folder_id}")
        
        # 個別処理モードであることを確認
        assert settings.batch_mode is False, f"BATCH_MODE は False である必要があります。現在の値: {settings.batch_mode}"
        assert settings.ward_folder_id, f"WARD_FOLDER_ID が設定されていません。現在の値: {settings.ward_folder_id}"
    
    def test_drive_client_get_ward_folder_info(self):
        """区フォルダ情報取得テスト"""
        ward_info = self.drive_client.get_file_info(settings.ward_folder_id)
        
        print(f"取得した区フォルダ名: {ward_info['name']}")
        
        # 区フォルダが「練馬区」であることを確認
        assert ward_info['name'] == "練馬区", f"期待: 練馬区, 実際: {ward_info['name']}"
        assert 'id' in ward_info
        assert ward_info['id'] == settings.ward_folder_id
    
    def test_drive_client_list_school_folders(self):
        """学校フォルダ一覧取得テスト"""
        school_folders = self.drive_client.list_folders(settings.ward_folder_id)
        
        print(f"学校フォルダ数: {len(school_folders)}")
        for folder in school_folders:
            print(f"  - {folder['name']}")
        
        # 学校フォルダが1つ存在することを確認
        assert len(school_folders) >= 1, f"学校フォルダが見つかりません。フォルダ数: {len(school_folders)}"
        
        # 「練馬東」フォルダを探す
        nerima_higashi = None
        for folder in school_folders:
            if folder['name'] == "練馬東":
                nerima_higashi = folder
                break
        
        assert nerima_higashi is not None, f"'練馬東' フォルダが見つかりません。存在するフォルダ: {[f['name'] for f in school_folders]}"
        assert 'id' in nerima_higashi
        
        # 後続のテストで使用するためにフォルダIDを保存
        self.nerima_higashi_folder_id = nerima_higashi['id']
    
    def test_drive_client_list_pdf_files(self):
        """PDFファイル一覧取得テスト"""
        # まず学校フォルダを取得
        if not hasattr(self, 'nerima_higashi_folder_id'):
            school_folders = self.drive_client.list_folders(settings.ward_folder_id)
            nerima_higashi = next((f for f in school_folders if f['name'] == "練馬東"), None)
            assert nerima_higashi is not None, "練馬東フォルダが見つかりません"
            self.nerima_higashi_folder_id = nerima_higashi['id']
        
        # PDFファイル一覧を取得
        pdf_files = self.drive_client.list_files(
            self.nerima_higashi_folder_id, 
            mime_type='application/pdf'
        )
        
        print(f"PDFファイル数: {len(pdf_files)}")
        for pdf in pdf_files:
            print(f"  - {pdf['name']} (ID: {pdf['id']})")
        
        # PDFファイルが1つ以上存在することを確認
        assert len(pdf_files) >= 1, f"PDFファイルが見つかりません。ファイル数: {len(pdf_files)}"
        
        # 指定されたファイルIDまたはファイル名を確認
        expected_file_id = "1nAjsLuI2pWZfUbZSBpqeCdjLw1nvrzD3"
        expected_file_name = "211練東中　R7_0404版_学校生活のきまり.pdf"
        
        target_pdf = None
        # まずファイルIDで検索
        for pdf in pdf_files:
            if pdf['id'] == expected_file_id:
                target_pdf = pdf
                break
        
        # ファイルIDで見つからなければファイル名で検索
        if target_pdf is None:
            for pdf in pdf_files:
                if pdf['name'] == expected_file_name:
                    target_pdf = pdf
                    print(f"ファイル名で発見: {pdf['name']} (ID: {pdf['id']})")
                    break
        
        assert target_pdf is not None, f"指定されたファイルが見つかりません。ID: {expected_file_id}, 名前: {expected_file_name}"
        
        # 基本的なファイル情報が含まれていることを確認
        assert 'size_mb' in target_pdf
        assert 'mime_type' in target_pdf
        assert target_pdf['mime_type'] == 'application/pdf'
        
        # 後続のテストで使用するためにファイル情報を保存
        self.target_pdf = target_pdf
    
    def test_drive_client_get_pdf_file_info(self):
        """特定PDFファイル情報取得テスト"""
        if not hasattr(self, 'target_pdf'):
            # target_pdfが設定されていない場合は前のテストから取得
            self.test_drive_client_list_pdf_files()
        
        file_id = self.target_pdf['id']
        file_info = self.drive_client.get_file_info(file_id)
        
        print(f"ファイル情報: {file_info['name']} (ID: {file_info['id']})")
        
        # ファイル情報の確認
        assert file_info['id'] == file_id
        assert file_info['mime_type'] == 'application/pdf'
        assert 'size_mb' in file_info
        assert file_info['size_mb'] > 0
    
    def test_drive_client_download_file_content(self):
        """ファイル内容ダウンロードテスト"""
        if not hasattr(self, 'target_pdf'):
            self.test_drive_client_list_pdf_files()
        
        file_id = self.target_pdf['id']
        
        # ファイル内容をダウンロード
        file_content = self.drive_client.download_file_content(file_id)
        
        print(f"ダウンロードサイズ: {len(file_content)} bytes")
        
        # バイナリデータが取得できることを確認
        assert isinstance(file_content, bytes)
        assert len(file_content) > 0
        
        # PDFファイルのヘッダーが含まれていることを確認
        assert file_content.startswith(b'%PDF'), "PDFファイルの形式が正しくありません"
    
    def test_collector_validate_drive_structure(self):
        """Collector の Drive 構造検証テスト"""
        validation_result = self.collector.validate_drive_structure()
        
        print(f"検証結果: {validation_result}")
        
        # 検証が成功することを確認
        if not validation_result['valid']:
            print(f"検証エラー: {validation_result['errors']}")
        
        assert validation_result['valid'] is True, f"Drive構造検証に失敗: {validation_result['errors']}"
        assert len(validation_result['errors']) == 0
        
        # 情報が正しく取得されていることを確認
        info = validation_result['info']
        assert info['ward_folder'] == "練馬区", f"期待: 練馬区, 実際: {info['ward_folder']}"
        assert info['school_count'] >= 1, f"学校数が不正: {info['school_count']}"
    
    def test_collector_collect_all_school_rules(self):
        """Collector の校則データ収集テスト（メイン機能）"""
        # 校則データを収集
        school_rule_pdfs = self.collector.collect_all_school_rules()
        
        print(f"収集されたPDF数: {len(school_rule_pdfs)}")
        for pdf in school_rule_pdfs:
            print(f"  - {pdf.ward}/{pdf.school}: {pdf.file_name}")
        
        # 収集結果の基本検証
        assert isinstance(school_rule_pdfs, list)
        assert len(school_rule_pdfs) >= 1, "校則PDFが収集されませんでした"
        
        # 練馬東のPDFを探す
        nerima_higashi_pdf = None
        for pdf in school_rule_pdfs:
            if pdf.ward == "練馬区" and pdf.school == "練馬東":
                nerima_higashi_pdf = pdf
                break
        
        assert nerima_higashi_pdf is not None, "練馬区/練馬東の校則PDFが見つかりません"
        
        # SchoolRulePDF オブジェクトの検証
        assert isinstance(nerima_higashi_pdf, SchoolRulePDF)
        
        # 基本的な値の確認（ファイルIDとファイル名は柔軟に対応）
        assert nerima_higashi_pdf.ward == "練馬区"
        assert nerima_higashi_pdf.school == "練馬東"
        
        # ファイルパスの形式確認
        expected_path_pattern = "練馬区/練馬東/"
        assert nerima_higashi_pdf.file_path.startswith(expected_path_pattern), f"ファイルパス形式が不正: {nerima_higashi_pdf.file_path}"
        
        # その他の項目は存在することのみ確認
        assert hasattr(nerima_higashi_pdf, 'file_size_mb')
        assert hasattr(nerima_higashi_pdf, 'web_view_link')
        assert hasattr(nerima_higashi_pdf, 'created_time')
        assert hasattr(nerima_higashi_pdf, 'modified_time')
        
        # 後続テスト用に保存
        self.collected_pdfs = school_rule_pdfs
        self.nerima_higashi_pdf = nerima_higashi_pdf
    
    def test_collector_prepare_for_gemini_processing(self):
        """Collector の Gemini 処理用データ準備テスト"""
        # 校則データを収集（まだ収集されていない場合）
        if not hasattr(self, 'collected_pdfs'):
            self.test_collector_collect_all_school_rules()
        
        # Gemini処理用データを準備
        gemini_data = self.collector.prepare_for_gemini_processing(self.collected_pdfs)
        
        print(f"Gemini用データ: {len(gemini_data['schools'])}校, {gemini_data['metadata']['total_pdfs']}PDF")
        
        # データ構造の確認
        assert 'schools' in gemini_data
        assert 'metadata' in gemini_data
        
        # schools データの確認
        schools = gemini_data['schools']
        assert len(schools) >= 1
        
        # 練馬東のデータを探す
        nerima_higashi_school = None
        for school in schools:
            if school['ward'] == "練馬区" and school['school'] == "練馬東":
                nerima_higashi_school = school
                break
        
        assert nerima_higashi_school is not None, "練馬区/練馬東の学校データが見つかりません"
        assert len(nerima_higashi_school['pdfs']) >= 1
        
        # metadata の確認
        metadata = gemini_data['metadata']
        assert metadata['total_schools'] >= 1
        assert metadata['total_pdfs'] >= 1
        assert metadata['collection_mode'] == "個別収集"
    
    def test_end_to_end_integration(self):
        """エンドツーエンド統合テスト"""
        print("=== エンドツーエンド統合テスト開始 ===")
        
        # 1. Drive構造検証
        validation_result = self.collector.validate_drive_structure()
        assert validation_result['valid'] is True
        print("✓ Drive構造検証 OK")
        
        # 2. 校則データ収集
        school_rule_pdfs = self.collector.collect_all_school_rules()
        assert len(school_rule_pdfs) >= 1
        print(f"✓ 校則データ収集 OK ({len(school_rule_pdfs)}件)")
        
        # 3. Gemini処理用データ準備
        gemini_data = self.collector.prepare_for_gemini_processing(school_rule_pdfs)
        print(f"✓ Gemini処理用データ準備 OK ({gemini_data['metadata']['total_schools']}校)")
        
        # 4. 練馬東のデータを確認
        nerima_higashi_school = None
        for school in gemini_data['schools']:
            if school['ward'] == "練馬区" and school['school'] == "練馬東":
                nerima_higashi_school = school
                break
        
        assert nerima_higashi_school is not None
        assert len(nerima_higashi_school['pdfs']) >= 1
        print("✓ 練馬東データ確認 OK")
        
        # 5. 実際のファイルダウンロードも確認
        pdf = nerima_higashi_school['pdfs'][0]
        file_content = self.drive_client.download_file_content(pdf['file_id'])
        assert isinstance(file_content, bytes)
        assert len(file_content) > 0
        assert file_content.startswith(b'%PDF')
        print("✓ ファイルダウンロード OK")
        
        print("=== エンドツーエンド統合テスト完了 ===")


class TestDriveIntegrationErrorHandling:
    """統合テストのエラーハンドリング"""
    
    def setup_method(self):
        """各テストメソッドの前処理"""
        try:
            self.drive_client = create_drive_client()
            self.collector = create_school_rules_collector(self.drive_client)
        except Exception as e:
            pytest.skip(f"Drive接続に失敗しました: {str(e)}")
    
    def test_invalid_folder_id_handling(self):
        """無効なフォルダIDの処理テスト"""
        invalid_folder_id = "invalid_folder_id_123"
        
        # 無効なフォルダIDでエラーが発生することを確認
        with pytest.raises(Exception):  # ConnectionError or HttpError
            self.drive_client.get_file_info(invalid_folder_id)
    
    def test_invalid_file_id_handling(self):
        """無効なファイルIDの処理テスト"""
        invalid_file_id = "invalid_file_id_123"
        
        # 無効なファイルIDでエラーが発生することを確認
        with pytest.raises(Exception):  # ConnectionError or HttpError
            self.drive_client.download_file_content(invalid_file_id)


if __name__ == "__main__":
    # 統合テストは時間がかかるため、明示的に実行する場合のみ
    pytest.main([__file__, "-v", "-s"])  # -s で print 出力を表示