"""
sheets/writer.py の単体テスト

実際のGoogleスプレッドシートへの書き込みテストを実施
書き込み結果を目視確認できるようにテストデータを残す
"""

import sys
from pathlib import Path
import pytest
from datetime import datetime

# srcディレクトリをパスに追加
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from config.settings import settings
from sheets.client import SpreadsheetClient
from sheets.writer import get_header_row, convert_json_to_row, write_data


class TestSheetsWriter:
    """sheets/writer.py の単体テスト"""
    
    @classmethod
    def setup_class(cls):
        """テストクラスの初期化"""
        print(f"テスト開始:")
        print(f"  SPREADSHEET_ID: {settings.spreadsheet_id}")
        print(f"  WORKSHEET_NAME: {settings.worksheet_name}")
        
        cls.client = SpreadsheetClient(settings.google_application_credentials)
        cls.worksheet = cls.client.get_worksheet(
            settings.spreadsheet_id, 
            settings.worksheet_name
        )
        
        assert cls.worksheet is not None, "ワークシートの取得に失敗"
        print(f"✓ ワークシート接続成功: '{cls.worksheet.title}'")
    
    def test_get_header_row(self):
        """ヘッダー行生成テスト"""
        header_row = get_header_row()
        
        assert isinstance(header_row, list)
        assert len(header_row) > 0
        
        # 最初の3列が期待通りかチェック
        expected_first_three = ["区名", "学校名", "学校フォルダURL"]
        actual_first_three = header_row[:3]
        
        assert actual_first_three == expected_first_three, f"ヘッダーの最初の3列が不正: {actual_first_three}"
        
        print(f"✓ ヘッダー行生成成功 (列数: {len(header_row)})")
        print(f"  最初の3列: {actual_first_three}")
        print(f"  最後の3列: {header_row[-3:]}")
    
    def test_convert_json_to_row_with_metadata(self):
        """メタデータ付きJSON → 行データ変換テスト"""
        test_data = {
            "_metadata": {
                "ward": "練馬区",
                "school": "テスト中学校",
                "school_folder_url": "https://drive.google.com/drive/folders/test123",
                "file_name": "test.pdf",
                "analysis_timestamp": "2025-09-27 12:00:00"
            },
            "general": {
                "revision_process": {
                    "status": "規定あり",
                    "evidence": "生徒手帳第1章に記載"
                }
            },
            "uniform": {
                "standard_uniform": {
                    "status": "指定あり",
                    "evidence": "学校指定の制服着用必須"
                },
                "lgbtq_consideration": {
                    "status": "配慮あり",
                    "evidence": "性別に関わらず制服選択可能"
                }
            },
            "appearance": {
                "hair": {
                    "gender_specific_length": {
                        "status": "男女別の長さ指定あり",
                        "evidence": "男子は耳にかからない長さ、女子は肩につかない長さ"
                    }
                }
            }
        }
        
        row_data = convert_json_to_row(test_data)
        header_row = get_header_row()
        
        assert isinstance(row_data, list)
        assert len(row_data) == len(header_row), f"行データの長さが不正: {len(row_data)} != {len(header_row)}"
        
        # 最初の3列（メタデータ）をチェック
        assert row_data[0] == "練馬区", f"区名が不正: {row_data[0]}"
        assert row_data[1] == "テスト中学校", f"学校名が不正: {row_data[1]}"
        assert row_data[2] == "https://drive.google.com/drive/folders/test123", f"URLが不正: {row_data[2]}"
        
        # 分析データ部分をチェック
        assert row_data[3] == "規定あり", f"見直しプロセス_規定が不正: {row_data[3]}"
        assert row_data[4] == "生徒手帳第1章に記載", f"見直しプロセス_根拠が不正: {row_data[4]}"
        
        print("✓ JSON → 行データ変換成功")
        print(f"  区名: {row_data[0]}")
        print(f"  学校名: {row_data[1]}")
        print(f"  URL: {row_data[2]}")
        print(f"  行データ長: {len(row_data)}")
    
    def test_convert_json_to_row_without_metadata(self):
        """メタデータなしJSON → 行データ変換テスト"""
        test_data = {
            "general": {
                "revision_process": {
                    "status": "規定なし",
                    "evidence": ""
                }
            }
        }
        
        row_data = convert_json_to_row(test_data)
        header_row = get_header_row()
        
        assert len(row_data) == len(header_row)
        
        # メタデータがない場合は空文字列になることを確認
        assert row_data[0] == "", f"区名が空文字列でない: '{row_data[0]}'"
        assert row_data[1] == "", f"学校名が空文字列でない: '{row_data[1]}'"
        assert row_data[2] == "", f"URLが空文字列でない: '{row_data[2]}'"
        
        print("✓ メタデータなしJSON変換成功（空文字列で埋められる）")
    
    def test_write_data_complete_sample(self):
        """完全なサンプルデータ書き込みテスト"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # テスト用の完全なサンプルデータ
        sample_data = {
            "_metadata": {
                "ward": "練馬区",
                "school": f"テスト中学校_{timestamp}",
                "school_folder_url": "https://drive.google.com/drive/folders/1nAjsLuI2pWZfUbZSBpqeCdjLw1nvrzD3",
                "file_name": f"test_sample_{timestamp}.pdf",
                "file_id": "test_file_id_12345",
                "file_path": f"練馬区/テスト中学校_{timestamp}/test_sample_{timestamp}.pdf",
                "analysis_timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "model_used": "models/gemini-2.5-flash"
            },
            "general": {
                "revision_process": {
                    "status": "規定あり",
                    "evidence": "生徒指導要録第1条に校則見直し手続きを規定"
                }
            },
            "uniform": {
                "standard_uniform": {
                    "status": "指定あり",
                    "evidence": "本校指定の制服着用を義務とする"
                },
                "lgbtq_consideration": {
                    "status": "配慮あり",
                    "evidence": "性別に関わらず制服（スラックス・スカート）を選択できる"
                },
                "seasonal_transition_period": {
                    "status": "移行期間あり",
                    "evidence": "6月1日〜15日、10月1日〜15日を衣替え移行期間とする"
                }
            },
            "clothing_items": {
                "shirts_blouses": {
                    "color_specification": {
                        "status": "指定あり",
                        "evidence": "白色のシャツ・ブラウスを着用すること"
                    },
                    "wearing_method": {
                        "status": "指定あり",
                        "details": "シャツの裾はズボンに入れる",
                        "evidence": "シャツの裾は必ずズボン・スカートに入れること"
                    }
                },
                "underwear": {
                    "obligation_to_wear": {
                        "status": "着用義務あり",
                        "evidence": "肌着の着用を義務とする"
                    },
                    "color_specification": {
                        "status": "指定あり",
                        "evidence": "白色または肌色の肌着を着用すること"
                    },
                    "pattern_specification": {
                        "status": "指定なし",
                        "evidence": ""
                    }
                },
                "slacks_skirts": {
                    "length_specification": {
                        "status": "指定あり",
                        "evidence": "スカート丈は膝が隠れる長さとする"
                    },
                    "belt_obligation": {
                        "status": "着用義務あり",
                        "evidence": "ベルトの着用を義務とする"
                    },
                    "belt_color_specification": {
                        "status": "指定あり",
                        "evidence": "黒色または茶色のベルトを着用"
                    },
                    "belt_design_specification": {
                        "status": "指定なし",
                        "evidence": ""
                    }
                },
                "indoor_outerwear": {
                    "color_specification": {
                        "status": "指定あり",
                        "evidence": "紺色またはグレーのカーディガン"
                    },
                    "type_restriction": {
                        "status": "種類を限定",
                        "evidence": "カーディガンまたはベストのみ着用可"
                    },
                    "pattern_specification": {
                        "status": "規定なし",
                        "evidence": ""
                    }
                },
                "outdoor_outerwear": {
                    "school_designated": {
                        "status": "学校指定",
                        "evidence": "学校指定のブレザー着用"
                    },
                    "color_specification": {
                        "status": "指定あり",
                        "evidence": "紺色のブレザー"
                    },
                    "design_specification": {
                        "status": "指定あり",
                        "evidence": "校章付きブレザーを着用"
                    }
                },
                "scarves_gloves": {
                    "status": "規定なし",
                    "evidence": ""
                },
                "socks": {
                    "design_specification": {
                        "status": "色・柄・模様の指定あり",
                        "evidence": "白色または紺色の無地靴下"
                    },
                    "length_specification": {
                        "status": "長さの指定あり",
                        "evidence": "くるぶしが隠れる長さ以上"
                    }
                }
            },
            "appearance": {
                "hair": {
                    "gender_specific_length": {
                        "status": "男女別の長さ指定あり",
                        "evidence": "男子は耳にかからない、女子は肩につかない長さ"
                    },
                    "fringe_neck_length": {
                        "status": "前髪・襟足の長さ指定あり",
                        "evidence": "前髪は眉毛にかからない、襟足は制服の襟にかからない"
                    },
                    "tying_obligation": {
                        "status": "長さによる結束義務あり",
                        "evidence": "肩につく長さの場合は束ねること"
                    },
                    "prohibited_styles_modifications": {
                        "status": "特定の髪型・加工の禁止あり",
                        "items": ["パーマ", "カラーリング", "ツーブロック"],
                        "evidence": "パーマ、カラーリング、ツーブロック等は禁止"
                    },
                    "abstract_expressions": {
                        "status": "抽象的な表現での指定あり",
                        "evidence": "中学生らしい清潔感のある髪型"
                    },
                    "hair_accessories": {
                        "status": "指定あり",
                        "details": "黒・紺・茶色のゴムまたはピン",
                        "evidence": "髪留めは黒・紺・茶色に限る"
                    }
                },
                "face": {
                    "makeup_prohibition": {
                        "status": "メイク禁止",
                        "evidence": "化粧は一切禁止とする"
                    },
                    "eyebrow_modification_prohibition": {
                        "status": "眉毛加工の禁止あり",
                        "evidence": "眉毛の加工・整形は禁止"
                    }
                },
                "inspections": {
                    "hair_inspection": {
                        "status": "頭髪検査あり",
                        "evidence": "月1回の頭髪検査を実施"
                    }
                }
            },
            "belongings": {
                "school_bag": {
                    "school_designated": {
                        "status": "学校指定あり",
                        "evidence": "学校指定のバッグを使用すること"
                    },
                    "design_specification": {
                        "status": "色・デザイン等に指定あり",
                        "evidence": "紺色の指定バッグ"
                    },
                    "accessory_restriction": {
                        "status": "アクセサリーの制限あり",
                        "evidence": "キーホルダー等の装飾品は禁止"
                    }
                },
                "care_products": {
                    "carrying_prohibited": {
                        "status": "規定なし",
                        "evidence": ""
                    },
                    "specific_item_restriction": {
                        "status": "特定の用品の持ち込み制限あり",
                        "evidence": "化粧品・整髪料の持ち込み禁止"
                    }
                }
            },
            "school_life_outside": {
                "loitering_prohibition": {
                    "status": "寄り道禁止",
                    "evidence": "登下校時の寄り道は禁止"
                },
                "facility_entry_prohibition": {
                    "status": "特定施設への立ち入り禁止",
                    "details": "ゲームセンター、カラオケ店",
                    "evidence": "ゲームセンター・カラオケ店等への立ち入り禁止"
                },
                "gathering_in_public_prohibition": {
                    "status": "公共の場での集まり禁止",
                    "evidence": "制服での公共施設での集団行動禁止"
                }
            }
        }
        
        print(f"\n完全サンプルデータ書き込みテスト開始:")
        print(f"  学校名: {sample_data['_metadata']['school']}")
        print(f"  タイムスタンプ: {timestamp}")
        
        # 書き込み実行
        success = write_data(self.worksheet, sample_data)
        
        assert success, "完全サンプルデータの書き込みに失敗"
        
        print("✓ 完全サンプルデータ書き込み成功")
        print(f"  スプレッドシート確認URL: https://docs.google.com/spreadsheets/d/{settings.spreadsheet_id}")
    
    def test_write_data_minimal_sample(self):
        """最小限サンプルデータ書き込みテスト"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 最小限のテストデータ
        minimal_data = {
            "_metadata": {
                "ward": "練馬区",
                "school": f"最小テスト校_{timestamp}",
                "school_folder_url": "https://drive.google.com/drive/folders/1cRMK9nzL7i6foEUOrhmKsvnKKahk0arY",
                "file_name": f"minimal_test_{timestamp}.pdf"
            },
            "general": {
                "revision_process": {
                    "status": "規定なし",
                    "evidence": ""
                }
            }
        }
        
        print(f"\n最小限サンプルデータ書き込みテスト:")
        print(f"  学校名: {minimal_data['_metadata']['school']}")
        
        success = write_data(self.worksheet, minimal_data)
        
        assert success, "最小限サンプルデータの書き込みに失敗"
        print("✓ 最小限サンプルデータ書き込み成功")
    
    def test_write_data_metadata_only(self):
        """メタデータのみ書き込みテスト"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # メタデータのみのテストデータ
        metadata_only_data = {
            "_metadata": {
                "ward": "練馬区",
                "school": f"メタデータのみ_{timestamp}",
                "school_folder_url": "https://drive.google.com/drive/folders/test_metadata_only",
                "file_name": f"metadata_only_{timestamp}.pdf",
                "analysis_timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
        print(f"\nメタデータのみ書き込みテスト:")
        print(f"  学校名: {metadata_only_data['_metadata']['school']}")
        
        success = write_data(self.worksheet, metadata_only_data)
        
        assert success, "メタデータのみの書き込みに失敗"
        print("✓ メタデータのみ書き込み成功")


if __name__ == "__main__":
    # 直接実行時のテスト
    test_writer = TestSheetsWriter()
    test_writer.setup_class()
    
    print("=== sheets/writer.py 単体テスト ===\n")
    
    try:
        test_writer.test_get_header_row()
        test_writer.test_convert_json_to_row_with_metadata()
        test_writer.test_convert_json_to_row_without_metadata()
        test_writer.test_write_data_complete_sample()
        test_writer.test_write_data_minimal_sample()
        test_writer.test_write_data_metadata_only()
        
        print("\n" + "="*70)
        print("✓ 全テストが成功しました！")
        print("✓ スプレッドシートにテストデータが書き込まれました")
        print(f"✓ 確認URL: https://docs.google.com/spreadsheets/d/{settings.spreadsheet_id}")
        print("="*70)
        
    except Exception as e:
        print(f"\n✗ テスト失敗: {str(e)}")
        raise