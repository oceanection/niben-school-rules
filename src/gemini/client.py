"""
Gemini API クライアント

Google Gemini APIとの通信を管理
"""

import time
import logging
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core import exceptions as google_exceptions

from config.settings import settings


@dataclass
class GeminiRequest:
    """Gemini API リクエストデータ"""
    prompt: str
    file_content: Optional[bytes] = None
    file_name: Optional[str] = None
    temperature: Optional[float] = None  # Noneの場合は設定値を使用
    max_output_tokens: Optional[int] = None  # Noneの場合は設定値を使用


@dataclass
class GeminiResponse:
    """Gemini API レスポンスデータ"""
    content: str
    finish_reason: str
    usage_metadata: Optional[Dict[str, Any]] = None
    safety_ratings: Optional[Dict[str, Any]] = None
    request_time: Optional[float] = None


class GeminiClient:
    """Google Gemini API クライアント"""
    
    def __init__(self):
        self.model = None
        self.logger = logging.getLogger(__name__)
        self._configure()
    
    def _configure(self):
        """Gemini API の設定"""
        try:
            if not settings.gemini_api_key:
                raise ValueError("Gemini API キーが設定されていません")
            
            # API キーを設定
            genai.configure(api_key=settings.gemini_api_key)
            
            # モデルを初期化（デフォルト設定）
            self.model = genai.GenerativeModel(
                model_name=settings.gemini_model,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.gemini_temperature,
                    top_p=settings.gemini_top_p,
                    top_k=settings.gemini_top_k,
                    max_output_tokens=settings.gemini_max_output_tokens
                ),
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            self.logger.info("Gemini API クライアントを初期化しました")
            
        except Exception as e:
            self.logger.error(f"Gemini API 初期化に失敗: {str(e)}")
            raise ConnectionError(f"Gemini API 初期化に失敗: {str(e)}")
    
    def analyze_pdf_content(self, request: GeminiRequest) -> GeminiResponse:
        """
        PDF内容を分析
        
        Args:
            request: Gemini リクエストデータ
            
        Returns:
            Gemini レスポンスデータ
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"PDF分析開始: {request.file_name}")
            
            # PDFファイルをアップロード
            if request.file_content and request.file_name:
                uploaded_file = self._upload_file(request.file_content, request.file_name)
                
                # プロンプトとファイルを含むコンテンツを作成
                content = [
                    request.prompt,
                    uploaded_file
                ]
            else:
                # テキストのみの場合
                content = request.prompt
            
            # 動的な設定でAPIリクエストを送信
            response = self.model.generate_content(
                content,
                generation_config=genai.types.GenerationConfig(
                    temperature=request.temperature if request.temperature is not None else settings.gemini_temperature,
                    max_output_tokens=request.max_output_tokens if request.max_output_tokens is not None else settings.gemini_max_output_tokens,
                    top_p=settings.gemini_top_p,
                    top_k=settings.gemini_top_k
                )
            )
            
            # レスポンスの確認
            if not response.text:
                raise ValueError("Gemini から空のレスポンスが返されました")
            
            # PDFファイルを削除（リソース管理）
            if request.file_content and request.file_name:
                self._cleanup_uploaded_file(uploaded_file)
            
            elapsed_time = time.time() - start_time
            
            self.logger.info(f"PDF分析完了: {request.file_name} ({elapsed_time:.2f}秒)")
            
            return GeminiResponse(
                content=response.text,
                finish_reason=response.candidates[0].finish_reason.name if response.candidates else "UNKNOWN",
                usage_metadata=self._extract_usage_metadata(response),
                safety_ratings=None,
                request_time=elapsed_time
            )
            
        except google_exceptions.ResourceExhausted as e:
            self.logger.error(f"Gemini API クォータ制限: {str(e)}")
            raise ConnectionError(f"Gemini API クォータ制限に達しました: {str(e)}")
            
        except google_exceptions.InvalidArgument as e:
            self.logger.error(f"Gemini API 引数エラー: {str(e)}")
            raise ValueError(f"Gemini API への引数が不正です: {str(e)}")
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.logger.error(f"PDF分析エラー: {request.file_name} ({elapsed_time:.2f}秒) - {str(e)}")
            raise ConnectionError(f"Gemini API エラー: {str(e)}")
    
    def _upload_file(self, file_content: bytes, file_name: str) -> Any:
        """
        ファイルを Gemini にアップロード
        
        Args:
            file_content: ファイル内容
            file_name: ファイル名
            
        Returns:
            アップロードされたファイルオブジェクト
        """
        try:
            # 一時的にファイルを保存してアップロード
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                uploaded_file = genai.upload_file(
                    path=temp_file_path,
                    display_name=file_name
                )
                
                # ファイルの処理完了を待機
                while uploaded_file.state.name == "PROCESSING":
                    time.sleep(1)
                    uploaded_file = genai.get_file(uploaded_file.name)
                
                if uploaded_file.state.name == "FAILED":
                    raise ValueError(f"ファイルアップロードに失敗: {file_name}")
                
                return uploaded_file
                
            finally:
                # 一時ファイルを削除
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.logger.error(f"ファイルアップロードエラー: {file_name} - {str(e)}")
            raise ConnectionError(f"ファイルアップロードに失敗: {str(e)}")
    
    def _cleanup_uploaded_file(self, uploaded_file: Any):
        """
        アップロードされたファイルを削除
        
        Args:
            uploaded_file: アップロードされたファイルオブジェクト
        """
        try:
            genai.delete_file(uploaded_file.name)
            self.logger.debug(f"アップロードファイルを削除: {uploaded_file.display_name}")
        except Exception as e:
            self.logger.warning(f"アップロードファイル削除に失敗: {str(e)}")
    
    def _extract_usage_metadata(self, response: Any) -> Optional[Dict[str, Any]]:
        """
        使用量メタデータを抽出
        
        Args:
            response: Gemini レスポンス
            
        Returns:
            使用量メタデータ
        """
        try:
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                return {
                    "prompt_token_count": getattr(usage, 'prompt_token_count', 0),
                    "candidates_token_count": getattr(usage, 'candidates_token_count', 0),
                    "total_token_count": getattr(usage, 'total_token_count', 0)
                }
        except Exception as e:
            self.logger.warning(f"使用量メタデータ抽出に失敗: {str(e)}")
        
        return None
    
    def test_connection(self) -> bool:
        """
        Gemini API 接続テスト
        
        Returns:
            接続成功可否
        """
        try:
            # 簡単なテストリクエストを送信
            test_request = GeminiRequest(
                prompt="これはテストです。'OK'とだけ返答してください。",
                temperature=0.0,
                max_output_tokens=10
            )
            
            response = self.model.generate_content(
                test_request.prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=test_request.temperature,
                    max_output_tokens=test_request.max_output_tokens
                )
            )
            
            self.logger.info("Gemini API 接続テスト成功")
            return True
            
        except Exception as e:
            self.logger.error(f"Gemini API 接続テスト失敗: {str(e)}")
            return False


def create_gemini_client() -> GeminiClient:
    """Gemini クライアントインスタンスを作成"""
    return GeminiClient()