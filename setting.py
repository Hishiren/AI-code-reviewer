import customtkinter
import keyring
import FloatSpinbox
from typing import Tuple


class SettingWindow(customtkinter.CTkToplevel):
    """設定ウィンドウ"""

    # 定数
    LABEL_AND_BUTTON_STYLE = ("Meiryo", 13, "bold")
    WINDOW_WIDTH = 400
    WINDOW_HEIGHT = 320
    ENTRY_WIDTH = 300
    BUTTON_WIDTH = 100
    SERVICE_NAME = "AI-Code-Reviewer"
    SOURCE_CODE_FONTS = [
        "Meiryo",
        "JetBrains Mono",
        "Fira Code",
        "Hack",
        "Source Code Pro",
        "HackGen",
    ]

    def __init__(self, *args, app_settings, auth_config, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_settings = app_settings
        self.auth_config = auth_config
        self.setup_window()
        self.build_ui()
        self._display_credentials()

    def setup_window(self) -> None:
        """ウィンドウの基本設定を行う"""
        self.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.minsize(width=self.WINDOW_WIDTH, height=self.WINDOW_HEIGHT)
        self.title("設定")
        self.attributes("-topmost", True)
        self.after(100, self.focus_force)

    def build_ui(self) -> None:
        """UI要素を作成する"""
        main_frame = self._create_main_frame()
        self._build_font_settings(main_frame)
        self._build_text_size_settings(main_frame)
        self._build_aws_credentials_settings(main_frame)
        self._build_button_area(main_frame)

    def _create_main_frame(self) -> customtkinter.CTkFrame:
        """メインフレームを作成して返す"""
        frame = customtkinter.CTkFrame(self, fg_color="transparent")
        frame.pack(padx=(20, 10), pady=(10, 10), fill="both", expand=True)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(7, weight=1)
        return frame

    def _build_font_settings(self, parent_frame: customtkinter.CTkFrame) -> None:
        """フォント設定フィールドを作成する"""
        label = customtkinter.CTkLabel(
            master=parent_frame,
            text="テキストフォント",
            fg_color="transparent",
            font=self.LABEL_AND_BUTTON_STYLE,
        )
        label.grid(row=0, column=0, sticky="wn")

        self.font_option = customtkinter.CTkComboBox(
            master=parent_frame, values=self.SOURCE_CODE_FONTS
        )
        self.font_option.grid(row=1, column=0, sticky="wn")
        self.font_option.set(self.app_settings.source_code_font)

    def _build_text_size_settings(self, parent_frame: customtkinter.CTkFrame) -> None:
        """テキストサイズ設定フィールドを作成する"""
        label = customtkinter.CTkLabel(
            master=parent_frame,
            text="デフォルトテキストサイズ",
            fg_color="transparent",
            font=self.LABEL_AND_BUTTON_STYLE,
        )
        label.grid(row=2, column=0, pady=(20, 0), sticky="wn")

        self.default_text_size = FloatSpinbox.FloatSpinbox(
            parent_frame, width=150, step_size=1
        )
        self.default_text_size.grid(row=3, column=0, sticky="wn")
        self.default_text_size.set(self.app_settings.default_text_font_size)

    def _build_aws_credentials_settings(
        self, parent_frame: customtkinter.CTkFrame
    ) -> None:
        """AWS認証設定フィールドを作成する"""
        label = customtkinter.CTkLabel(
            master=parent_frame,
            text="AWS認証設定",
            fg_color="transparent",
            font=self.LABEL_AND_BUTTON_STYLE,
        )
        label.grid(row=4, column=0, pady=(20, 0), sticky="wn")

        self.aws_access_key_entry = customtkinter.CTkEntry(
            parent_frame, width=self.ENTRY_WIDTH, placeholder_text="アクセスキーを入力"
        )
        self.aws_access_key_entry.grid(row=5, column=0, sticky="wn")

        self.aws_secret_key_entry = customtkinter.CTkEntry(
            parent_frame,
            width=self.ENTRY_WIDTH,
            placeholder_text="シークレットキーを入力",
            show="*",
        )
        self.aws_secret_key_entry.grid(row=6, column=0, pady=15, sticky="wn")

    def _build_button_area(self, parent_frame: customtkinter.CTkFrame) -> None:
        """OKボタンを作成する"""
        self.btn_ok = customtkinter.CTkButton(
            parent_frame,
            text="OK",
            font=self.LABEL_AND_BUTTON_STYLE,
            width=self.BUTTON_WIDTH,
            command=self._on_ok_clicked,
        )
        self.btn_ok.grid(row=7, column=0, sticky="se")

    def _on_ok_clicked(self) -> None:
        """OKボタンクリック時の処理"""
        self._save_application_settings()

        # 保存処理の成功確認
        if not self._save_credentials():
            self._show_error("認証情報の保存に失敗しました")
            return
        self.destroy()

    def _get_entry_input(self) -> Tuple[str, str]:
        """入力フィールドから認証情報を取得する"""
        access_key = self.aws_access_key_entry.get().strip()
        secret_key = self.aws_secret_key_entry.get().strip()
        return access_key, secret_key

    def _get_saved_secret_key(self) -> str:
        """保存済みのAWSシークレットキーを取得する"""
        secret_key = keyring.get_password(
            self.SERVICE_NAME, self.auth_config.active_access_key_id
        )
        if secret_key is None:
            return ""
        return secret_key

    def _save_application_settings(self) -> None:
        """アプリケーション設定を保存する"""
        self.app_settings.source_code_font = self.font_option.get()
        self.app_settings.default_text_font_size = self.default_text_size.get()
        self.auth_config.active_access_key_id = self.aws_access_key_entry.get().strip()
        self.master.save_data()

    def _save_credentials(self) -> bool:
        """AWS認証情報を保存する"""
        access_key, secret_key = self._get_entry_input()
        try:
            keyring.set_password(self.SERVICE_NAME, access_key, secret_key)
            return True
        except Exception as e:
            print(f"Error saving credentials: {e}")
            return False
        
    def _display_credentials(self) -> None:
        """AWS認証情報を表示する"""
        access_key = self.auth_config.active_access_key_id
        secret_key = self._get_saved_secret_key()

        if not access_key or not secret_key.strip():
            return # 認証キーが存在しない場合は何もしない
        
        self.aws_access_key_entry.insert(0, access_key)
        self.aws_secret_key_entry.insert(0, secret_key)
        

    def _show_error(self, message: str) -> None:
        """エラーメッセージを表示する"""
        error_window = customtkinter.CTkToplevel(self)
        error_window.title("エラー")
        error_window.geometry("300x100")

        label = customtkinter.CTkLabel(error_window, text=message, wraplength=250)
        label.pack(padx=20, pady=20)

        button = customtkinter.CTkButton(
            error_window, text="OK", command=error_window.destroy
        )
        button.pack(pady=10)
