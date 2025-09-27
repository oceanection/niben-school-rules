"""
gemini/client.py の純粋な単体テスト

prompt_manager.py や response_parser.py との依存関係を除外
PDFアップロード機能も統合テストで実施
"""

import pytest
import time
import os
from unittest.mock import Mock, patch, MagicMock

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
        assert request.temperature is None  # 設定値を使用
        assert request.max_output_tokens is None  # 設定値を使用


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
    """GeminiClient クラスのテスト（純粋な単体テスト）"""
    
    @classmethod
    def setup_class(cls):
        """テストクラス全体の前処理"""
        # Gemini API キーの存在確認
        if not settings.gemini_api_key:
            pytest.skip("GEMINI_API_KEY が設定されていません。単体テストをスキップします。")
        
        print(f"使用モデル: {settings.gemini_model}")
    
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
        assert result is True, "Gemini API への接続に失敗しました"
    
    def test_analyze_simple_text_only_content(self):
        """シンプルなテキストのみの分析テスト"""
        request = GeminiRequest(
            prompt="「OK」とだけ答えてください。",
            temperature=0.0,
            max_output_tokens=20
        )
        
        response = self.client.analyze_pdf_content(request)
        
        # レスポンスの基本検証
        assert isinstance(response, GeminiResponse)
        assert response.content is not None
        assert len(response.content.strip()) > 0
        assert response.finish_reason is not None
        assert isinstance(response.request_time, float)
        assert response.request_time > 0
    
    def test_analyze_with_different_parameters(self):
        """異なるパラメータでの分析テスト"""
        request = GeminiRequest(
            prompt="1から3の数字を一つ選んでください。",
            temperature=0.5,
            max_output_tokens=50
        )
        
        response = self.client.analyze_pdf_content(request)
        
        # レスポンスの基本検証
        assert response.content is not None
        assert len(response.content) > 0
        
        # 数字が含まれているかの基本的な確認
        assert any(str(i) in response.content for i in range(1, 4))
    
    def test_extract_usage_metadata_with_mock(self):
        """使用量メタデータ抽出テスト（モック使用）"""
        # モックレスポンスを作成
        mock_response = MagicMock()
        mock_usage = MagicMock()
        mock_usage.prompt_token_count = 150
        mock_usage.candidates_token_count = 75
        mock_usage.total_token_count = 225
        mock_response.usage_metadata = mock_usage
        
        usage_metadata = self.client._extract_usage_metadata(mock_response)
        
        assert usage_metadata is not None
        assert usage_metadata["prompt_token_count"] == 150
        assert usage_metadata["candidates_token_count"] == 75
        assert usage_metadata["total_token_count"] == 225
    
    def test_extract_usage_metadata_missing_attribute(self):
        """使用量メタデータが存在しない場合のテスト"""
        mock_response = MagicMock()
        # usage_metadata属性を削除
        if hasattr(mock_response, 'usage_metadata'):
            delattr(mock_response, 'usage_metadata')
        
        usage_metadata = self.client._extract_usage_metadata(mock_response)
        
        assert usage_metadata is None
    
    def test_extract_usage_metadata_exception_handling(self):
        """使用量メタデータ抽出時の例外処理テスト"""
        mock_response = MagicMock()
        
        # 例外を発生させるモック
        def raise_exception(*args, **kwargs):
            raise AttributeError("Test exception")
        
        mock_response.usage_metadata = MagicMock(side_effect=raise_exception)
        
        # 例外が発生してもNoneが返されることを確認
        usage_metadata = self.client._extract_usage_metadata(mock_response)
        assert usage_metadata is None
    
    def test_different_temperature_values(self):
        """異なる temperature 値でのテスト"""
        base_prompt = "「A」または「B」を選んでください。"
        
        # デフォルト設定を使用（.env値）
        request_default = GeminiRequest(prompt=base_prompt)
        response_default = self.client.analyze_pdf_content(request_default)
        
        # 明示的に低い temperature を指定
        request_low = GeminiRequest(
            prompt=base_prompt, 
            temperature=0.0, 
            max_output_tokens=10
        )
        response_low = self.client.analyze_pdf_content(request_low)
        
        # 明示的に高い temperature を指定
        request_high = GeminiRequest(
            prompt=base_prompt, 
            temperature=0.9, 
            max_output_tokens=10
        )
        response_high = self.client.analyze_pdf_content(request_high)
        
        # 全て正常にレスポンスが返ることを確認
        assert response_default.content is not None
        assert response_low.content is not None
        assert response_high.content is not None
        assert len(response_default.content.strip()) > 0
        assert len(response_low.content.strip()) > 0
        assert len(response_high.content.strip()) > 0
    
    def test_max_output_tokens_settings(self):
        """max_output_tokens 設定のテスト"""
        prompt = "短く答えてください。"
        
        # 短い制限
        request_short = GeminiRequest(
            prompt=prompt, 
            temperature=0.1, 
            max_output_tokens=10
        )
        response_short = self.client.analyze_pdf_content(request_short)
        
        # 長い制限
        request_long = GeminiRequest(
            prompt=prompt, 
            temperature=0.1, 
            max_output_tokens=100
        )
        response_long = self.client.analyze_pdf_content(request_long)
        
        # 両方とも正常にレスポンスが返ることを確認
        assert response_short.content is not None
        assert response_long.content is not None
        assert len(response_short.content) > 0
        assert len(response_long.content) > 0
    
    def test_request_time_measurement(self):
        """リクエスト時間測定テスト"""
        request = GeminiRequest(
            prompt="すぐに「はい」と答えてください。",
            temperature=0.0,
            max_output_tokens=5
        )
        
        start_time = time.time()
        response = self.client.analyze_pdf_content(request)
        end_time = time.time()
        
        # リクエスト時間が測定されていることを確認
        assert response.request_time is not None
        assert isinstance(response.request_time, float)
        assert response.request_time > 0
        
        # 実際の経過時間との比較（2秒以内の誤差許容）
        actual_time = end_time - start_time
        time_diff = abs(response.request_time - actual_time)
        assert time_diff < 2.0, f"時間測定の誤差が大きすぎます: {time_diff}秒"


