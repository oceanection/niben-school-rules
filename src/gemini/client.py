"""
PDF学校規則分析専用 Gemini API クライアント
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core import exceptions as google_exceptions


class GeminiClient:
    """
    PDF学校規則分析専用のGemini APIクライアント
    責任範囲：PDFアップロード、プロンプト管理、API呼び出し
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-pro"):
        """
        クライアントを初期化
        
        Args:
            api_key: Gemini APIキー
            model_name: 使用するモデル名
        """
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.model_name = model_name
        
        # Gemini APIを設定
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=model_name,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        # プロンプトテンプレートを読み込み
        self._load_prompts()
        
        self.logger.info(f"Gemini クライアント初期化完了 (モデル: {model_name})")
    
    def analyze_pdf(self, pdf_content: bytes, file_name: str) -> str:
        """
        PDF学校規則文書を分析してJSON形式の結果を取得
        
        Args:
            pdf_content: PDFファイルの内容（バイト形式）
            file_name: PDFファイル名
            
        Returns:
            str: Gemini APIからの生レスポンステキスト（JSON形式を期待）
            
        Raises:
            ConnectionError: API接続エラー
            ValueError: PDFアップロードエラー
        """
        try:
            self.logger.info(f"PDF分析開始: {file_name}")
            
            # 1. PDFをGemini APIにアップロード
            uploaded_file = self._upload_pdf(pdf_content, file_name)
            
            # 2. プロンプトを構築
            prompts = self._build_prompts(file_name)
            
            # 3. Gemini APIで分析実行
            response = self.model.generate_content([
                prompts['system'],
                prompts['user'], 
                uploaded_file
            ])
            
            # 4. レスポンスチェック
            if not response.text:
                raise ValueError("空のレスポンスが返されました")
            
            self.logger.info(f"PDF分析完了: {file_name}")
            return response.text
            
        except google_exceptions.ResourceExhausted as e:
            error_msg = f"Gemini API クォータ制限: {str(e)}"
            self.logger.error(f"クォータエラー: {file_name} - {error_msg}")
            raise ConnectionError(error_msg)
            
        except google_exceptions.GoogleAPICallError as e:
            error_msg = f"Gemini API エラー: {str(e)}"
            self.logger.error(f"APIエラー: {file_name} - {error_msg}")
            raise ConnectionError(error_msg)
            
        except Exception as e:
            error_msg = f"PDF分析エラー: {str(e)}"
            self.logger.error(f"分析エラー: {file_name} - {error_msg}")
            raise ValueError(error_msg)
    
    def _upload_pdf(self, pdf_content: bytes, file_name: str) -> object:
        """
        PDFをGemini APIにアップロード
        
        Args:
            pdf_content: PDFファイルの内容
            file_name: ファイル名（ログ用）
            
        Returns:
            アップロードされたファイルオブジェクト
        """
        try:
            self.logger.debug(f"PDFアップロード開始: {file_name}")
            
            uploaded_file = genai.upload_file(
                data=pdf_content,
                mime_type="application/pdf",
                display_name=file_name
            )
            
            self.logger.debug(f"PDFアップロード完了: {file_name}")
            return uploaded_file
            
        except Exception as e:
            error_msg = f"PDFアップロードエラー: {str(e)}"
            self.logger.error(f"アップロードエラー: {file_name} - {error_msg}")
            raise ValueError(error_msg)
    
    def _load_prompts(self):
        """
        prompts_templates.yamlからプロンプトテンプレートを読み込み
        """
        try:
            prompt_file = Path(__file__).parent / "prompts_templates.yaml"
            
            if not prompt_file.exists():
                raise FileNotFoundError(f"プロンプトファイルが見つかりません: {prompt_file}")
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                self.prompt_templates = yaml.safe_load(f)
            
            self.logger.debug("プロンプトテンプレート読み込み完了")
            
        except Exception as e:
            self.logger.error(f"プロンプト読み込みエラー: {e}")
            raise
    
    def _build_prompts(self, file_name: str) -> Dict[str, str]:
        """
        PDF分析用のプロンプトを構築
        
        Args:
            file_name: PDFファイル名
            
        Returns:
            Dict[str, str]: システムプロンプトとユーザープロンプト
        """
        try:
            system_prompt = self.prompt_templates['system_prompts']['school_rules_analysis']
            
            user_prompt_template = self.prompt_templates['user_prompts']['analyze_pdf']
            user_prompt = user_prompt_template.format(
                file_name=file_name
            )
            
            return {
                'system': system_prompt,
                'user': user_prompt
            }
            
        except KeyError as e:
            error_msg = f"プロンプトテンプレートキーが見つかりません: {e}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"プロンプト構築エラー: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
    
    def test_connection(self) -> bool:
        """
        Gemini API接続テスト
        
        Returns:
            bool: 接続成功時True
        """
        try:
            response = self.model.generate_content("テスト")
            return bool(response.text)
        except Exception as e:
            self.logger.error(f"接続テスト失敗: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        使用中のモデル情報を取得
        
        Returns:
            Dict[str, Any]: モデル情報
        """
        try:
            model_info = genai.get_model(f"models/{self.model_name}")
            return {
                'name': model_info.name,
                'display_name': model_info.display_name,
                'description': model_info.description,
                'input_token_limit': model_info.input_token_limit,
                'output_token_limit': model_info.output_token_limit
            }
        except Exception as e:
            self.logger.error(f"モデル情報取得エラー: {str(e)}")
            return {'name': self.model_name, 'error': str(e)}