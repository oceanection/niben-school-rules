"""
学校規則分析メインプログラム

Google Drive → Gemini分析 → Google Sheets保存の一連の処理を実行
"""
import sys
from pathlib import Path

import logging
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

# 設定
from src.config.settings import settings

# 各パッケージのクライアント
from src.drive.client import create_drive_client
from src.drive.school_rules_collector import create_school_rules_collector
from src.gemini.client import GeminiClient
from src.sheets.client import SpreadsheetClient
from src.sheets.writer import write_data


class SchoolRulesAnalyzer:
    """学校規則分析システムのメインクラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # クライアントの初期化
        self.drive_client = None
        self.gemini_client = None
        self.sheets_client = None
        self.worksheet = None
        
        # 統計情報
        self.stats = {
            'processed_schools': 0,
            'processed_pdfs': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'successful_saves': 0,
            'failed_saves': 0,
            'start_time': None,
            'end_time': None
        }
    
    def initialize_clients(self) -> bool:
        """
        各クライアントを初期化
        
        Returns:
            bool: 初期化成功時True
        """
        try:
            self.logger.info("クライアント初期化開始")
            
            # Drive クライアント初期化
            self.drive_client = create_drive_client()
            self.logger.info("Google Drive クライアント初期化完了")
            
            # Gemini クライアント初期化
            self.gemini_client = GeminiClient(
                api_key=settings.gemini_api_key,
                model_name=settings.gemini_model
            )
            self.logger.info(f"Gemini クライアント初期化完了 (モデル: {settings.gemini_model})")
            
            # Sheets クライアント初期化
            self.sheets_client = SpreadsheetClient(settings.google_application_credentials)
            if not self.sheets_client.client:
                raise ConnectionError("Google Sheets クライアントの初期化に失敗")
            
            # ワークシート取得
            self.worksheet = self.sheets_client.get_worksheet(
                settings.spreadsheet_id, 
                settings.worksheet_name
            )
            if not self.worksheet:
                raise ConnectionError(f"ワークシート '{settings.worksheet_name}' の取得に失敗")
            
            self.logger.info(f"Google Sheets クライアント初期化完了 (シート: {settings.worksheet_name})")
            
            # 接続テスト
            if not self.gemini_client.test_connection():
                raise ConnectionError("Gemini API 接続テストに失敗")
            
            self.logger.info("全クライアント初期化完了")
            return True
            
        except Exception as e:
            self.logger.error(f"クライアント初期化エラー: {e}")
            return False
    
    def validate_environment(self) -> bool:
        """
        実行環境の妥当性を検証
        
        Returns:
            bool: 検証成功時True
        """
        try:
            self.logger.info("環境検証開始")
            
            # 必須設定の確認
            required_settings = [
                ('GEMINI_API_KEY', settings.gemini_api_key),
                ('GOOGLE_APPLICATION_CREDENTIALS', settings.google_application_credentials),
                ('SPREADSHEET_ID', settings.spreadsheet_id),
            ]
            
            for setting_name, setting_value in required_settings:
                if not setting_value:
                    raise ValueError(f"必須設定が未設定: {setting_name}")
            
            # 処理モード別の設定確認
            if settings.batch_mode:
                if not settings.root_folder_id:
                    raise ValueError("一括処理モードには ROOT_FOLDER_ID が必要")
                self.logger.info(f"処理モード: 一括処理 (ROOT_FOLDER_ID: {settings.root_folder_id})")
            else:
                if not settings.ward_folder_id:
                    raise ValueError("個別処理モードには WARD_FOLDER_ID が必要")
                self.logger.info(f"処理モード: 個別処理 (WARD_FOLDER_ID: {settings.ward_folder_id})")
            
            # Google Drive構造の検証
            collector = create_school_rules_collector(self.drive_client)
            validation_result = collector.validate_drive_structure()
            
            if not validation_result['valid']:
                for error in validation_result['errors']:
                    self.logger.error(f"Drive構造検証エラー: {error}")
                return False
            
            # 警告がある場合は表示
            for warning in validation_result['warnings']:
                self.logger.warning(f"Drive構造検証警告: {warning}")
            
            # 検証情報を表示
            info = validation_result['info']
            if settings.batch_mode:
                self.logger.info(f"検証結果: {info.get('valid_ward_count', 0)}区のフォルダを検出")
            else:
                self.logger.info(f"検証結果: {info.get('school_count', 0)}校のフォルダを検出")
            
            self.logger.info("環境検証完了")
            return True
            
        except Exception as e:
            self.logger.error(f"環境検証エラー: {e}")
            return False
    
    def collect_school_data(self) -> List[Dict[str, Any]]:
        """
        Google Driveから学校規則データを収集
        
        Returns:
            List[Dict]: 学校データのリスト
        """
        try:
            self.logger.info("学校データ収集開始")
            
            collector = create_school_rules_collector(self.drive_client)
            school_pdfs = collector.collect_all_school_rules()
            
            if not school_pdfs:
                self.logger.warning("収集されたPDFが0件です")
                return []
            
            # Gemini処理用データ構造に変換
            processed_data = collector.prepare_for_gemini_processing(school_pdfs)
            schools = processed_data['schools']
            metadata = processed_data['metadata']
            
            self.logger.info(f"データ収集完了: {metadata['total_schools']}校, {metadata['total_pdfs']}ファイル")
            
            return schools
            
        except Exception as e:
            self.logger.error(f"学校データ収集エラー: {e}")
            return []
    
    def analyze_school_pdf(self, pdf_info: Dict[str, Any], school_context: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        単一PDFの分析処理
        
        Args:
            pdf_info: PDFファイル情報
            school_context: 学校コンテキスト情報
            
        Returns:
            Optional[Dict]: 分析結果、失敗時はNone
        """
        try:
            file_id = pdf_info['file_id']
            file_name = pdf_info['file_name']
            
            self.logger.info(f"PDF分析開始: {school_context['ward']}/{school_context['school']}/{file_name}")
            
            # PDFファイルをダウンロード
            pdf_content = self.drive_client.download_file_content(file_id)
            self.logger.debug(f"PDFダウンロード完了: {len(pdf_content)} バイト")
            
            # Gemini APIで分析
            analysis_result = self.gemini_client.analyze_pdf(pdf_content, file_name)
            
            # JSON形式での解析を試行
            try:
                # JSONブロックの抽出
                if '```json' in analysis_result:
                    json_start = analysis_result.find('```json') + 7
                    json_end = analysis_result.find('```', json_start)
                    json_str = analysis_result[json_start:json_end].strip()
                else:
                    # JSONブロックがない場合、全体から{...}を抽出
                    start_idx = analysis_result.find('{')
                    end_idx = analysis_result.rfind('}') + 1
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = analysis_result[start_idx:end_idx]
                    else:
                        raise ValueError("JSONデータが見つかりません")
                
                parsed_result = json.loads(json_str)
                
                # メタデータを追加
                parsed_result['_metadata'] = {
                    'ward': school_context['ward'],
                    'school': school_context['school'],
                    'file_name': file_name,
                    'file_id': file_id,
                    'file_path': pdf_info['file_path'],
                    'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'model_used': self.gemini_client.model_name
                }
                
                self.logger.info(f"PDF分析成功: {file_name}")
                return parsed_result
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON解析エラー: {file_name} - {e}")
                self.logger.error(f"レスポンス内容（先頭500文字）: {analysis_result[:500]}")
                return None
                
        except Exception as e:
            self.logger.error(f"PDF分析エラー: {pdf_info.get('file_name', 'unknown')} - {e}")
            return None
    
    def save_analysis_result(self, analysis_result: Dict[str, Any]) -> bool:
        """
        分析結果をGoogle Sheetsに保存
        
        Args:
            analysis_result: 分析結果
            
        Returns:
            bool: 保存成功時True
        """
        try:
            metadata = analysis_result.get('_metadata', {})
            ward = metadata.get('ward', '')
            school = metadata.get('school', '')
            file_name = metadata.get('file_name', '')
            
            self.logger.info(f"結果保存開始: {ward}/{school}/{file_name}")
            
            # メタデータを除いた分析結果のみを保存
            clean_result = {k: v for k, v in analysis_result.items() if not k.startswith('_')}
            
            success = write_data(self.worksheet, clean_result)
            
            if success:
                self.logger.info(f"結果保存成功: {file_name}")
                return True
            else:
                self.logger.error(f"結果保存失敗: {file_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"結果保存エラー: {e}")
            return False
    
    def process_school(self, school_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        単一学校の全PDFを処理
        
        Args:
            school_data: 学校データ
            
        Returns:
            Dict: 処理結果の統計
        """
        ward = school_data['ward']
        school = school_data['school']
        pdfs = school_data['pdfs']
        
        school_stats = {
            'ward': ward,
            'school': school,
            'total_pdfs': len(pdfs),
            'successful_analyses': 0,
            'failed_analyses': 0,
            'successful_saves': 0,
            'failed_saves': 0
        }
        
        self.logger.info(f"学校処理開始: {ward}/{school} ({len(pdfs)}ファイル)")
        
        school_context = {'ward': ward, 'school': school}
        
        for pdf_info in pdfs:
            try:
                # PDF分析
                analysis_result = self.analyze_school_pdf(pdf_info, school_context)
                
                if analysis_result:
                    school_stats['successful_analyses'] += 1
                    self.stats['successful_analyses'] += 1
                    
                    # 結果保存
                    if self.save_analysis_result(analysis_result):
                        school_stats['successful_saves'] += 1
                        self.stats['successful_saves'] += 1
                    else:
                        school_stats['failed_saves'] += 1
                        self.stats['failed_saves'] += 1
                else:
                    school_stats['failed_analyses'] += 1
                    self.stats['failed_analyses'] += 1
                    
                self.stats['processed_pdfs'] += 1
                
                # 進捗表示
                if self.stats['processed_pdfs'] % 10 == 0:
                    self.logger.info(f"進捗: {self.stats['processed_pdfs']}ファイル処理完了")
                
                # API制限を考慮した待機
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"PDF処理エラー: {pdf_info.get('file_name', 'unknown')} - {e}")
                school_stats['failed_analyses'] += 1
                self.stats['failed_analyses'] += 1
                continue
        
        self.stats['processed_schools'] += 1
        
        self.logger.info(f"学校処理完了: {ward}/{school} "
                        f"(成功: {school_stats['successful_analyses']}/{school_stats['total_pdfs']})")
        
        return school_stats
    
    def run_analysis(self) -> bool:
        """
        メイン分析処理を実行
        
        Returns:
            bool: 処理成功時True
        """
        try:
            self.stats['start_time'] = time.time()
            
            self.logger.info("学校規則分析システム開始")
            
            # 1. クライアント初期化（環境検証前に実行）
            if not self.initialize_clients():
                return False
            
            # 2. 環境検証
            if not self.validate_environment():
                return False
            
            # 3. 学校データ収集
            schools = self.collect_school_data()
            if not schools:
                self.logger.error("処理対象の学校データが見つかりません")
                return False
            
            self.logger.info(f"処理開始: {len(schools)}校")
            
            # 4. 各学校の処理
            for i, school_data in enumerate(schools, 1):
                try:
                    self.logger.info(f"学校 {i}/{len(schools)}: {school_data['ward']}/{school_data['school']}")
                    
                    school_result = self.process_school(school_data)
                    
                    # 学校処理完了の詳細ログ
                    self.logger.info(f"学校完了 [{i}/{len(schools)}]: {school_result['ward']}/{school_result['school']} "
                                   f"分析({school_result['successful_analyses']}/{school_result['total_pdfs']}) "
                                   f"保存({school_result['successful_saves']}/{school_result['successful_analyses']})")
                    
                except Exception as e:
                    self.logger.error(f"学校処理エラー: {school_data.get('school', 'unknown')} - {e}")
                    continue
            
            self.stats['end_time'] = time.time()
            
            # 5. 最終結果レポート
            self.generate_final_report()
            
            return True
            
        except Exception as e:
            self.logger.error(f"メイン処理エラー: {e}")
            return False
    
    def generate_final_report(self):
        """最終処理結果レポートを生成"""
        elapsed_time = self.stats['end_time'] - self.stats['start_time']
        elapsed_minutes = elapsed_time / 60
        
        self.logger.info("=" * 60)
        self.logger.info("学校規則分析システム処理完了")
        self.logger.info("=" * 60)
        self.logger.info(f"処理時間: {elapsed_minutes:.1f}分")
        self.logger.info(f"処理学校数: {self.stats['processed_schools']}校")
        self.logger.info(f"処理PDFファイル数: {self.stats['processed_pdfs']}ファイル")
        self.logger.info(f"分析成功: {self.stats['successful_analyses']}ファイル")
        self.logger.info(f"分析失敗: {self.stats['failed_analyses']}ファイル")
        self.logger.info(f"保存成功: {self.stats['successful_saves']}ファイル")
        self.logger.info(f"保存失敗: {self.stats['failed_saves']}ファイル")
        
        if self.stats['processed_pdfs'] > 0:
            success_rate = (self.stats['successful_analyses'] / self.stats['processed_pdfs']) * 100
            self.logger.info(f"成功率: {success_rate:.1f}%")
        
        self.logger.info("=" * 60)


def setup_logging():
    """ログ設定を初期化"""
    log_dir = settings.project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_filename = log_dir / f"school_rules_analysis_{time.strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # サードパーティライブラリのログレベルを調整
    logging.getLogger('google').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('googleapiclient').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


def main():
    """メイン関数"""
    logger = setup_logging()
    
    try:
        logger.info("学校規則分析システム起動")
        
        # システム設定表示
        logger.info(f"処理モード: {'一括処理' if settings.batch_mode else '個別処理'}")
        logger.info(f"Geminiモデル: {settings.gemini_model}")
        logger.info(f"対象スプレッドシート: {settings.spreadsheet_id}")
        logger.info(f"対象シート: {settings.worksheet_name}")
        
        # 分析システム実行
        analyzer = SchoolRulesAnalyzer()
        success = analyzer.run_analysis()
        
        if success:
            logger.info("処理が正常に完了しました")
            return 0
        else:
            logger.error("処理中にエラーが発生しました")
            return 1
            
    except KeyboardInterrupt:
        logger.info("ユーザーによって処理が中断されました")
        return 130
    except Exception as e:
        logger.error(f"予期しないエラー: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    # パスを修正してsrcディレクトリを追加
    import sys
    from pathlib import Path
    
    # srcディレクトリをパスに追加
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))
    
    exit(main())