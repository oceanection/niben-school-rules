"""
正しいフォルダIDを確認するためのデバッグスクリプト
"""

from config.settings import settings
from src.drive.client import create_drive_client

def debug_folder_structure():
    """フォルダ構造を確認"""
    try:
        print("=== Google Drive 接続テスト ===")
        drive_client = create_drive_client()
        print("✓ Drive接続成功")
        
        print(f"\n=== 設定値確認 ===")
        print(f"WARD_FOLDER_ID: {settings.ward_folder_id}")
        print(f"BATCH_MODE: {settings.batch_mode}")
        
        # もしROOT_FOLDER_IDが設定されていれば、そこから練馬区を探す
        if hasattr(settings, 'root_folder_id') and settings.root_folder_id:
            print(f"ROOT_FOLDER_ID: {settings.root_folder_id}")
            try:
                print(f"\n=== ROOT_FOLDER_ID配下の確認 ===")
                root_folders = drive_client.list_folders(settings.root_folder_id)
                print(f"ルートフォルダ配下のフォルダ数: {len(root_folders)}")
                for folder in root_folders:
                    print(f"  - {folder['name']} (ID: {folder['id']})")
                    if folder['name'] == "練馬区":
                        print(f"    *** 練馬区フォルダ発見: {folder['id']} ***")
            except Exception as e:
                print(f"ROOT_FOLDER_ID読み込みエラー: {e}")
        
        # WARD_FOLDER_IDで直接アクセス試行
        print(f"\n=== WARD_FOLDER_ID直接アクセス試行 ===")
        try:
            ward_info = drive_client.get_file_info(settings.ward_folder_id)
            print(f"✓ フォルダアクセス成功: {ward_info['name']}")
            
            print(f"\n=== 学校フォルダ一覧 ===")
            school_folders = drive_client.list_folders(settings.ward_folder_id)
            print(f"学校フォルダ数: {len(school_folders)}")
            
            for school_folder in school_folders:
                print(f"\n学校: {school_folder['name']} (ID: {school_folder['id']})")
                
                # 各学校のPDFファイルを取得
                pdf_files = drive_client.list_files(school_folder['id'], mime_type='application/pdf')
                print(f"  PDFファイル数: {len(pdf_files)}")
                
                for pdf in pdf_files:
                    print(f"    - {pdf['name']}")
                    print(f"      ID: {pdf['id']}")
                    print(f"      サイズ: {pdf['size_mb']}MB")
                
        except Exception as e:
            print(f"✗ WARD_FOLDER_IDアクセスエラー: {e}")
            
            # 代替案: 環境変数を直接確認
            import os
            print(f"\n=== 環境変数直接確認 ===")
            ward_id_env = os.environ.get('WARD_FOLDER_ID', 'NOT_SET')
            print(f"環境変数 WARD_FOLDER_ID: {ward_id_env}")
            
            if ward_id_env != 'NOT_SET' and ward_id_env != settings.ward_folder_id:
                print(f"⚠️  設定値と環境変数が異なります:")
                print(f"   settings.ward_folder_id: {settings.ward_folder_id}")
                print(f"   環境変数 WARD_FOLDER_ID: {ward_id_env}")
        
    except Exception as e:
        print(f"✗ 初期化エラー: {e}")

if __name__ == "__main__":
    debug_folder_structure()