class TestGeminiClientErrorHandling:
    """エラーハンドリングのテスト"""
    
    def test_missing_api_key_initialization(self):
        """APIキー未設定時の初期化エラーテスト"""
        # 環境変数を一時的に保存・クリア
        original_key = os.environ.get('GEMINI_API_KEY')
        
        try:
            # 環境変数をクリア
            if 'GEMINI_API_KEY' in os.environ:
                del os.environ['GEMINI_API_KEY']
            
            # 設定のモック
            with patch('src.gemini.client.settings') as mock_settings:
                mock_settings.gemini_api_key = None
                mock_settings.gemini_model = "models/gemini-2.5-flash"
                
                with pytest.raises(ValueError, match="Gemini API キーが設定されていません"):
                    GeminiClient()
        
        finally:
            # 環境変数を復元
            if original_key:
                os.environ['GEMINI_API_KEY'] = original_key
    
    @pytest.mark.skipif(not settings.gemini_api_key, reason="Gemini API key not available")
    def test_empty_prompt_error(self):
        """空のプロンプトでのエラーテスト"""
        client = create_gemini_client()
        request = GeminiRequest(prompt="", temperature=0.1, max_output_tokens=10)
        
        # 空のプロンプトはエラーになることを期待
        with pytest.raises(ConnectionError):
            client.analyze_pdf_content(request)
    
    @pytest.mark.skipif(not settings.gemini_api_key, reason="Gemini API key not available")
    def test_invalid_model_configuration(self):
        """無効なモデル設定でのエラーテスト"""
        # 無効なモデル名で初期化を試行
        with patch('src.gemini.client.settings') as mock_settings:
            mock_settings.gemini_api_key = settings.gemini_api_key
            mock_settings.gemini_model = "invalid-model-name"
            
            # 初期化時または最初のAPI呼び出し時にエラーが発生することを期待
            try:
                client = GeminiClient()
                # API呼び出しでエラーが発生する場合
                request = GeminiRequest(prompt="テスト", max_output_tokens=10)
                with pytest.raises(ConnectionError):
                    client.analyze_pdf_content(request)
            except (ConnectionError, ValueError):
                # 初期化時にエラーが発生する場合も想定内
                pass


