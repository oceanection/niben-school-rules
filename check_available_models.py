"""
利用可能なGeminiモデルを確認するスクリプト
"""

import google.generativeai as genai
from config.settings import settings

def check_available_models():
    """利用可能なモデル一覧を取得"""
    try:
        if not settings.gemini_api_key:
            print("❌ GEMINI_API_KEY が設定されていません")
            return
        
        genai.configure(api_key=settings.gemini_api_key)
        
        print("=== 利用可能なGeminiモデル一覧 ===")
        models = genai.list_models()
        
        for model in models:
            print(f"📋 {model.name}")
            print(f"   表示名: {model.display_name}")
            if hasattr(model, 'supported_generation_methods'):
                methods = [method for method in model.supported_generation_methods]
                print(f"   対応メソッド: {methods}")
            print()
        
        print("=== 推奨設定 ===")
        print("校則分析に適したモデル:")
        
        for model in models:
            if 'generateContent' in getattr(model, 'supported_generation_methods', []):
                if any(name in model.name.lower() for name in ['pro', '1.5']):
                    print(f"✅ {model.name} - {model.display_name}")
        
    except Exception as e:
        print(f"❌ モデル一覧取得エラー: {str(e)}")

if __name__ == "__main__":
    check_available_models()