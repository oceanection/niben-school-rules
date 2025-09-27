"""
Google Drive API クライアント（共有ドライブ対応版）

Google Drive APIの基本操作を提供
"""

import io
from typing import List, Dict, Any, Optional

from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

from src.config.settings import settings


class DriveClient:
    """Google Drive API クライアント（共有ドライブ対応）"""
    
    def __init__(self):
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Google Drive API認証"""
        try:
            if not settings.google_application_credentials:
                raise ValueError("Google認証情報が設定されていません")
            
            credentials = ServiceAccountCredentials.from_service_account_file(
                settings.google_application_credentials,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            
            self.service = build('drive', 'v3', credentials=credentials)
            
        except Exception as e:
            raise ConnectionError(f"Google Drive認証に失敗: {str(e)}")
    
    def list_folders(self, parent_folder_id: str) -> List[Dict[str, Any]]:
        """
        指定フォルダ内のサブフォルダ一覧を取得（共有ドライブ対応）
        
        Args:
            parent_folder_id: 親フォルダID
            
        Returns:
            フォルダ情報のリスト
        """
        try:
            query = f"'{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            results = self.service.files().list(
                q=query,
                fields="files(id, name, createdTime, modifiedTime)",
                orderBy="name",
                supportsAllDrives=True,  # 共有ドライブ対応
                includeItemsFromAllDrives=True  # 共有ドライブ対応
            ).execute()
            
            return results.get('files', [])
            
        except HttpError as e:
            raise ConnectionError(f"フォルダ一覧取得に失敗: {str(e)}")
    
    def list_files(self, folder_id: str, mime_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        指定フォルダ内のファイル一覧を取得（共有ドライブ対応）
        
        Args:
            folder_id: フォルダID
            mime_type: MIMEタイプでフィルタ（例: 'application/pdf'）
            
        Returns:
            ファイル情報のリスト
        """
        try:
            query = f"'{folder_id}' in parents and trashed=false"
            
            if mime_type:
                query += f" and mimeType='{mime_type}'"
            
            results = self.service.files().list(
                q=query,
                fields="files(id, name, size, mimeType, createdTime, modifiedTime, webViewLink)",
                orderBy="name",
                supportsAllDrives=True,  # 共有ドライブ対応
                includeItemsFromAllDrives=True  # 共有ドライブ対応
            ).execute()
            
            files = []
            for file in results.get('files', []):
                files.append({
                    'id': file['id'],
                    'name': file['name'],
                    'size': int(file.get('size', 0)),
                    'size_mb': round(int(file.get('size', 0)) / 1024 / 1024, 2),
                    'mime_type': file.get('mimeType'),
                    'created_time': file.get('createdTime'),
                    'modified_time': file.get('modifiedTime'),
                    'web_view_link': file.get('webViewLink')
                })
            
            return files
            
        except HttpError as e:
            raise ConnectionError(f"ファイル一覧取得に失敗: {str(e)}")
    
    def download_file_content(self, file_id: str) -> bytes:
        """
        ファイル内容をメモリに直接ダウンロード（共有ドライブ対応）
        
        Args:
            file_id: ファイルID
            
        Returns:
            ファイルの内容（バイナリデータ）
        """
        try:
            request = self.service.files().get_media(
                fileId=file_id,
                supportsAllDrives=True  # 共有ドライブ対応
            )
            file_content = io.BytesIO()
            
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            return file_content.getvalue()
            
        except HttpError as e:
            raise ConnectionError(f"ファイルダウンロードに失敗: {str(e)}")
    
    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """
        ファイル情報を取得（共有ドライブ対応）
        
        Args:
            file_id: ファイルID
            
        Returns:
            ファイル情報
        """
        try:
            file_info = self.service.files().get(
                fileId=file_id,
                fields="id, name, size, mimeType, parents, createdTime, modifiedTime, webViewLink",
                supportsAllDrives=True  # 共有ドライブ対応
            ).execute()
            
            return {
                'id': file_info['id'],
                'name': file_info['name'],
                'size': int(file_info.get('size', 0)),
                'size_mb': round(int(file_info.get('size', 0)) / 1024 / 1024, 2),
                'mime_type': file_info.get('mimeType'),
                'parents': file_info.get('parents', []),
                'created_time': file_info.get('createdTime'),
                'modified_time': file_info.get('modifiedTime'),
                'web_view_link': file_info.get('webViewLink')
            }
            
        except HttpError as e:
            raise ConnectionError(f"ファイル情報取得に失敗: {str(e)}")


def create_drive_client() -> DriveClient:
    """Drive クライアントインスタンスを作成"""
    return DriveClient()