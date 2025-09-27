"""
school_rules_collector.py の単体テスト

DriveClientとの依存関係がない部分をテスト
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from src.drive.school_rules_collector import (
    SchoolRulesCollector, 
    SchoolRulePDF,
    create_school_rules_collector
)


class TestSchoolRulePDF:
    """SchoolRulePDF データクラスのテスト"""
    
    def test_school_rule_pdf_creation(self):
        """SchoolRulePDFの作成テスト"""
        pdf = SchoolRulePDF(
            ward="渋谷区",
            school="XX中学校",
            file_id="abc123",
            file_name="校則.pdf",
            file_size_mb=1.5,
            file_path="渋谷区/XX中学校/校則.pdf",
            web_view_link="https://drive.google.com/file/d/abc123/view",
            created_time="2025-01-01T00:00:00.000Z",
            modified_time="2025-01-01T00:00:00.000Z"
        )
        
        assert pdf.ward == "渋谷区"
        assert pdf.school == "XX中学校"
        assert pdf.file_id == "abc123"
        assert pdf.file_name == "校則.pdf"
        assert pdf.file_size_mb == 1.5
        assert pdf.file_path == "渋谷区/XX中学校/校則.pdf"
        assert pdf.web_view_link == "https://drive.google.com/file/d/abc123/view"
        assert pdf.created_time == "2025-01-01T00:00:00.000Z"
        assert pdf.modified_time == "2025-01-01T00:00:00.000Z"


class TestSchoolRulesCollector:
    """SchoolRulesCollector クラスのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.mock_drive_client = Mock()
        self.collector = SchoolRulesCollector(self.mock_drive_client)
    
    def test_init(self):
        """初期化テスト"""
        assert self.collector.drive_client == self.mock_drive_client
        assert len(self.collector.tokyo_wards) == 23
        assert "渋谷区" in self.collector.tokyo_wards
        assert "千代田区" in self.collector.tokyo_wards
        assert "江戸川区" in self.collector.tokyo_wards
    
    def test_tokyo_wards_list(self):
        """東京23区リストの完全性テスト"""
        expected_wards = [
            "千代田区", "中央区", "港区", "新宿区", "文京区", "台東区", "墨田区",
            "江東区", "品川区", "目黒区", "大田区", "世田谷区", "渋谷区", "中野区",
            "杉並区", "豊島区", "北区", "荒川区", "板橋区", "練馬区", "足立区",
            "葛飾区", "江戸川区"
        ]
        
        assert set(self.collector.tokyo_wards) == set(expected_wards)
        assert len(self.collector.tokyo_wards) == 23
    
    @patch('src.drive.school_rules_collector.settings')
    def test_validate_configuration_batch_mode_valid(self, mock_settings):
        """設定検証テスト - 一括モード（正常）"""
        mock_settings.batch_mode = True
        mock_settings.root_folder_id = "root123"
        
        # 例外が発生しないことを確認
        self.collector._validate_configuration()
    
    @patch('src.drive.school_rules_collector.settings')
    def test_validate_configuration_batch_mode_invalid(self, mock_settings):
        """設定検証テスト - 一括モード（異常）"""
        mock_settings.batch_mode = True
        mock_settings.root_folder_id = None
        
        with pytest.raises(ValueError, match="一括収集にはROOT_FOLDER_IDが必要です"):
            self.collector._validate_configuration()
    
    @patch('src.drive.school_rules_collector.settings')
    def test_validate_configuration_individual_mode_valid(self, mock_settings):
        """設定検証テスト - 個別モード（正常）"""
        mock_settings.batch_mode = False
        mock_settings.ward_folder_id = "ward123"
        
        # 例外が発生しないことを確認
        self.collector._validate_configuration()
    
    @patch('src.drive.school_rules_collector.settings')
    def test_validate_configuration_individual_mode_invalid(self, mock_settings):
        """設定検証テスト - 個別モード（異常）"""
        mock_settings.batch_mode = False
        mock_settings.ward_folder_id = None
        
        with pytest.raises(ValueError, match="個別収集にはWARD_FOLDER_IDが必要です"):
            self.collector._validate_configuration()
    
    def test_prepare_for_gemini_processing_single_school_single_pdf(self):
        """Gemini処理用データ準備テスト - 単一学校・単一PDF"""
        pdfs = [
            SchoolRulePDF(
                ward="渋谷区",
                school="XX中学校",
                file_id="abc123",
                file_name="校則.pdf",
                file_size_mb=1.5,
                file_path="渋谷区/XX中学校/校則.pdf",
                web_view_link="https://drive.google.com/file/d/abc123/view",
                created_time="2025-01-01T00:00:00.000Z",
                modified_time="2025-01-01T00:00:00.000Z"
            )
        ]
        
        with patch('src.drive.school_rules_collector.settings') as mock_settings:
            mock_settings.batch_mode = True
            result = self.collector.prepare_for_gemini_processing(pdfs)
        
        assert "schools" in result
        assert "metadata" in result
        
        # schools データの検証
        schools = result["schools"]
        assert len(schools) == 1
        
        school = schools[0]
        assert school["ward"] == "渋谷区"
        assert school["school"] == "XX中学校"
        assert len(school["pdfs"]) == 1
        
        pdf = school["pdfs"][0]
        assert pdf["file_id"] == "abc123"
        assert pdf["file_name"] == "校則.pdf"
        assert pdf["file_size_mb"] == 1.5
        
        # metadata の検証
        metadata = result["metadata"]
        assert metadata["total_schools"] == 1
        assert metadata["total_pdfs"] == 1
        assert metadata["collection_mode"] == "一括収集"
    
    def test_prepare_for_gemini_processing_single_school_multiple_pdfs(self):
        """Gemini処理用データ準備テスト - 単一学校・複数PDF"""
        pdfs = [
            SchoolRulePDF(
                ward="渋谷区",
                school="XX中学校",
                file_id="abc123",
                file_name="校則.pdf",
                file_size_mb=1.5,
                file_path="渋谷区/XX中学校/校則.pdf",
                web_view_link="https://drive.google.com/file/d/abc123/view",
                created_time="2025-01-01T00:00:00.000Z",
                modified_time="2025-01-01T00:00:00.000Z"
            ),
            SchoolRulePDF(
                ward="渋谷区",
                school="XX中学校",
                file_id="def456",
                file_name="生活のきまり.pdf",
                file_size_mb=2.0,
                file_path="渋谷区/XX中学校/生活のきまり.pdf",
                web_view_link="https://drive.google.com/file/d/def456/view",
                created_time="2025-01-02T00:00:00.000Z",
                modified_time="2025-01-02T00:00:00.000Z"
            )
        ]
        
        with patch('src.drive.school_rules_collector.settings') as mock_settings:
            mock_settings.batch_mode = False
            result = self.collector.prepare_for_gemini_processing(pdfs)
        
        # schools データの検証
        schools = result["schools"]
        assert len(schools) == 1
        
        school = schools[0]
        assert school["ward"] == "渋谷区"
        assert school["school"] == "XX中学校"
        assert len(school["pdfs"]) == 2
        
        # PDFファイルの検証
        pdf_names = [pdf["file_name"] for pdf in school["pdfs"]]
        assert "校則.pdf" in pdf_names
        assert "生活のきまり.pdf" in pdf_names
        
        # metadata の検証
        metadata = result["metadata"]
        assert metadata["total_schools"] == 1
        assert metadata["total_pdfs"] == 2
        assert metadata["collection_mode"] == "個別収集"
    
    def test_prepare_for_gemini_processing_multiple_schools(self):
        """Gemini処理用データ準備テスト - 複数学校"""
        pdfs = [
            SchoolRulePDF(
                ward="渋谷区",
                school="XX中学校",
                file_id="abc123",
                file_name="校則.pdf",
                file_size_mb=1.5,
                file_path="渋谷区/XX中学校/校則.pdf",
                web_view_link="https://drive.google.com/file/d/abc123/view",
                created_time="2025-01-01T00:00:00.000Z",
                modified_time="2025-01-01T00:00:00.000Z"
            ),
            SchoolRulePDF(
                ward="渋谷区",
                school="YY小学校",
                file_id="def456",
                file_name="学校生活のルール.pdf",
                file_size_mb=2.0,
                file_path="渋谷区/YY小学校/学校生活のルール.pdf",
                web_view_link="https://drive.google.com/file/d/def456/view",
                created_time="2025-01-02T00:00:00.000Z",
                modified_time="2025-01-02T00:00:00.000Z"
            ),
            SchoolRulePDF(
                ward="新宿区",
                school="ZZ高等学校",
                file_id="ghi789",
                file_name="生徒心得.pdf",
                file_size_mb=1.8,
                file_path="新宿区/ZZ高等学校/生徒心得.pdf",
                web_view_link="https://drive.google.com/file/d/ghi789/view",
                created_time="2025-01-03T00:00:00.000Z",
                modified_time="2025-01-03T00:00:00.000Z"
            )
        ]
        
        with patch('src.drive.school_rules_collector.settings') as mock_settings:
            mock_settings.batch_mode = True
            result = self.collector.prepare_for_gemini_processing(pdfs)
        
        # schools データの検証
        schools = result["schools"]
        assert len(schools) == 3
        
        # 学校名でソートして検証
        schools_by_name = {f"{s['ward']}_{s['school']}": s for s in schools}
        
        assert "渋谷区_XX中学校" in schools_by_name
        assert "渋谷区_YY小学校" in schools_by_name
        assert "新宿区_ZZ高等学校" in schools_by_name
        
        # 各学校のPDF数確認
        assert len(schools_by_name["渋谷区_XX中学校"]["pdfs"]) == 1
        assert len(schools_by_name["渋谷区_YY小学校"]["pdfs"]) == 1
        assert len(schools_by_name["新宿区_ZZ高等学校"]["pdfs"]) == 1
        
        # metadata の検証
        metadata = result["metadata"]
        assert metadata["total_schools"] == 3
        assert metadata["total_pdfs"] == 3
        assert metadata["collection_mode"] == "一括収集"
    
    def test_prepare_for_gemini_processing_empty_list(self):
        """Gemini処理用データ準備テスト - 空リスト"""
        pdfs = []
        
        with patch('src.drive.school_rules_collector.settings') as mock_settings:
            mock_settings.batch_mode = True
            result = self.collector.prepare_for_gemini_processing(pdfs)
        
        assert result["schools"] == []
        assert result["metadata"]["total_schools"] == 0
        assert result["metadata"]["total_pdfs"] == 0
        assert result["metadata"]["collection_mode"] == "一括収集"
    
    def test_prepare_for_gemini_processing_cross_ward_schools(self):
        """Gemini処理用データ準備テスト - 同名学校が異なる区にある場合"""
        pdfs = [
            SchoolRulePDF(
                ward="渋谷区",
                school="第一中学校",
                file_id="abc123",
                file_name="校則.pdf",
                file_size_mb=1.5,
                file_path="渋谷区/第一中学校/校則.pdf",
                web_view_link="https://drive.google.com/file/d/abc123/view",
                created_time="2025-01-01T00:00:00.000Z",
                modified_time="2025-01-01T00:00:00.000Z"
            ),
            SchoolRulePDF(
                ward="新宿区",
                school="第一中学校",
                file_id="def456",
                file_name="校則.pdf",
                file_size_mb=2.0,
                file_path="新宿区/第一中学校/校則.pdf",
                web_view_link="https://drive.google.com/file/d/def456/view",
                created_time="2025-01-02T00:00:00.000Z",
                modified_time="2025-01-02T00:00:00.000Z"
            )
        ]
        
        with patch('src.drive.school_rules_collector.settings') as mock_settings:
            mock_settings.batch_mode = True
            result = self.collector.prepare_for_gemini_processing(pdfs)
        
        # 同名でも区が違えば別学校として扱われる
        schools = result["schools"]
        assert len(schools) == 2
        
        schools_by_key = {f"{s['ward']}_{s['school']}": s for s in schools}
        assert "渋谷区_第一中学校" in schools_by_key
        assert "新宿区_第一中学校" in schools_by_key
        
        # metadata の検証
        metadata = result["metadata"]
        assert metadata["total_schools"] == 2
        assert metadata["total_pdfs"] == 2


