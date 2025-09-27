"""
設定管理モジュール

環境変数からの基本設定読み込み
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートディレクトリの特定
PROJECT_ROOT = Path(__file__).parent.parent

# .envファイルの読み込み
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path)


class Settings:
    """設定管理クラス"""
    
    def __init__(self):
        # Google API設定
        self.google_application_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.spreadsheet_id = os.getenv("SPREADSHEET_ID")

        # Google Drive処理モード設定
        self.batch_mode = os.getenv("BATCH_MODE", "false").lower() == "true"
        self.root_folder_id = os.getenv("ROOT_FOLDER_ID")  # 一括処理時: 2025_校則 フォルダ
        self.ward_folder_id = os.getenv("WARD_FOLDER_ID")  # 個別処理時: 区フォルダ

        # Gemini API設定
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")

        gemini_temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.1"))
        gemini_max_output_tokens = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "6144"))
        gemini_top_p = float(os.getenv("GEMINI_TOP_P", "0.85"))
        gemini_top_k = int(os.getenv("GEMINI_TOP_K", "50"))
        
        # プロジェクト設定
        self.project_root = PROJECT_ROOT
        self.prompt_template_file = PROJECT_ROOT / "src" / "prompts" / "prompts_templates.yaml"
        
        # テスト用設定
        self.test_data_dir = PROJECT_ROOT / "tests" / "test_data"
        self.test_input_dir = self.test_data_dir / "input"
        self.test_expected_dir = self.test_data_dir / "expected"
        self.test_output_dir = PROJECT_ROOT / "logs" / "test_results"


# モジュールレベルの設定インスタンス
settings = Settings()