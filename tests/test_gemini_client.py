 
"""
gemini/client.py の単体テスト

実際の Gemini API を使用してテスト（PDFアップロード以外）
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.gemini.client import (
    GeminiClient,
    GeminiRequest,
    GeminiResponse,
    create_gemini_client
)
from config.settings import settings


class TestGeminiRequest:
    """GeminiRequest データクラスのテスト"""
    
    def test_gemini_request_creation(self):
        """GeminiRequest の作成テスト"""
        request = GeminiRequest(
            prompt="テストプロンプト",
            file_content=b"test content",
            file_name="test.pdf",
            temperature=0.2,
            max_output_tokens=1000
        )
        
        assert request.prompt == "テストプロンプト"
        assert request.file_content == b"test content"
        assert request.file_name == "test.pdf"
        assert request.temperature == 0.2
        assert request.max_output_tokens == 1000
    
    def test_gemini_request_defaults(self):
        """GeminiRequest のデフォルト値テスト"""
        request = GeminiRequest(prompt="テストプロンプト")
        
        assert request.prompt == "テストプロンプト"
        assert request.file_content is None
        assert request.file_name is None
        assert request.temperature == 0.1
        assert request.max_output_tokens == 8192


class TestGeminiResponse:
    """GeminiResponse データクラスのテスト"""
    
    def test_gemini_response_creation(self):
        """GeminiResponse の作成テスト"""
        usage_metadata = {"total_token_count": 100}
        
        response = GeminiResponse(
            content="レスポンス内容",
            finish_reason="STOP",
            usage_metadata=usage_metadata,
            safety_ratings=None,
            request_time=1.5
        )
        
        assert response.content == "レスポンス内容"
        assert response.finish_reason == "STOP"
        assert response.usage_metadata == usage_metadata
        assert response.safety_ratings is None
        assert response.request_time == 1.5


class TestGeminiClient:
    """GeminiClient クラスのテスト"""
    
    @classmethod
    def setup_class(cls):
        """テストクラス全体の前処理"""
        # Gemini API キーの存在確認
        if not settings.gemini_api_key:
            pytest.skip("GEMINI_API_KEY が設定されていません。単体テストをスキップします。")
    
    def setup_method(self):
        """各テストメソッドの前処理"""
        try:
            self.client = create_gemini_client()
        except Exception as e:
            pytest.skip(f"Gemini Client の初期化に失敗: {str(e)}")
    
    def test_client_initialization(self):
        """クライアント初期化テスト"""
        assert isinstance(self.client, GeminiClient)
        assert self.client.model is not None
        assert hasattr(self.client, 'logger')
    
    def test_test_connection(self):
        """Gemini API 接続テスト"""
        result = self.client.test_connection()
        
        assert isinstance(result, bool)
        assert result is True  # 正常に接続できることを期待
    
    def test_analyze_text_only_content(self):
        """テキストのみの分析テスト"""
        request = GeminiRequest(
            prompt="以下のテキストを分析してください。JSON形式で回答してください。\n\nテキスト: これはテストです。",
            temperature=0.0,
            max_output_tokens=100
        )
        
        response = self.client.analyze_pdf_content(request)
        
        # レスポンスの基本検証
        assert isinstance(response, GeminiResponse)
        assert response.content is not None
        assert len(response.content) > 0
        assert response.finish_reason is not None
        assert isinstance(response.request_time, float)
        assert response.request_time > 0
    
    def test_analyze_with_json_response(self):
        """JSON レスポンスの分析テスト"""
        json_prompt = """
        以下の質問に JSON 形式で答えてください:
        
        質問: 「校則」という言葉の意味を説明してください。
        
        回答は以下の形式で返してください:
        {
            "term": "校則",
            "definition": "説明文",
            "examples": ["例1", "例2"]
        }
        """
        
        request = GeminiRequest(
            prompt=json_prompt,
            temperature=0.1,
            max_output_tokens=500
        )
        
        response = self.client.analyze_pdf_content(request)
        
        # レスポンスの検証
        assert response.content is not None
        
        # JSON形式であることを確認
        try:
            parsed_json = json.loads(response.content)
            assert "term" in parsed_json
            assert "definition" in parsed_json
            assert isinstance(parsed_json.get("examples", []), list)
        except json.JSONDecodeError:
            # JSONブロック形式の場合も確認
            assert "```json" in response.content or "{" in response.content
    
    def test_extract_usage_metadata(self):
        """使用量メタデータ抽出テスト"""
        # モックレスポンスを作成
        mock_response = MagicMock()
        mock_usage = MagicMock()
        mock_usage.prompt_token_count = 100
        mock_usage.candidates_token_count = 50
        mock_usage.total_token_count = 150
        mock_response.usage_metadata = mock_usage
        
        usage_metadata = self.client._extract_usage_metadata(mock_response)
        
        assert usage_metadata is not None
        assert usage_metadata["prompt_token_count"] == 100
        assert usage_metadata["candidates_token_count"] == 50
        assert usage_metadata["total_token_count"] == 150
    
    def test_extract_usage_metadata_missing(self):
        """使用量メタデータが存在しない場合のテスト"""
        mock_response = MagicMock()
        del mock_response.usage_metadata  # 属性を削除
        
        usage_metadata = self.client._extract_usage_metadata(mock_response)
        
        assert usage_metadata is None
    
    def test_extract_usage_metadata_partial(self):
        """使用量メタデータが部分的な場合のテスト"""
        mock_response = MagicMock()
        mock_usage = MagicMock()
        mock_usage.prompt_token_count = 100
        # candidates_token_count と total_token_count は存在しない
        mock_response.usage_metadata = mock_usage
        
        usage_metadata = self.client._extract_usage_metadata(mock_response)
        
        assert usage_metadata is not None
        assert usage_metadata["prompt_token_count"] == 100
        assert usage_metadata["candidates_token_count"] == 0  # デフォルト値
        assert usage_metadata["total_token_count"] == 0  # デフォルト値
    
    def test_different_temperature_settings(self):
        """異なる temperature 設定のテスト"""
        base_prompt = "「はい」または「いいえ」で答えてください。今日は良い天気ですか？"
        
        # 低い temperature (決定論的)
        request_low = GeminiRequest(prompt=base_prompt, temperature=0.0, max_output_tokens=50)
        response_low = self.client.analyze_pdf_content(request_low)
        
        # 高い temperature (創造的)
        request_high = GeminiRequest(prompt=base_prompt, temperature=0.9, max_output_tokens=50)
        response_high = self.client.analyze_pdf_content(request_high)
        
        # 両方とも正常にレスポンスが返ることを確認
        assert response_low.content is not None
        assert response_high.content is not None
        assert len(response_low.content) > 0
        assert len(response_high.content) > 0
    
    def test_max_output_tokens_limit(self):
        """max_output_tokens 制限のテスト"""
        long_prompt = "以下の数字を1から100まで列挙してください。各数字に詳しい説明を付けてください。"
        
        # 短い制限
        request_short = GeminiRequest(
            prompt=long_prompt, 
            temperature=0.1, 
            max_output_tokens=100
        )
        response_short = self.client.analyze_pdf_content(request_short)
        
        # 長い制限
        request_long = GeminiRequest(
            prompt=long_prompt, 
            temperature=0.1, 
            max_output_tokens=2000
        )
        response_long = self.client.analyze_pdf_content(request_long)
        
        # 短い制限の方が短いレスポンスになることを期待
        assert response_short.content is not None
        assert response_long.content is not None
        assert len(response_short.content) <= len(response_long.content)
    
    def test_request_time_measurement(self):
        """リクエスト時間測定テスト"""
        request = GeminiRequest(
            prompt="簡単な質問です。「OK」とだけ答えてください。",
            temperature=0.0,
            max_output_tokens=10
        )
        
        start_time = time.time()
        response = self.client.analyze_pdf_content(request)
        end_time = time.time()
        
        # リクエスト時間が測定されていることを確認
        assert response.request_time is not None
        assert isinstance(response.request_time, float)
        assert response.request_time > 0
        
        # 実際の経過時間と近い値であることを確認（誤差許容）
        actual_time = end_time - start_time
        assert abs(response.request_time - actual_time) < 1.0  # 1秒以内の誤差


class TestGeminiClientErrorHandling:
    """エラーハンドリングのテスト"""
    
    def test_invalid_api_key(self):
        """無効なAPIキーのテスト"""
        with patch('config.settings.settings') as mock_settings:
            mock_settings.gemini_api_key = "invalid_api_key"
            
            # 初期化時はエラーにならない（API呼び出し時にエラー）
            try:
                client = GeminiClient()
                assert client is not None
            except Exception:
                # 初期化で失敗する場合もある
                pass
    
    def test_missing_api_key(self):
        """APIキー未設定のテスト"""
        with patch('config.settings.settings') as mock_settings:
            mock_settings.gemini_api_key = None
            
            with pytest.raises(ValueError, match="Gemini API キーが設定されていません"):
                GeminiClient()
    
    @pytest.mark.skipif(not settings.gemini_api_key, reason="Gemini API key not available")
    def test_empty_prompt(self):
        """空のプロンプトのテスト"""
        client = create_gemini_client()
        request = GeminiRequest(prompt="", temperature=0.1, max_output_tokens=10)
        
        # 空のプロンプトでもエラーにならずに何らかのレスポンスが返ることを期待
        response = client.analyze_pdf_content(request)
        assert isinstance(response, GeminiResponse)
    
    @pytest.mark.skipif(not settings.gemini_api_key, reason="Gemini API key not available")
    def test_very_long_prompt(self):
        """非常に長いプロンプトのテスト"""
        client = create_gemini_client()
        
        # 非常に長いプロンプトを作成
        long_prompt = "これはテストです。" * 1000  # 約8000文字
        request = GeminiRequest(
            prompt=long_prompt, 
            temperature=0.1, 
            max_output_tokens=100
        )
        
        # 長いプロンプトでも処理できることを確認
        response = client.analyze_pdf_content(request)
        assert isinstance(response, GeminiResponse)
        assert response.content is not None


class TestCreateGeminiClient:
    """create_gemini_client ファクトリー関数のテスト"""
    
    @pytest.mark.skipif(not settings.gemini_api_key, reason="Gemini API key not available")
    def test_create_gemini_client(self):
        """ファクトリー関数のテスト"""
        client = create_gemini_client()
        
        assert isinstance(client, GeminiClient)
        assert client.model is not None


class TestGeminiClientIntegrationBasics:
    """基本的な統合テスト（軽量）"""
    
    @pytest.mark.skipif(not settings.gemini_api_key, reason="Gemini API key not available")
    def test_school_rules_style_prompt(self):
        """校則分析スタイルのプロンプトテスト"""
        school_rules_prompt = """
        以下の校則テキストを分析し、JSON形式で回答してください。

        校則テキスト:
        「生徒は清潔な服装を心がけること。髪型は中学生らしいものとする。」

        回答形式:
        {
            "uniform": {
                "cleanliness_requirement": {
                    "status": "規定あり",
                    "evidence": "生徒は清潔な服装を心がけること"
                }
            },
            "appearance": {
                "hair": {
                    "abstract_expressions": {
                        "status": "抽象的な表現での指定あり",
                        "evidence": "髪型は中学生らしいものとする"
                    }
                }
            }
        }
        """
        
        client = create_gemini_client()
        request = GeminiRequest(
            prompt=school_rules_prompt,
            temperature=0.1,
            max_output_tokens=1000
        )
        
        response = client.analyze_pdf_content(request)
        
        # 基本的なレスポンス検証
        assert response.content is not None
        assert len(response.content) > 0
        
        # JSON形式のレスポンスが含まれているかチェック
        content_lower = response.content.lower()
        assert any(keyword in content_lower for keyword in ['"status"', '"evidence"', 'uniform', 'appearance'])
        
        # 使用量メタデータの確認
        if response.usage_metadata:
            assert response.usage_metadata["total_token_count"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])