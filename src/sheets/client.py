# src/client.py
import gspread
from google.oauth2.service_account import Credentials

class SpreadsheetClient:
    """
    Googleスプレッドシートへの接続を管理するクライアント。
    """
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    def __init__(self, credentials_path: str):
        """
        サービスアカウントキーを使用して認証クライアントを初期化します。

        Args:
            credentials_path (str): サービスアカウントキー(JSON)のファイルパス。
        """
        if not credentials_path:
            print("エラー: 認証情報ファイルのパスが設定されていません。")
            self.client = None
            return

        try:
            creds = Credentials.from_service_account_file(credentials_path, scopes=self.SCOPES)
            self.client = gspread.authorize(creds)
        except FileNotFoundError:
            print(f"エラー: 認証情報ファイルが見つかりません: {credentials_path}")
            self.client = None
        except Exception as e:
            print(f"認証中にエラーが発生しました: {e}")
            self.client = None

    def get_worksheet(self, spreadsheet_id: str, worksheet_name: str) -> gspread.Worksheet | None:
        """
        スプレッドシートIDとシート名を指定して、ワークシートオブジェクトを取得します。

        Args:
            spreadsheet_id (str): スプレッドシートのID。
            worksheet_name (str): ワークシート名。

        Returns:
            gspread.Worksheet | None: ワークシートオブジェクト。見つからない場合はNone。
        """
        if not self.client:
            return None

        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet(worksheet_name)
            return worksheet
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"エラー: スプレッドシートが見つかりません。ID: {spreadsheet_id}")
            return None
        except gspread.exceptions.WorksheetNotFound:
            print(f"エラー: ワークシート '{worksheet_name}' が見つかりません。")
            return None
        except Exception as e:
            print(f"ワークシートの取得中にエラーが発生しました: {e}")
            return None