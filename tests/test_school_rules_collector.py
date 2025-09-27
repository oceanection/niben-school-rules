"""
SchoolRulesCollector の単体テスト

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
from drive.client import create_drive_client
from drive.school_rules_collector import SchoolRulesCollector, SchoolRulePDF, create_school_rules_collector


class TestSchoolRulesCollector:
    """SchoolRulesCollector の単体テスト"""
    
    @classmethod
    def setup_class(cls):
        """テストクラスの初期化"""
        cls.drive_client = create_drive_client()
        cls.collector = create_school_rules_collector(cls.drive_client)
        
        # テスト用の検証データ
        cls.expected_urls = {
            "練馬東": "https://drive.google.com/drive/folders/1nAjsLuI2pWZfUbZSBpqeCdjLw1nvrzD3",
            "北町": "https://drive.google.com/drive/folders/1cRMK9nzL7i6foEUOrhmKsvnKKahk0arY"
        }
        
        print(f"テスト開始: WARD_FOLDER_ID = {settings.ward_folder_id}")
        print(f"BATCH_MODE = {settings.batch_mode}")
    
    def test_collector_initialization(self):
        """SchoolRulesCollector の初期化テスト"""
        assert self.collector is not None
        assert self.collector.drive_client is not None
        assert len(self.collector.tokyo_wards) == 23
        print("✓ SchoolRulesCollector 初期化成功")
    
    def test_validate_configuration(self):
        """設定検証テスト"""
        try:
            self.collector._validate_configuration()
            print("✓ 設定検証成功")
        except ValueError as e:
            pytest.fail(f"設定検証失敗: {e}")
    
    def test_validate_drive_structure(self):
        """Google Drive構造検証テスト"""
        validation_result = self.collector.validate_drive_structure()
        
        assert isinstance(validation_result, dict)
        assert 'valid' in validation_result
        assert 'errors' in validation_result
        assert 'warnings' in validation_result
        assert 'info' in validation_result
        
        print(f"Drive構造検証結果:")
        print(f"  Valid: {validation_result['valid']}")
        print(f"  Errors: {validation_result['errors']}")
        print(f"  Warnings: {validation_result['warnings']}")
        print(f"  Info: {validation_result['info']}")
        
        # 個別処理モードの場合の検証
        if not settings.batch_mode:
            info = validation_result['info']
            assert 'ward_folder' in info
            assert 'school_count' in info
            print(f"  区フォルダ: {info['ward_folder']}")
            print(f"  学校数: {info['school_count']}")
        
        assert validation_result['valid'], "Drive構造検証が失敗しました"
        print("✓ Drive構造検証成功")
    
    def test_collect_ward_pdfs(self):
        """区フォルダ内PDF収集テスト"""
        ward_info = self.drive_client.get_file_info(settings.ward_folder_id)
        ward_name = ward_info['name']
        
        print(f"PDF収集テスト開始: {ward_name}")
        
        ward_pdfs = self.collector._collect_ward_pdfs(settings.ward_folder_id, ward_name)
        
        assert isinstance(ward_pdfs, list)
        print(f"収集されたPDF数: {len(ward_pdfs)}")
        
        # 各PDFの内容確認
        school_urls = {}
        for pdf in ward_pdfs:
            assert isinstance(pdf, SchoolRulePDF)
            assert pdf.ward == ward_name
            assert pdf.school_folder_url.startswith("https://drive.google.com/drive/folders/")
            
            # 学校別にURLを記録
            if pdf.school not in school_urls:
                school_urls[pdf.school] = pdf.school_folder_url
            
            print(f"  PDF: {pdf.ward}/{pdf.school}/{pdf.file_name}")
            print(f"    URL: {pdf.school_folder_url}")
            print(f"    サイズ: {pdf.file_size_mb} MB")
        
        # URL検証
        print(f"\n学校フォルダURL検証:")
        for school, url in school_urls.items():
            print(f"  {school}: {url}")
            
            if school in self.expected_urls:
                expected = self.expected_urls[school]
                match = url == expected
                print(f"    期待値: {expected}")
                print(f"    一致: {'✓' if match else '✗'}")
                assert match, f"{school}のURL生成が期待値と一致しません"
        
        print("✓ 区フォルダ内PDF収集成功")
        return ward_pdfs
    
    def test_collect_all_school_rules(self):
        """全校則収集テスト"""
        school_pdfs = self.collector.collect_all_school_rules()
        
        assert isinstance(school_pdfs, list)
        assert len(school_pdfs) > 0
        
        print(f"全校則収集結果: {len(school_pdfs)}件のPDF")
        
        # 学校別の統計
        school_stats = {}
        for pdf in school_pdfs:
            school_key = f"{pdf.ward}_{pdf.school}"
            if school_key not in school_stats:
                school_stats[school_key] = {
                    'count': 0,
                    'url': pdf.school_folder_url
                }
            school_stats[school_key]['count'] += 1
        
        print(f"学校別PDF統計:")
        for school_key, stats in school_stats.items():
            print(f"  {school_key}: {stats['count']}件 (URL: {stats['url']})")
        
        print("✓ 全校則収集成功")
        return school_pdfs
    
    def test_prepare_for_gemini_processing(self):
        """Gemini処理用データ準備テスト"""
        school_pdfs = self.collector.collect_all_school_rules()
        processed_data = self.collector.prepare_for_gemini_processing(school_pdfs)
        
        assert isinstance(processed_data, dict)
        assert 'schools' in processed_data
        assert 'metadata' in processed_data
        
        schools = processed_data['schools']
        metadata = processed_data['metadata']
        
        print(f"Gemini処理用データ準備結果:")
        print(f"  学校数: {metadata['total_schools']}")
        print(f"  総PDF数: {metadata['total_pdfs']}")
        print(f"  収集モード: {metadata['collection_mode']}")
        
        # 各学校のデータ構造確認
        for school in schools:
            assert 'ward' in school
            assert 'school' in school
            assert 'school_folder_url' in school  # ←ここが重要！
            assert 'pdfs' in school
            
            print(f"  学校: {school['ward']}/{school['school']}")
            print(f"    URL: {school['school_folder_url']}")
            print(f"    PDF数: {len(school['pdfs'])}")
            
            # URL検証
            school_name = school['school']
            if school_name in self.expected_urls:
                expected_url = self.expected_urls[school_name]
                actual_url = school['school_folder_url']
                match = actual_url == expected_url
                print(f"    URL検証: {'✓' if match else '✗'}")
                assert match, f"{school_name}のURL生成が期待値と一致しません"
        
        print("✓ Gemini処理用データ準備成功")
        return processed_data
    
    def test_school_rule_pdf_dataclass(self):
        """SchoolRulePDF データクラステスト"""
        # サンプルデータでテスト
        pdf = SchoolRulePDF(
            ward="練馬区",
            school="テスト学校",
            file_id="test_id",
            file_name="test.pdf",
            file_size_mb=1.5,
            file_path="練馬区/テスト学校/test.pdf",
            web_view_link="https://drive.google.com/file/d/test_id/view",
            created_time="2024-01-01T00:00:00.000Z",
            modified_time="2024-01-01T00:00:00.000Z",
            school_folder_url="https://drive.google.com/drive/folders/test_folder_id"
        )
        
        assert pdf.ward == "練馬区"
        assert pdf.school == "テスト学校"
        assert pdf.school_folder_url == "https://drive.google.com/drive/folders/test_folder_id"
        
        print("✓ SchoolRulePDF データクラステスト成功")


if __name__ == "__main__":
    # 直接実行時のテスト
    test_collector = TestSchoolRulesCollector()
    test_collector.setup_class()
    
    print("=== SchoolRulesCollector 単体テスト ===\n")
    
    try:
        test_collector.test_collector_initialization()
        test_collector.test_validate_configuration()
        test_collector.test_validate_drive_structure()
        test_collector.test_school_rule_pdf_dataclass()
        test_collector.test_collect_ward_pdfs()
        test_collector.test_collect_all_school_rules()
        test_collector.test_prepare_for_gemini_processing()
        
        print("\n" + "="*50)
        print("✓ 全テストが成功しました！")
        print("="*50)
        
    except Exception as e:
        print(f"\n✗ テスト失敗: {str(e)}")
        raise