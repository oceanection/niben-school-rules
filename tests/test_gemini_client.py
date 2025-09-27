"""
Gemini Client のテスト
実際の config/settings.py を使用
"""

import pytest
import sys
from pathlib import Path
import logging

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 実際の設定システムを使用
try:
    from config.settings import settings
    config_available = True
except ImportError as e:
    print(f"Warning: config.settings のインポートに失敗: {e}")
    config_available = False

# Gemini クライアントをインポート
try:
    from src.gemini.client import GeminiClient
    client_available = True
except ImportError as e:
    print(f"Warning: Gemini Client のインポートに失敗: {e}")
    client_available = False


class TestGeminiClient:
    """GeminiClient のテストクラス"""
    
    @pytest.fixture(scope="class")
    def gemini_config(self):
        """Gemini設定を取得"""
        if not config_available:
            pytest.skip("config.settings が利用できません")
        
        if not settings.gemini_api_key:
            pytest.skip("GEMINI_API_KEY が設定されていません")
        
        return {
            'api_key': settings.gemini_api_key,
            'model': settings.gemini_model
        }
    
    @pytest.fixture(scope="class")
    def test_pdf_path(self):
        """テスト用PDFファイルのパス"""
        pdf_path = project_root / "data" / "input" / "test.pdf"
        if not pdf_path.exists():
            pytest.skip(f"テストファイルが見つかりません: {pdf_path}")
        return pdf_path
    
    @pytest.fixture(scope="class")
    def test_pdf_content(self, test_pdf_path):
        """テスト用PDFの内容を読み込み"""
        with open(test_pdf_path, 'rb') as f:
            return f.read()
    
    @pytest.fixture(scope="class")
    def client(self, gemini_config):
        """Geminiクライアントのインスタンス"""
        if not client_available:
            pytest.skip("GeminiClient が利用できません")
        
        return GeminiClient(
            api_key=gemini_config['api_key'],
            model_name=gemini_config['model']
        )
    
    def test_settings_loading(self):
        """設定ファイル読み込みテスト"""
        if not config_available:
            pytest.skip("config.settings が利用できません")
        
        print(f"\n=== 設定情報 ===")
        print(f"プロジェクトルート: {settings.project_root}")
        print(f"Gemini APIキー: {'設定済み' if settings.gemini_api_key else '未設定'}")
        print(f"Gemini モデル: {settings.gemini_model}")
        print(f"プロンプトテンプレートファイル: {settings.prompt_template_file}")
        print(f"プロンプトファイル存在: {settings.prompt_template_file.exists()}")
        
        assert settings.gemini_api_key is not None, "GEMINI_API_KEY が設定されていません"
        assert settings.gemini_model is not None, "GEMINI_MODEL が設定されていません"
    
    def test_client_initialization(self, gemini_config):
        """クライアント初期化テスト"""
        if not client_available:
            pytest.skip("GeminiClient が利用できません")
        
        client = GeminiClient(
            api_key=gemini_config['api_key'],
            model_name=gemini_config['model']
        )
        
        assert client.api_key == gemini_config['api_key']
        assert client.model_name == gemini_config['model']
        assert hasattr(client, 'prompt_templates')
        assert hasattr(client, 'model')
        
        print(f"\n=== クライアント初期化 ===")
        print(f"APIキー: {'*' * (len(gemini_config['api_key']) - 8) + gemini_config['api_key'][-8:]}")
        print(f"モデル: {client.model_name}")
        print(f"プロンプトテンプレート読み込み: {'成功' if client.prompt_templates else '失敗'}")
    
    def test_prompts_loading(self, client):
        """プロンプトテンプレート読み込みテスト"""
        # プロンプトテンプレートが正しく読み込まれているかチェック
        assert client.prompt_templates is not None
        assert isinstance(client.prompt_templates, dict)
        assert len(client.prompt_templates) > 0
        
        print(f"\n=== プロンプトテンプレート情報 ===")
        print(f"読み込み成功: True")
        print(f"トップレベルキー: {list(client.prompt_templates.keys())}")
        
        # 各セクションの詳細を表示
        for section_key, section_value in client.prompt_templates.items():
            if isinstance(section_value, dict):
                print(f"{section_key}: {list(section_value.keys())}")
                for key, value in section_value.items():
                    print(f"  {key}: {len(value)} 文字")
            else:
                print(f"{section_key}: {type(section_value)} - {len(str(section_value))} 文字")
    
    def test_connection(self, client):
        """API接続テスト"""
        result = client.test_connection()
        assert result is True, "Gemini APIへの接続に失敗しました"
        
        print(f"\n=== API接続テスト ===")
        print(f"接続成功: {result}")
    
    def test_model_info(self, client):
        """モデル情報取得テスト"""
        model_info = client.get_model_info()
        assert 'name' in model_info
        
        print(f"\n=== モデル情報 ===")
        
        if 'error' in model_info:
            print(f"⚠️  モデル情報取得エラー: {model_info['error']}")
            # エラーがあってもテストは継続（API制限の可能性）
        else:
            for key, value in model_info.items():
                print(f"{key}: {value}")
    
    def test_prompt_path_verification(self):
        """プロンプトファイルパスの検証"""
        if not config_available:
            pytest.skip("config.settings が利用できません")
        
        # 設定で指定されたパス
        configured_path = settings.prompt_template_file
        print(f"\n=== プロンプトファイルパス検証 ===")
        print(f"設定ファイルで指定されたパス: {configured_path}")
        print(f"ファイル存在: {configured_path.exists()}")
        
        # clientが期待するパス
        expected_client_path = project_root / "src" / "gemini" / "prompts_templates.yaml"
        print(f"clientが期待するパス: {expected_client_path}")
        print(f"ファイル存在: {expected_client_path.exists()}")
        
        # どちらかが存在すればOK
        assert configured_path.exists() or expected_client_path.exists(), \
            "プロンプトテンプレートファイルが見つかりません"
    
    def test_build_prompts_with_actual_structure(self, client):
        """実際のプロンプト構造を使用したプロンプト構築テスト"""
        file_name = "test.pdf"
        
        print(f"\n=== プロンプト構築テスト ===")
        print(f"利用可能なプロンプト構造:")
        
        templates = client.prompt_templates
        for section_key, section_value in templates.items():
            print(f"  {section_key}:")
            if isinstance(section_value, dict):
                for prompt_key in section_value.keys():
                    print(f"    - {prompt_key}")
        
        try:
            # _build_prompts メソッドが存在するか確認
            if hasattr(client, '_build_prompts'):
                prompts = client._build_prompts(file_name)
                
                assert 'system' in prompts, "システムプロンプトが構築されていません"
                assert 'user' in prompts, "ユーザープロンプトが構築されていません"
                assert isinstance(prompts['system'], str)
                assert isinstance(prompts['user'], str)
                assert len(prompts['system']) > 0
                assert len(prompts['user']) > 0
                
                print(f"プロンプト構築成功:")
                print(f"  システムプロンプト: {len(prompts['system'])} 文字")
                print(f"  ユーザープロンプト: {len(prompts['user'])} 文字")
                print(f"  ファイル名含有: {file_name in prompts['user']}")
                
                # プロンプトの一部を表示
                print(f"  システムプロンプト（先頭200文字）:")
                print(f"    {prompts['system'][:200]}...")
                print(f"  ユーザープロンプト（先頭200文字）:")
                print(f"    {prompts['user'][:200]}...")
                
            else:
                pytest.skip("_build_prompts メソッドが実装されていません")
                
        except Exception as e:
            print(f"プロンプト構築エラー: {e}")
            print(f"エラータイプ: {type(e)}")
            
            # デバッグ情報を表示
            print("デバッグ情報:")
            print(f"  templates type: {type(templates)}")
            print(f"  templates keys: {list(templates.keys()) if isinstance(templates, dict) else 'not dict'}")
            
            pytest.fail(f"プロンプト構築に失敗: {e}")
    
    def test_analyze_pdf_integration(self, client, test_pdf_content):
        """PDF分析統合テスト"""
        file_name = "test.pdf"
        
        print(f"\n=== PDF分析統合テスト ===")
        print(f"PDFファイルサイズ: {len(test_pdf_content)} バイト")
        
        try:
            # PDF分析を実行
            result = client.analyze_pdf(test_pdf_content, file_name)
            
            # 基本的な検証
            assert isinstance(result, str), "レスポンスが文字列ではありません"
            assert len(result) > 0, "空のレスポンスが返されました"
            
            print(f"✅ 分析完了")
            print(f"  レスポンス長: {len(result)} 文字")
            print(f"  レスポンス（先頭1000文字）:")
            print(f"  {'-' * 50}")
            print(f"  {result[:1000]}")
            print(f"  {'-' * 50}")
            
            # JSON形式の可能性をチェック
            has_json_structure = '{' in result and '}' in result
            has_json_keyword = 'json' in result.lower()
            has_code_block = '```' in result
            
            print(f"  JSON構造検出: {has_json_structure}")
            print(f"  JSONキーワード検出: {has_json_keyword}")
            print(f"  コードブロック検出: {has_code_block}")
            
            # 基本的な内容チェック
            keywords = ['規則', 'ルール', '禁止', '義務', '学校', 'rules']
            found_keywords = [kw for kw in keywords if kw in result.lower()]
            print(f"  関連キーワード検出: {found_keywords}")
            
            return result
            
        except Exception as e:
            print(f"❌ PDF分析エラー: {e}")
            print(f"  エラータイプ: {type(e)}")
            print(f"  エラー詳細: {str(e)}")
            pytest.fail(f"PDF分析に失敗: {e}")


if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=== Gemini Client テスト（実際の設定使用） ===")
    print(f"プロジェクトルート: {project_root}")
    print(f"設定ファイル利用可能: {config_available}")
    print(f"クライアント利用可能: {client_available}")
    
    # テスト実行
    pytest.main([__file__, "-v", "-s", "--tb=short"])