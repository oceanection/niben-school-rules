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
        
        # モデル名の正規化（重複prefix除去）
        if model_name.startswith('models/models/'):
            model_name = model_name.replace('models/models/', 'models/')
        elif not model_name.startswith('models/'):
            model_name = f"models/{model_name}"
            
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
            
            # 最新のGemini APIのファイルアップロード方法を試行
            try:
                import tempfile
                import os
                
                # 一時ファイルに保存してアップロード
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    temp_file.write(pdf_content)
                    temp_file_path = temp_file.name
                
                try:
                    uploaded_file = genai.upload_file(
                        path=temp_file_path,
                        mime_type="application/pdf",
                        display_name=file_name
                    )
                    self.logger.debug(f"PDFアップロード完了: {file_name}")
                    return uploaded_file
                finally:
                    # 一時ファイルを削除
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                        
            except (AttributeError, TypeError) as e:
                self.logger.warning(f"upload_file API使用失敗: {e}")
                
                # フォールバック: 直接バイトデータでの分析
                self.logger.warning(f"フォールバック: 直接分析を試行: {file_name}")
                
                # PDFバイトデータを直接使用
                import base64
                pdf_data = {
                    "mime_type": "application/pdf",
                    "data": base64.b64encode(pdf_content).decode()
                }
                return pdf_data
            
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
            # 実際のプロンプト構造に対応
            if 'school_rules_analysis' in self.prompt_templates:
                analysis_prompts = self.prompt_templates['school_rules_analysis']
                system_prompt = analysis_prompts['system']
                user_prompt_template = analysis_prompts['user']
            else:
                # フォールバック: 旧形式
                system_prompt = self.prompt_templates['system_prompts']['school_rules_analysis']
                user_prompt_template = self.prompt_templates['user_prompts']['analyze_pdf']
            
            # ファイル名のみを安全に置換
            user_prompt = user_prompt_template.format(file_name=file_name)
            
            return {
                'system': system_prompt,
                'user': user_prompt
            }
            
        except KeyError as e:
            error_msg = f"プロンプトテンプレートキーが見つかりません: {e}"
            self.logger.error(error_msg)
            self.logger.error(f"利用可能なキー: {list(self.prompt_templates.keys())}")
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