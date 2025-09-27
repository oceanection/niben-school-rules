"""
共有ドライブの権限とアクセス可能性を確認
"""

from config.settings import settings
from src.drive.client import create_drive_client

def check_shared_drive_access():
    """共有ドライブアクセスの確認"""
    try:
        print("=== 共有ドライブアクセス確認 ===")
        drive_client = create_drive_client()
        
        # 1. 全ての共有ドライブを一覧表示
        print("\n=== 1. アクセス可能な共有ドライブ一覧 ===")
        try:
            drives_result = drive_client.service.drives().list().execute()
            drives = drives_result.get('drives', [])
            
            print(f"アクセス可能な共有ドライブ数: {len(drives)}")
            for drive in drives:
                print(f"  📁 {drive['name']} (ID: {drive['id']})")
                
                # 各共有ドライブのルートフォルダを確認
                try:
                    root_items = drive_client.service.files().list(
                        q=f"'{drive['id']}' in parents and trashed=false",
                        fields="files(id, name, mimeType)",
                        supportsAllDrives=True,
                        includeItemsFromAllDrives=True,
                        corpora='drive',
                        driveId=drive['id']
                    ).execute()
                    
                    items = root_items.get('files', [])
                    print(f"     ルート配下のアイテム数: {len(items)}")
                    for item in items[:5]:  # 最初の5個のみ表示
                        icon = "📁" if item.get('mimeType') == 'application/vnd.google-apps.folder' else "📄"
                        print(f"       {icon} {item['name']}")
                        
                        # 練馬区関連のフォルダを探す
                        if "練馬" in item['name']:
                            print(f"         🎯 練馬区関連フォルダ発見: {item['id']}")
                    
                except Exception as e:
                    print(f"     共有ドライブ内容取得エラー: {e}")
        
        except Exception as e:
            print(f"共有ドライブ一覧取得エラー: {e}")
        
        # 2. 指定されたWARD_FOLDER_IDに直接アクセス（共有ドライブ対応）
        print(f"\n=== 2. WARD_FOLDER_ID直接アクセス（共有ドライブ対応） ===")
        print(f"WARD_FOLDER_ID: {settings.ward_folder_id}")
        
        try:
            # 共有ドライブ対応でファイル情報取得
            ward_info = drive_client.service.files().get(
                fileId=settings.ward_folder_id,
                fields="id, name, mimeType, parents, driveId",
                supportsAllDrives=True
            ).execute()
            
            print(f"✅ フォルダアクセス成功!")
            print(f"   名前: {ward_info['name']}")
            print(f"   ID: {ward_info['id']}")
            print(f"   タイプ: {ward_info.get('mimeType')}")
            print(f"   親: {ward_info.get('parents', [])}")
            print(f"   共有ドライブID: {ward_info.get('driveId', 'なし（マイドライブ）')}")
            
            # フォルダ配下を確認
            print(f"\n=== 3. {ward_info['name']} フォルダ配下の確認 ===")
            school_folders = drive_client.list_folders(settings.ward_folder_id)
            print(f"学校フォルダ数: {len(school_folders)}")
            
            for school in school_folders:
                print(f"\n学校: {school['name']} (ID: {school['id']})")
                
                # PDFファイルを確認
                pdfs = drive_client.list_files(school['id'], mime_type='application/pdf')
                print(f"  PDFファイル数: {len(pdfs)}")
                for pdf in pdfs:
                    print(f"    📄 {pdf['name']} ({pdf['size_mb']}MB)")
            
        except Exception as e:
            print(f"❌ WARD_FOLDER_IDアクセスエラー: {e}")
            print("\n可能な原因:")
            print("1. フォルダIDが間違っている")
            print("2. サービスアカウントが共有ドライブにアクセスできない")
            print("3. フォルダが共有ドライブから削除/移動された")
        
        # 3. ROOT_FOLDER_IDも確認
        if settings.root_folder_id:
            print(f"\n=== 4. ROOT_FOLDER_ID確認 ===")
            print(f"ROOT_FOLDER_ID: {settings.root_folder_id}")
            
            try:
                root_info = drive_client.service.files().get(
                    fileId=settings.root_folder_id,
                    fields="id, name, mimeType, parents, driveId",
                    supportsAllDrives=True
                ).execute()
                
                print(f"✅ ルートフォルダアクセス成功!")
                print(f"   名前: {root_info['name']}")
                print(f"   共有ドライブID: {root_info.get('driveId', 'なし（マイドライブ）')}")
                
                # ルート配下を確認
                root_folders = drive_client.list_folders(settings.root_folder_id)
                print(f"   配下のフォルダ数: {len(root_folders)}")
                for folder in root_folders:
                    print(f"     📁 {folder['name']} (ID: {folder['id']})")
                    if "練馬" in folder['name']:
                        print(f"        🎯 練馬区フォルダ発見!")
                
            except Exception as e:
                print(f"❌ ROOT_FOLDER_IDアクセスエラー: {e}")
    
    except Exception as e:
        print(f"初期化エラー: {e}")

if __name__ == "__main__":
    check_shared_drive_access()