class TestCreateGeminiClient:
    """create_gemini_client ファクトリー関数のテスト"""
    
    @pytest.mark.skipif(not settings.gemini_api_key, reason="Gemini API key not available")
    def test_create_gemini_client_factory(self):
        """ファクトリー関数のテスト"""
        client = create_gemini_client()
        
        assert isinstance(client, GeminiClient)
        assert client.model is not None
        assert hasattr(client, 'logger')


class TestGeminiClientBasicFunctionality:
    """基本機能のテスト（依存関係なし）"""
    
    @pytest.mark.skipif(not settings.gemini_api_key, reason="Gemini API key not available")
    def test_simple_question_answer(self):
        """シンプルな質問応答テスト"""
        client = create_gemini_client()
        
        request = GeminiRequest(
            prompt="2+2はいくつですか？数字だけで答えてください。",
            temperature=0.0,
            max_output_tokens=10
        )
        
        response = client.analyze_pdf_content(request)
        
        # 基本的なレスポンス検証
        assert response.content is not None
        assert "4" in response.content
        
        # 使用量メタデータの確認
        if response.usage_metadata:
            assert response.usage_metadata["total_token_count"] > 0
    
    @pytest.mark.skipif(not settings.gemini_api_key, reason="Gemini API key not available")
    def test_finish_reason_capture(self):
        """finish_reason の捕捉テスト"""
        client = create_gemini_client()
        
        request = GeminiRequest(
            prompt="「完了」と言ってください。",
            temperature=0.0,
            max_output_tokens=50
        )
        
        response = client.analyze_pdf_content(request)
        
        # finish_reason が設定されていることを確認
        assert response.finish_reason is not None
        assert isinstance(response.finish_reason, str)
        # 通常は "STOP" が返される
        assert response.finish_reason in ["STOP", "MAX_TOKENS", "SAFETY", "RECITATION", "OTHER"]


class TestGeminiClientParameterValidation:
    """Gemini パラメータ設定の検証テスト"""
    
    @pytest.mark.skipif(not settings.gemini_api_key, reason="Gemini API key not available")
    def test_env_parameter_usage(self):
        """環境変数設定パラメータの使用確認テスト"""
        client = create_gemini_client()
        
        # 設定値の確認
        print(f"GEMINI_TEMPERATURE: {settings.gemini_temperature}")
        print(f"GEMINI_MAX_OUTPUT_TOKENS: {settings.gemini_max_output_tokens}")
        print(f"GEMINI_TOP_P: {settings.gemini_top_p}")
        print(f"GEMINI_TOP_K: {settings.gemini_top_k}")
        
        # 設定値の妥当性確認
        assert 0.0 <= settings.gemini_temperature <= 1.0
        assert settings.gemini_max_output_tokens > 0
        assert 0.0 <= settings.gemini_top_p <= 1.0
        assert settings.gemini_top_k > 0
        
        # デフォルト設定でのAPIテスト
        request = GeminiRequest(prompt="設定テストです。「OK」と答えてください。")
        response = client.analyze_pdf_content(request)
        
        assert response.content is not None
        assert len(response.content) > 0
    
    @pytest.mark.skipif(not settings.gemini_api_key, reason="Gemini API key not available")  
    def test_token_limit_effectiveness(self):
        """トークン制限の効果確認テスト"""
        client = create_gemini_client()
        
        # 短いトークン制限
        request_short = GeminiRequest(
            prompt="1から100まで数えてください。",
            max_output_tokens=50
        )
        response_short = client.analyze_pdf_content(request_short)
        
        # 設定値でのトークン制限
        request_default = GeminiRequest(
            prompt="1から100まで数えてください。"
        )
        response_default = client.analyze_pdf_content(request_default)
        
        # 短い制限の方が短いレスポンスになることを期待
        assert response_short.content is not None
        assert response_default.content is not None
        assert len(response_short.content) <= len(response_default.content)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])