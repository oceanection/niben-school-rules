"""
Google Drive フォルダナビゲーター

校則データのフォルダ構造解析とPDFファイル検索
"""

import re
from typing import List, Dict, Any, Tuple, Optional

from config.settings import settings
from src.drive.client import DriveClient


class FolderNavigator:
    """校則データフォルダのナビゲーター"""
    
    def __init__(self, drive_client: DriveClient):
        self.drive_client = drive_client
        
        # 東京23区リスト
        self.tokyo_wards = [
            "千代田区", "中央区", "港区", "新宿区", "文京区", "台東区", "墨田区",
            "江東区", "品川区", "目黒区", "大田区", "世田谷区", "渋谷区", "中野区",
            "杉並区", "豊島区", "北区", "荒川区", "板橋区", "練馬区", "足立区",
            "葛飾区", "江戸川区"
        ]
    
    def find_all_school_rules_pdfs(self) -> List[Dict[str, Any]]:
        """
        設定に基づいて校則PDFを検索
        
        Returns:
            校則PDFファイル情報のリスト
        """
        if settings.batch_mode:
            return self._batch_process()
        else:
            return self._individual_process()
    
    def _batch_process(self) -> List[Dict[str, Any]]:
        """
        一括処理: ROOT_FOLDER_ID配下の全区を処理
        
        Returns:
            全区の校則PDFファイル情報のリスト
        """
        if not settings.root_folder_id:
            raise ValueError("一括処理にはROOT_FOLDER_IDが必要です")
        
        all_pdfs = []
        
        # 年度フォルダから年度を抽出
        root_info = self.drive_client.get_file_info(settings.root_folder_id)
        year = self._extract_year_from_folder_name(root_info['name'])
        
        # 区フォルダ一覧を取得
        ward_folders = self.drive_client.list_folders(settings.root_folder_id)
        
        # 東京23区のフォルダのみを処理
        valid_ward_folders = [
            folder for folder in ward_folders 
            if folder['name'] in self.tokyo_wards
        ]
        
        for ward_folder in valid_ward_folders:
            try:
                ward_pdfs = self._process_ward_folder(
                    ward_folder['id'], 
                    ward_folder['name'],
                    year
                )
                all_pdfs.extend(ward_pdfs)
            except Exception as e:
                print(f"区フォルダ処理エラー [{ward_folder['name']}]: {str(e)}")
                continue
        
        return all_pdfs
    
    def _individual_process(self) -> List[Dict[str, Any]]:
        """
        個別処理: WARD_FOLDER_IDのみ処理
        
        Returns:
            指定区の校則PDFファイル情報のリスト
        """
        if not settings.ward_folder_id:
            raise ValueError("個別処理にはWARD_FOLDER_IDが必要です")
        
        # 区フォルダ情報を取得
        ward_info = self.drive_client.get_file_info(settings.ward_folder_id)
        ward_name = ward_info['name']
        
        # 親フォルダから年度を推定
        parent_folders = ward_info.get('parents', [])
        year = "不明"
        
        if parent_folders:
            try:
                parent_info = self.drive_client.get_file_info(parent_folders[0])
                year = self._extract_year_from_folder_name(parent_info['name'])
            except:
                pass
        
        return self._process_ward_folder(settings.ward_folder_id, ward_name, year)
    
    def _process_ward_folder(self, ward_folder_id: str, ward_name: str, year: str) -> List[Dict[str, Any]]:
        """
        区フォルダ内の全学校・PDFを処理
        
        Args:
            ward_folder_id: 区フォルダID
            ward_name: 区名
            year: 年度
            
        Returns:
            区内の全校則PDFファイル情報のリスト
        """
        ward_pdfs = []
        
        # 学校フォルダ一覧を取得
        school_folders = self.drive_client.list_folders(ward_folder_id)
        
        for school_folder in school_folders:
            try:
                # 各学校フォルダ内のPDFファイルを取得
                pdf_files = self.drive_client.list_files(
                    school_folder['id'], 
                    mime_type='application/pdf'
                )
                
                # 校則関連PDFのみをフィルタ
                school_rule_pdfs = self._filter_school_rule_pdfs(pdf_files)
                
                for pdf_file in school_rule_pdfs:
                    ward_pdfs.append({
                        'year': year,
                        'ward': ward_name,
                        'school': school_folder['name'],
                        'file': pdf_file,
                        'path': f"{year}_校則データ/{ward_name}/{school_folder['name']}/{pdf_file['name']}"
                    })
                    
            except Exception as e:
                print(f"学校フォルダ処理エラー [{school_folder['name']}]: {str(e)}")
                continue
        
        return ward_pdfs
    
    def _extract_year_from_folder_name(self, folder_name: str) -> str:
        """
        フォルダ名から年度を抽出
        
        Args:
            folder_name: フォルダ名（例: "2025_校則データ"）
            
        Returns:
            年度（例: "2025"）
        """
        year_pattern = re.compile(r'^(202[0-9])_校則')
        match = year_pattern.match(folder_name)
        return match.group(1) if match else "不明"
    
    def _filter_school_rule_pdfs(self, pdf_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        校則関連PDFファイルをフィルタ
        
        Args:
            pdf_files: PDFファイルリスト
            
        Returns:
            校則関連PDFファイルのリスト
        """
        # 校則関連キーワード
        school_rule_keywords = [
            "校則", "生活のきまり", "生徒心得", "学校生活", "生活指導",
            "規則", "きまり", "ルール", "心得", "生活規定"
        ]
        
        filtered_pdfs = []
        
        for pdf_file in pdf_files:
            file_name = pdf_file['name'].lower()
            
            # キーワードに一致するファイルを抽出
            if any(keyword in pdf_file['name'] for keyword in school_rule_keywords):
                pdf_file['rule_type'] = 'school_rules'
                filtered_pdfs.append(pdf_file)
            # キーワードなしでもPDFが少ない場合は含める（暫定）
            elif len(pdf_files) <= 3:
                pdf_file['rule_type'] = 'potential_rules'
                filtered_pdfs.append(pdf_file)
        
        return filtered_pdfs
    
    def get_school_folders(self, ward_folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        学校フォルダ一覧を取得
        
        Args:
            ward_folder_id: 区フォルダID（未指定の場合は設定から取得）
            
        Returns:
            学校フォルダ情報のリスト
        """
        if not ward_folder_id:
            if settings.batch_mode:
                raise ValueError("一括処理モードでは区フォルダIDの指定が必要です")
            ward_folder_id = settings.ward_folder_id
        
        if not ward_folder_id:
            raise ValueError("区フォルダIDが設定されていません")
        
        return self.drive_client.list_folders(ward_folder_id)
    
    def get_school_pdf_files(self, school_folder_id: str) -> List[Dict[str, Any]]:
        """
        学校フォルダ内のPDFファイル一覧を取得
        
        Args:
            school_folder_id: 学校フォルダID
            
        Returns:
            PDFファイル情報のリスト
        """
        pdf_files = self.drive_client.list_files(school_folder_id, mime_type='application/pdf')
        return self._filter_school_rule_pdfs(pdf_files)
    
    def validate_folder_structure(self) -> Dict[str, Any]:
        """
        フォルダ構造の妥当性を検証
        
        Returns:
            検証結果
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": {}
        }
        
        try:
            if settings.batch_mode:
                # 一括処理モードの検証
                if not settings.root_folder_id:
                    validation_result["errors"].append("ROOT_FOLDER_IDが設定されていません")
                    validation_result["valid"] = False
                else:
                    root_info = self.drive_client.get_file_info(settings.root_folder_id)
                    validation_result["info"]["root_folder"] = root_info['name']
                    
                    ward_folders = self.drive_client.list_folders(settings.root_folder_id)
                    valid_wards = [f for f in ward_folders if f['name'] in self.tokyo_wards]
                    validation_result["info"]["ward_count"] = len(valid_wards)
                    validation_result["info"]["ward_names"] = [f['name'] for f in valid_wards]
            else:
                # 個別処理モードの検証
                if not settings.ward_folder_id:
                    validation_result["errors"].append("WARD_FOLDER_IDが設定されていません")
                    validation_result["valid"] = False
                else:
                    ward_info = self.drive_client.get_file_info(settings.ward_folder_id)
                    validation_result["info"]["ward_folder"] = ward_info['name']
                    
                    school_folders = self.drive_client.list_folders(settings.ward_folder_id)
                    validation_result["info"]["school_count"] = len(school_folders)
        
        except Exception as e:
            validation_result["errors"].append(f"フォルダ構造検証エラー: {str(e)}")
            validation_result["valid"] = False
        
        return validation_result
    
    def parse_file_path(self, file_path: str) -> Tuple[str, str, str]:
        """
        ファイルパスから年度、区、学校名を抽出
        
        Args:
            file_path: "2025_校則データ/渋谷区/XX中学校/校則.pdf" 形式のパス
            
        Returns:
            (年度, 区名, 学校名) のタプル
        """
        try:
            path_parts = file_path.strip('/').split('/')
            
            if len(path_parts) < 4:
                raise ValueError(f"パス形式が不正: {file_path}")
            
            year_folder, ward, school = path_parts[:3]
            year = self._extract_year_from_folder_name(year_folder)
            
            return year, ward, school
            
        except Exception as e:
            raise ValueError(f"パス解析エラー: {str(e)}")


def create_folder_navigator(drive_client: DriveClient) -> FolderNavigator:
    """FolderNavigator インスタンスを作成"""
    return FolderNavigator(drive_client)