class TestCreateSchoolRulesCollector:
    """create_school_rules_collector 関数のテスト"""
    
    def test_create_school_rules_collector(self):
        """ファクトリー関数のテスト"""
        mock_drive_client = Mock()
        collector = create_school_rules_collector(mock_drive_client)
        
        assert isinstance(collector, SchoolRulesCollector)
        assert collector.drive_client == mock_drive_client


class TestSchoolRulesCollectorEdgeCases:
    """エッジケースのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.mock_drive_client = Mock()
        self.collector = SchoolRulesCollector(self.mock_drive_client)
    
    def test_ward_filtering_case_sensitivity(self):
        """区名フィルタリングの大文字小文字チェック"""
        # 東京23区リストは正確な文字列でのみマッチすることを確認
        test_wards = ["渋谷区", "SHIBUYA区", "しぶや区", "渋谷", "渋谷区　"]
        
        valid_wards = [ward for ward in test_wards if ward in self.collector.tokyo_wards]
        
        assert valid_wards == ["渋谷区"]  # 完全一致のみ
    
    def test_school_key_generation(self):
        """学校キー生成の一意性テスト"""
        pdfs = [
            SchoolRulePDF(
                ward="渋谷区",
                school="第一中学校",
                file_id="abc123",
                file_name="校則.pdf",
                file_size_mb=1.5,
                file_path="渋谷区/第一中学校/校則.pdf",
                web_view_link="",
                created_time="",
                modified_time=""
            ),
            SchoolRulePDF(
                ward="渋谷区",
                school="第一中学校",  # 同じ学校
                file_id="def456",
                file_name="生活指導.pdf",
                file_size_mb=2.0,
                file_path="渋谷区/第一中学校/生活指導.pdf",
                web_view_link="",
                created_time="",
                modified_time=""
            ),
            SchoolRulePDF(
                ward="新宿区",
                school="第一中学校",  # 同名だが異なる区
                file_id="ghi789",
                file_name="校則.pdf",
                file_size_mb=1.8,
                file_path="新宿区/第一中学校/校則.pdf",
                web_view_link="",
                created_time="",
                modified_time=""
            )
        ]
        
        with patch('src.drive.school_rules_collector.settings') as mock_settings:
            mock_settings.batch_mode = True
            result = self.collector.prepare_for_gemini_processing(pdfs)
        
        schools = result["schools"]
        
        # 渋谷区の第一中学校は2つのPDF
        shibuya_school = next(s for s in schools if s["ward"] == "渋谷区" and s["school"] == "第一中学校")
        assert len(shibuya_school["pdfs"]) == 2
        
        # 新宿区の第一中学校は1つのPDF
        shinjuku_school = next(s for s in schools if s["ward"] == "新宿区" and s["school"] == "第一中学校")
        assert len(shinjuku_school["pdfs"]) == 1
        
        # 合計2つの学校として認識
        assert len(schools) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])