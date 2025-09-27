"""
校則データ収集モジュール

Google Driveから校則PDFデータを収集し、Gemini処理用に整理
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from config.settings import settings
from drive.client import DriveClient


@dataclass
class SchoolRulePDF:
    """校則PDFファイルのデータクラス"""
    ward: str
    school: str
    file_id: str
    file_name: str
    file_size_mb: float
    file_path: str
    web_view_link: str
    created_time: str
    modified_time: str
    school_folder_url: str



class SchoolRulesCollector:
    """校則データ収集クラス"""
    
    def __init__(self, drive_client: DriveClient):
        self.drive_client = drive_client
        
        # 東京23区リスト
        self.tokyo_wards = [
            "千代田区", "中央区", "港区", "新宿区", "文京区", "台東区", "墨田区",
            "江東区", "品川区", "目黒区", "大田区", "世田谷区", "渋谷区", "中野区",
            "杉並区", "豊島区", "北区", "荒川区", "板橋区", "練馬区", "足立区",
            "葛飾区", "江戸川区"
        ]
    
    def collect_all_school_rules(self) -> List[SchoolRulePDF]:
        """
        設定に基づいて校則PDFを収集
        
        Returns:
            校則PDFファイル情報のリスト
        """
        # 設定の事前検証
        self._validate_configuration()
        
        if settings.batch_mode:
            return self._collect_batch_mode()
        else:
            return self._collect_individual_mode()
    
    def _collect_batch_mode(self) -> List[SchoolRulePDF]:
        """
        一括収集: ROOT_FOLDER_ID配下の全区を処理
        
        Returns:
            全区の校則PDFファイル情報のリスト
        """
        all_pdfs = []
        
        # 区フォルダ一覧を取得
        ward_folders = self.drive_client.list_folders(settings.root_folder_id)
        
        # 東京23区のフォルダのみを処理
        valid_ward_folders = [
            folder for folder in ward_folders 
            if folder['name'] in self.tokyo_wards
        ]
        
        print(f"収集開始: {len(valid_ward_folders)}区を処理対象とします")
        
        for ward_folder in valid_ward_folders:
            try:
                print(f"収集中: {ward_folder['name']}")
                ward_pdfs = self._collect_ward_pdfs(
                    ward_folder['id'], 
                    ward_folder['name']
                )
                all_pdfs.extend(ward_pdfs)
                print(f"  → {len(ward_pdfs)}件のPDFを収集")
            except Exception as e:
                print(f"区フォルダ収集エラー [{ward_folder['name']}]: {str(e)}")
                continue
        
        return all_pdfs
    
    def _collect_individual_mode(self) -> List[SchoolRulePDF]:
        """
        個別収集: WARD_FOLDER_IDのみ処理
        
        Returns:
            指定区の校則PDFファイル情報のリスト
        """
        # 区フォルダ情報を取得
        ward_info = self.drive_client.get_file_info(settings.ward_folder_id)
        ward_name = ward_info['name']
        
        print(f"収集開始: {ward_name}")
        return self._collect_ward_pdfs(settings.ward_folder_id, ward_name)
    
    def _collect_ward_pdfs(self, ward_folder_id: str, ward_name: str) -> List[SchoolRulePDF]:
        """
        区フォルダ内の全校則PDFを収集
        
        Args:
            ward_folder_id: 区フォルダID
            ward_name: 区名
            
        Returns:
            区内の全校則PDFファイル情報のリスト
        """
        ward_pdfs = []
        
        # 学校フォルダ一覧を取得
        school_folders = self.drive_client.list_folders(ward_folder_id)
        
        for school_folder in school_folders:
            try:

                # 学校フォルダのURLを生成 ← ここに追加
                school_folder_url = f"https://drive.google.com/drive/folders/{school_folder['id']}"

                # 各学校フォルダ内の全PDFファイルを取得（校則データと保証されている）
                pdf_files = self.drive_client.list_files(
                    school_folder['id'], 
                    mime_type='application/pdf'
                )
                
                # 全PDFを校則データとして登録
                for pdf_file in pdf_files:
                    school_rule_pdf = SchoolRulePDF(
                        ward=ward_name,
                        school=school_folder['name'],
                        file_id=pdf_file['id'],
                        file_name=pdf_file['name'],
                        file_size_mb=pdf_file['size_mb'],
                        file_path=f"{ward_name}/{school_folder['name']}/{pdf_file['name']}",
                        web_view_link=pdf_file.get('web_view_link', ''),
                        created_time=pdf_file.get('created_time', ''),
                        modified_time=pdf_file.get('modified_time', ''),
                        school_folder_url=school_folder_url
                    )
                    ward_pdfs.append(school_rule_pdf)
                    
            except Exception as e:
                print(f"学校フォルダ収集エラー [{school_folder['name']}]: {str(e)}")
                continue
        
        return ward_pdfs
    
    def _validate_configuration(self) -> None:
        """
        設定の妥当性を検証
        
        Raises:
            ValueError: 設定が不正な場合
        """
        if settings.batch_mode:
            if not settings.root_folder_id:
                raise ValueError("一括収集にはROOT_FOLDER_IDが必要です")
        else:
            if not settings.ward_folder_id:
                raise ValueError("個別収集にはWARD_FOLDER_IDが必要です")
    
    def prepare_for_gemini_processing(self, pdfs: List[SchoolRulePDF]) -> Dict[str, Any]:
        """
        Gemini処理用のデータ構造を準備
        
        Args:
            pdfs: 校則PDFリスト
            
        Returns:
            Gemini処理用データ構造
        """
        # 学校別にPDFをグループ化（同一学校の複数PDFをまとめる）
        schools_data = {}
        
        for pdf in pdfs:
            school_key = f"{pdf.ward}_{pdf.school}"
            
            if school_key not in schools_data:
                schools_data[school_key] = {
                    "ward": pdf.ward,
                    "school": pdf.school,
                    "school_folder_url": pdf.school_folder_url,
                    "pdfs": []
                }
            
            schools_data[school_key]["pdfs"].append({
                "file_id": pdf.file_id,
                "file_name": pdf.file_name,
                "file_size_mb": pdf.file_size_mb,
                "file_path": pdf.file_path,
                "web_view_link": pdf.web_view_link,
                "created_time": pdf.created_time,
                "modified_time": pdf.modified_time
            })
        
        # Gemini処理用の最終形式
        return {
            "schools": list(schools_data.values()),
            "metadata": {
                "total_schools": len(schools_data),
                "total_pdfs": len(pdfs),
                "collection_mode": "一括収集" if settings.batch_mode else "個別収集"
            }
        }
    
    def validate_drive_structure(self) -> Dict[str, Any]:
        """
        Google Driveの構造を検証
        
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
                root_info = self.drive_client.get_file_info(settings.root_folder_id)
                validation_result["info"]["root_folder"] = root_info['name']
                
                ward_folders = self.drive_client.list_folders(settings.root_folder_id)
                valid_wards = [f for f in ward_folders if f['name'] in self.tokyo_wards]
                
                validation_result["info"]["total_ward_folders"] = len(ward_folders)
                validation_result["info"]["valid_ward_count"] = len(valid_wards)
                validation_result["info"]["valid_ward_names"] = [f['name'] for f in valid_wards]
                
                if len(valid_wards) == 0:
                    validation_result["warnings"].append("有効な区フォルダが見つかりません")
                    
            else:
                # 個別処理モードの検証
                ward_info = self.drive_client.get_file_info(settings.ward_folder_id)
                validation_result["info"]["ward_folder"] = ward_info['name']
                
                school_folders = self.drive_client.list_folders(settings.ward_folder_id)
                validation_result["info"]["school_count"] = len(school_folders)
                
                if len(school_folders) == 0:
                    validation_result["warnings"].append("学校フォルダが見つかりません")
        
        except Exception as e:
            validation_result["errors"].append(f"Drive構造検証エラー: {str(e)}")
            validation_result["valid"] = False
        
        return validation_result


def create_school_rules_collector(drive_client: DriveClient) -> SchoolRulesCollector:
    """SchoolRulesCollector インスタンスを作成"""
    return SchoolRulesCollector(drive_client)