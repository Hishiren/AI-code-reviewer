import customtkinter
import pyperclip
import CTkMessagebox
import threading
import json
import datetime
import os
import sys
from PIL import Image
from dataclasses import asdict

import bedrock
import highlighting
import setting
import appdata

DEFAULT_FONT = "Meiryo"
LABEL_FONT_SIZE = 13
BUTTON_FONT_SIZE = 15
REVIEW_MODE_OPTIONS = ["Refactoring", "Bug-fix", "Security", "Performance"]
MODEL_OPTIONS = ["Nova 2 Lite", "Claude Haiku 4.5", "Gemma 3 12B IT"]
LANGUAGE_OPTIONS = ["JavaScript", "Python", "Go", "Kotlin", "Swift", "Java", "C#"]
ACTION_ICONS = [
    "delete",
    "archive",
    "archive_gray",
    "settings",
    "copy",
    "paste",
    "clear",
    "close",
    "delete_red",
    "open_in_full",
    "close_fullscreen",
]


class App(customtkinter.CTk):
    """メインフレーム"""

    def __init__(self):
        super().__init__()
        self.load_data()
        self.setup_ui()

    def setup_ui(self):
        """UI要素の初期化と配置"""
        self.geometry("1280x800")
        self.minsize(width=960, height=600)
        self.title("AI Code Reviewer")
        self.wm_iconbitmap(self.get_resource_path("images/icon.ico"))
        customtkinter.set_appearance_mode("dark")

        self.source_code_font = self.app_data.app_settings.source_code_font

        self.is_loading = False
        self.spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spin_index = 0

        self.active_label_index = 0
        self.images = self.load_images()

        # 操作パネルフレーム
        self.option_frame = ControlPanelFrame(master=self, resource=self.images)
        self.option_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nse")
        # テキストプレーム
        self.text_frame = TextFrame(
            master=self, resource=self.images, fg_color="transparent"
        )
        self.text_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        # アーカイブ用フレーム
        self.saved_text_frame = SavedTextFrame(
            master=self,
            text_frame_instance=self.text_frame,
            resource=self.images,
            fg_color="transparent",
        )
        self.saved_text_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        # 全画面用フレーム
        self.fullscreen_frame = FullScreenTextFrame(
            master=self,
            text_frame_instance=self.text_frame,
            resource=self.images,
            fg_color="transparent",
        )
        self.fullscreen_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.setting_window = None

        # アーカイブリスト初期表示
        self.option_frame.refresh_saved_text_frame(self.user_data_init)

        # 初期表示
        self.show_frame(self.text_frame)

        # 画面フォーム
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def load_data(self):
        """JSONファイルからデータを読み込む"""
        try:
            with open("data.json", "r", encoding="utf-8") as file:
                loaded_dict = json.load(file)
                settings = appdata.AppSettings(**loaded_dict.get("app_settings", {}))
                auth = appdata.AuthConfig(**loaded_dict.get("auth_config", {}))
                user_data_list = [
                    appdata.ReviewEntry(**item)
                    for item in loaded_dict.get("user_data", [])
                ]
                # AppDataクラスを構成
                self.app_data = appdata.AppData(
                    app_settings=settings, auth_config=auth, user_data=user_data_list
                )
                self.user_data_init = self.app_data.user_data
        except FileNotFoundError:
            # ファイルが存在しない場合は、空のdataclassをインスタンス化
            self.app_data = appdata.AppData()
            self.user_data_init = []
        except json.JSONDecodeError:
            # JSONファイルのでコードエラー
            CTkMessagebox.CTkMessagebox(
                master=self,
                title="エラー",
                message="data.jsonファイルの読み込みに失敗しました。ファイルが壊れている可能性があります。",
                icon="cancel",
                width=600,
            )

    def load_images(self) -> dict:
        """画像ファイルの読み込み"""
        image_objects = {}
        for name in ACTION_ICONS:
            image = customtkinter.CTkImage(
                Image.open(self.get_resource_path(f"images/{name}.png"))
            )
            image_objects[name] = image

        return image_objects

    def get_resource_path(self, relative_path):
        """リソースファイルへのパスを取得する"""
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.dirname(os.path.abspath(__file__))

        return os.path.join(base_path, relative_path)

    def save_data(self):
        """アーカイブデータをJSONファイルに保存する"""
        try:
            with open("data.json", "w", encoding="utf-8") as file:
                json.dump(asdict(self.app_data), file, ensure_ascii=False, indent=2)
        except Exception as e:
            CTkMessagebox.CTkMessagebox(
                master=self,
                title="エラー",
                message=f"data.jsonファイルの保存に失敗しました。\n{str(e)}",
                icon="cancel",
                width=600,
            )

    def show_frame(self, frame):
        """指定されたフレームを表示する"""
        frame.tkraise()

    def open_setting_window(self):
        """設定画面を表示する"""
        if self.setting_window is None or not self.setting_window.winfo_exists():
            self.setting_window = setting.SettingWindow(
                self,
                app_settings=self.app_data.app_settings,
                auth_config=self.app_data.auth_config,
            )
        else:
            self.setting_window.focus()

    def clear_text_areas(self):
        """入力および出力テキストエリアをクリアする"""
        self.text_frame.input_textbox.delete(0.0, "end")
        self.text_frame.output_textbox.configure(state="normal")
        self.text_frame.output_textbox.delete(0.0, "end")
        self.text_frame.output_textbox.configure(state="disabled")

    def change_font_size(self, new_font_size):
        """フォントサイズを変更する"""
        font_size = new_font_size
        # スライダーの値をセット
        self.text_frame.input_textbox.configure(font=(self.source_code_font, font_size))
        self.text_frame.output_textbox.configure(
            font=(self.source_code_font, font_size)
        )
        self.saved_text_frame.original_textbox.configure(
            font=(self.source_code_font, font_size)
        )
        self.saved_text_frame.reviewed_textbox.configure(
            font=(self.source_code_font, font_size)
        )
        self.fullscreen_frame.textbox.configure(font=(self.source_code_font, font_size))

    def on_input_modified(self, event=None):
        """入力テキストボックスの変更時に呼び出される"""
        self.check_input()
        self.highlighting()
        # modifiedフラグをFalseに戻す
        self.text_frame.input_textbox.edit_modified(False)

    def check_input(self, event=None):
        """入力テキストのチェックとボタンの状態更新"""
        self.after(10, self.update_button_state)

    def update_button_state(self, event=None):
        """ボタンの状態を更新する"""
        has_text = len(self.text_frame.input_textbox.get(0.0, "end").strip())
        self.set_buttons_state(has_text)

    def set_buttons_state(self, is_enabled: bool):
        """ボタンの状態を設定する"""
        state = "normal" if is_enabled else "disabled"
        self.option_frame.review_button.configure(state=state)
        self.option_frame.save_button.configure(state=state)

        if is_enabled:
            self.option_frame.save_button.configure(image=self.images["archive"])
        else:
            self.option_frame.save_button.configure(image=self.images["archive_gray"])

    def highlighting(self, event=None):
        """入力テキストをハイライトする"""
        text_object = self.text_frame.input_textbox
        code = self.text_frame.input_textbox.get(0.0, "end")
        try:
            highlighting.highlight(textbox=text_object, code=code)
        except Exception as e:
            print(f"Highlight error: {e}")
            return

    def archive_current_review(self, event=None):
        """レビュー結果をアーカイブする"""
        input_source_code = self.text_frame.input_textbox.get(0.0, "end")
        reviewed_source_code = self.text_frame.output_textbox.get(0.0, "end")

        next_index = 1
        if self.app_data.user_data:
            next_index = max(entry.label_id for entry in self.app_data.user_data) + 1

        review_entry = appdata.ReviewEntry(
            label_id=next_index,
            # review_log="",
            input_code=input_source_code,
            reviewed_code=reviewed_source_code,
        )
        self.app_data.user_data.append(review_entry)

        self.option_frame.refresh_saved_text_frame(self.app_data.user_data)
        self.save_data()

        CTkMessagebox.CTkMessagebox(
            master=self, title="完了", message="アーカイブしました。", icon="check"
        )

    def on_click_archived_label(self, input_code: str, reviewed_code: str, index: int):
        """アーカイブラベルがクリックされた時の動作"""
        self.saved_text_frame.update_text_display(input_code, reviewed_code)
        self.show_frame(self.saved_text_frame)
        self.active_label_index = index
        self.update_label_style(index=index)

    def update_label_style(self, index: int = 0):
        """ラベルのスタイルを一括更新する"""
        for label in self.option_frame.saved_text_frame.winfo_children():
            if label.index == index:
                label.configure(fg_color="#757575")  # アクティブ色
            else:
                label.configure(fg_color="#383838")  # 通常色

        self.set_buttons_state(False)

    def delete_selected_label(self):
        """選択されたラベルを削除する"""
        msg = CTkMessagebox.CTkMessagebox(
            master=self.master,
            title="確認",
            message="このアーカイブを削除しますか？",
            icon="question",
            option_1="キャンセル",
            option_2="OK",
        )
        responce = msg.get()
        if responce == "OK":
            target_id = self.active_label_index
            # ラベルIDが一致する要素を削除
            self.app_data.user_data = [
                entry
                for entry in self.app_data.user_data
                if entry.label_id != target_id
            ]
            self.option_frame.refresh_saved_text_frame(self.app_data.user_data)
            self.update_button_state()
            self.show_frame(self.text_frame)
            self.save_data()

    def copy_output_text(self):
        """レビュー結果をコピーする"""
        text = self.text_frame.output_textbox.get(0.0, "end")
        pyperclip.copy(text)

    def paste_text(self):
        """テキストを貼り付ける"""
        text = pyperclip.paste()
        self.text_frame.input_textbox.insert("end", text)

    def execute_code_review(self):
        """コードレビューを実行"""
        input_code = self.text_frame.input_textbox.get(0.0, "end")
        selected_language = self.option_frame.language_option.get()
        selected_model = self.option_frame.model_option.get()
        review_type = self.option_frame.review_option.get()

        try:
            bedrock_output = bedrock.review_code(
                selected_language,
                selected_model,
                review_type,
                input_code,
                self.app_data.auth_config,
            )
        except Exception as e:
            CTkMessagebox.CTkMessagebox(
                master=self,
                title="予期しないエラー",
                message=f"エラーが発生しました。\n{str(e)}",
                icon="cancel",
                width=600,
            )
            return
        finally:
            self.after(0, self.stop_loading)

        # 出力結果をテキストボックスに表示
        self.text_frame.update_output_text(
            new_code=bedrock_output,
            review_mode=review_type,
            model=selected_model,
            language=selected_language,
        )

    def start_loading(self):
        """読み込み開始アニメーションを開始する"""
        self.is_loading = True
        self.option_frame.review_button.configure(state="disabled")  # 二重クリック防止

        self.animate_button(0)
        thread = threading.Thread(target=self.execute_code_review)
        thread.start()

    def animate_button(self, event=None):
        """読み込みアニメーションを更新する"""
        if self.is_loading:
            self.option_frame.review_button.configure(
                text=f"レビュー中 {self.spinner[self.spin_index]}"
            )
            self.spin_index = (self.spin_index + 1) % len(self.spinner)
            self.after(300, self.animate_button)

    def stop_loading(self):
        """読み込みアニメーションを停止する"""
        self.is_loading = False
        self.option_frame.review_button.configure(state="normal", text="レビュー")


class ControlPanelFrame(customtkinter.CTkFrame):
    """操作パネルのオブジェクトを格納するフレーム"""

    def __init__(self, master, resource, **kwargs):
        super().__init__(master, **kwargs)
        self.images = resource

        self.initialize_layout(master, **kwargs)
        self._create_option_widgets()
        self._create_button_widgets()

    def initialize_layout(self, master, **kwargs):
        """レイアウトの初期化"""
        self.grid_rowconfigure(1, weight=1)

        self.option_frame = customtkinter.CTkFrame(master=self, fg_color="transparent")
        self.option_frame.grid(row=0, column=0, sticky="n")

        self.saved_text_frame = customtkinter.CTkScrollableFrame(
            master=self,
            width=50,
            fg_color="transparent",
            border_width=2,
            corner_radius=20,
        )
        self.saved_text_frame.grid(
            row=1, column=0, padx=10, pady=(0, 10), sticky="nsew"
        )

        self.button_frame = customtkinter.CTkFrame(master=self, fg_color="transparent")
        self.button_frame.grid(row=2, column=0, sticky="s")

    def _create_option_widgets(self):
        """オプションウィジェットの作成"""
        self._create_settings_button()
        self._create_review_mode_selecter()
        self._create_model_selecter()
        self._create_language_selecter()
        self._create_font_size_slider()
        self._create_archive_label()

    def _create_settings_button(self):
        """設定ボタンの作成"""
        self.settings_button = customtkinter.CTkButton(
            master=self.option_frame,
            text="",
            image=self.images["settings"],
            width=25,
            height=25,
            fg_color="transparent",
            command=self.master.open_setting_window,
        )
        self.settings_button.grid(row=0, column=0, padx=3, pady=3, sticky="wn")

    def _create_review_mode_selecter(self):
        """レビューモード選択ウィジェットの作成"""
        self.review_mode_label = customtkinter.CTkLabel(
            master=self.option_frame,
            text="レビューモード",
            fg_color="transparent",
            font=(DEFAULT_FONT, LABEL_FONT_SIZE, "bold"),
        )
        self.review_mode_label.grid(
            row=1, column=0, padx=10, pady=0, sticky="wn", columnspan=2
        )

        self.review_option = customtkinter.CTkOptionMenu(
            master=self.option_frame,
            values=REVIEW_MODE_OPTIONS,
            font=(DEFAULT_FONT, LABEL_FONT_SIZE),
            dropdown_font=(DEFAULT_FONT, LABEL_FONT_SIZE),
            command=self._on_click_review_mode_option,
        )
        self.review_option.set(
            self.master.app_data.app_settings.review_mode
        )  # 起動時のデフォルト
        self.review_option.grid(
            row=2, column=0, padx=10, pady=(0, 5), sticky="n", columnspan=2
        )

    def _create_model_selecter(self):
        """AIモデル選択ウィジェットの作成"""
        self.model_label = customtkinter.CTkLabel(
            master=self.option_frame,
            text="AIモデル",
            fg_color="transparent",
            font=(DEFAULT_FONT, LABEL_FONT_SIZE, "bold"),
        )
        self.model_label.grid(
            row=3, column=0, padx=10, pady=(10, 0), sticky="wn", columnspan=2
        )

        self.model_option = customtkinter.CTkOptionMenu(
            master=self.option_frame,
            values=MODEL_OPTIONS,
            command=self._on_click_model_option,
        )
        self.model_option.set(
            self.master.app_data.app_settings.ai_model
        )  # 起動時のデフォルト
        self.model_option.grid(
            row=4, column=0, padx=10, pady=(0, 5), sticky="n", columnspan=2
        )

    def _create_language_selecter(self):
        """ソースコード言語選択ウィジェットの作成"""
        self.language_label = customtkinter.CTkLabel(
            master=self.option_frame,
            text="ソースコード言語",
            fg_color="transparent",
            font=(DEFAULT_FONT, LABEL_FONT_SIZE, "bold"),
        )
        self.language_label.grid(
            row=5, column=0, padx=10, pady=(10, 0), sticky="wn", columnspan=2
        )

        self.language_option = customtkinter.CTkOptionMenu(
            master=self.option_frame,
            values=LANGUAGE_OPTIONS,
            command=self._on_click_source_code_option,
        )
        self.language_option.set(
            self.master.app_data.app_settings.source_code_language
        )  # 起動時のデフォルト
        self.language_option.grid(
            row=6, column=0, padx=10, pady=(0, 5), sticky="n", columnspan=2
        )

    def _create_font_size_slider(self):
        """文字サイズスライダーの作成"""
        min_size = self.master.app_data.app_settings.default_text_font_size - 5
        max_size = self.master.app_data.app_settings.default_text_font_size + 5

        self.font_size_label = customtkinter.CTkLabel(
            master=self.option_frame,
            text="文字の大きさ",
            fg_color="transparent",
            font=(DEFAULT_FONT, LABEL_FONT_SIZE, "bold"),
        )
        self.font_size_label.grid(
            row=7, column=0, padx=10, pady=(10, 0), sticky="wn", columnspan=2
        )

        self.font_size_slider = customtkinter.CTkSlider(
            master=self.option_frame,
            from_=min_size,
            to=max_size,
            width=140,
            height=20,
            command=self.master.change_font_size,
        )
        self.font_size_slider.grid(
            row=8, column=0, pady=10, padx=(0, 5), sticky="n", columnspan=2
        )

    def _create_archive_label(self):
        """アーカイブフレームラベルの作成"""
        self.archive_frame_label = customtkinter.CTkLabel(
            master=self.option_frame,
            text="アーカイブリスト",
            fg_color="transparent",
            font=(DEFAULT_FONT, LABEL_FONT_SIZE, "bold"),
        )
        self.archive_frame_label.grid(
            row=9, column=0, padx=10, pady=(10, 0), sticky="we", columnspan=2
        )

    def _create_button_widgets(self):
        """ボタンウィジェットの作成"""
        self._create_delete_button()
        self._create_archive_button()
        self._create_review_button()

    def _create_delete_button(self):
        """削除ボタンの作成"""
        # ラベルクリアボタン
        self.delete_all_label_button = customtkinter.CTkButton(
            master=self.button_frame,
            width=65,
            height=40,
            text="",
            corner_radius=20,
            font=(DEFAULT_FONT, BUTTON_FONT_SIZE, "bold"),
            fg_color="transparent",
            border_width=2,
            border_color=("#3E3E3E"),
            image=self.images["delete"],
            command=self.on_click_delete_all_label,
        )
        self.delete_all_label_button.grid(
            row=1, column=0, padx=(10, 5), pady=(3, 10), sticky="s"
        )

    def _create_archive_button(self):
        """アーカイブボタンの作成"""
        self.save_button = customtkinter.CTkButton(
            master=self.button_frame,
            width=65,
            height=40,
            text="",
            corner_radius=20,
            font=(DEFAULT_FONT, BUTTON_FONT_SIZE),
            fg_color="transparent",
            border_width=2,
            border_color=("#3E3E3E"),
            image=self.images["archive_gray"],
            state="disabled",
            command=self.master.archive_current_review,
        )
        self.save_button.grid(row=1, column=1, padx=(5, 10), pady=(3, 10), sticky="s")

    def _create_review_button(self):
        """レビューボタンの作成"""
        self.review_button = customtkinter.CTkButton(
            master=self.button_frame,
            text="レビュー",
            corner_radius=20,
            height=50,
            font=(DEFAULT_FONT, BUTTON_FONT_SIZE, "bold"),
            state="disabled",
            command=self.master.start_loading,
        )
        self.review_button.grid(
            row=3, column=0, padx=10, pady=(3, 10), sticky="s", columnspan=2
        )

    def refresh_saved_text_frame(self, user_data: list):
        """アーカイブリストの表示を更新"""
        self._clear_saved_text_label()

        for values in user_data:
            self._create_archive_label_widget(values)

    def _clear_saved_text_label(self):
        """保存済みテキストラベルをクリア"""
        for label in self.saved_text_frame.winfo_children():
            label.destroy()

    def _create_archive_label_widget(self, values):
        """アーカイブラベルウィジェットの作成"""
        key = values.label_id
        # log = values.review_log
        original_text = values.input_code
        reviewed_text = values.reviewed_code

        label = customtkinter.CTkLabel(
            master=self.saved_text_frame,
            text=f"レビュー{key}",
            font=(DEFAULT_FONT, 13),
            corner_radius=10,
            width=100,
            height=30,
            fg_color="#383838",
        )
        label.pack(pady=5, padx=(0, 10))
        label.index = key

        label.bind(
            "<Button-1>",
            lambda e: self._handle_archived_label_click(
                original_text, reviewed_text, index=key
            ),
        )

    def _handle_archived_label_click(
        self, original_text: str, reviewed_text: str, index: str
    ):
        """アーカイブラベルクリック時の処理"""
        self.master.on_click_archived_label(original_text, reviewed_text, index)

    def on_click_delete_all_label(self):
        """ラベルクリアボタンが押された時の動作"""
        msg = CTkMessagebox.CTkMessagebox(
            master=self.master,
            title="確認",
            message="アーカイブリストをクリアしますか？",
            icon="question",
            option_1="キャンセル",
            option_2="OK",
        )
        responce = msg.get()
        if responce == "OK":
            self.master.app_data.user_data.clear()
            self.master.show_frame(self.master.text_frame)
            self.refresh_saved_text_frame(self.master.app_data.user_data)
            self.master.save_data()

    # =====各オプションの選択値が更新されたら呼び出される=====
    def _on_click_review_mode_option(self, choice):
        self.master.app_data.app_settings.review_mode = choice
        self.master.save_data()

    def _on_click_model_option(self, choice):
        self.master.app_data.app_settings.ai_model = choice
        self.master.save_data()

    def _on_click_source_code_option(self, choice):
        self.master.app_data.app_settings.source_code_language = choice
        self.master.save_data()


class TextFrame(customtkinter.CTkFrame):
    """
    テキストボックス類を格納するフレーム
    """

    LABEL_HEIGHT = 23
    BUTTON_SIZE = 25
    BUTTON_CORNER_RADIUS = 20
    LABEL_CORNER_RADIUS = 20
    LABEL_BG_COLOR = "#343434"

    def __init__(self, master, resource, **kwargs):
        super().__init__(master, **kwargs)
        self.images = resource
        self.text_font_size = (
            self.master.app_data.app_settings.default_text_font_size  # 初期フォントサイズ
        )
        self.source_code_font = (
            self.master.app_data.app_settings.source_code_font  # ソースコードフォント
        )

        self._setup_layout()
        self._create_input_section()
        self._create_output_section()

    def _setup_layout(self) -> None:
        """グリッドレイアウトの初期化"""
        self.grid_columnconfigure((0, 2), weight=1)
        self.grid_rowconfigure(1, weight=1)

    def _create_input_section(self) -> None:
        """入力セクションのウィジェット作成"""
        # 入力ラベル
        self.input_label = self.create_label(
            master=self, text="Input", row=0, column=0, columnspan=2
        )
        # ペーストボタン
        self.paste_button = self.create_icon_button(
            master=self,
            image=self.images["paste"],
            command=self.master.paste_text,
            row=0,
            column=1,
        )
        # 入力テキストボックス
        self.input_textbox = customtkinter.CTkTextbox(
            master=self, wrap="word", font=(self.source_code_font, self.text_font_size)
        )
        self.input_textbox.grid(
            row=1, column=0, padx=(0, 5), pady=0, sticky="nsew", columnspan=2
        )
        self.input_textbox.bind("<<Modified>>", self.master.on_input_modified)

    def _create_output_section(self) -> None:
        """出力セクションのウィジェット作成"""
        # 出力ラベル
        self.output_label = self.create_label(
            master=self, text="Output", row=0, column=2, columnspan=3
        )
        # コピーボタン
        self.copy_button = self.create_icon_button(
            master=self,
            image=self.images["copy"],
            command=self.master.copy_output_text,
            row=0,
            column=3,
        )
        # クリアボタン
        self.clear_button = self.create_icon_button(
            master=self,
            image=self.images["clear"],
            command=self.master.clear_text_areas,
            row=0,
            column=4,
        )
        # 出力テキストボックス
        self.output_textbox = customtkinter.CTkTextbox(
            master=self,
            wrap="word",
            font=(self.source_code_font, self.text_font_size),
            state="disabled",
        )
        self.output_textbox.grid(
            row=1, column=2, padx=(5, 0), pady=0, sticky="nsew", columnspan=3
        )

    def create_label(
        self,
        master: customtkinter.CTkFrame,
        text: str,
        row: int,
        column: int,
        columnspan: int = 1,
    ) -> customtkinter.CTkLabel:
        """ラベルウィジェットの作成"""
        label = customtkinter.CTkLabel(
            master=master,
            height=self.LABEL_HEIGHT,
            fg_color=self.LABEL_BG_COLOR,
            corner_radius=self.LABEL_CORNER_RADIUS,
            text=text,
            font=(self.source_code_font, LABEL_FONT_SIZE, "bold"),
        )
        label.grid(row=row, column=column, pady=(0, 5), columnspan=columnspan)
        return label

    def create_icon_button(
        self,
        master: customtkinter.CTkFrame,
        image: customtkinter.CTkImage,
        command: callable,
        row: int,
        column: int,
        columnspan: int = 1,
        sticky: str = None,
    ) -> customtkinter.CTkButton:
        """アイコンボタンの作成"""
        button = customtkinter.CTkButton(
            master=master,
            text="",
            corner_radius=self.BUTTON_CORNER_RADIUS,
            image=image,
            width=self.BUTTON_SIZE,
            height=self.BUTTON_SIZE,
            fg_color="transparent",
            command=command,
        )
        button.grid(
            row=row, column=column, pady=(0, 3), columnspan=columnspan, sticky=sticky
        )
        return button

    def update_output_text(self, new_code, review_mode, model, language) -> None:
        """出力テキストボックスの表示を更新"""
        self.output_textbox.configure(state="normal")
        self.output_textbox.delete(0.0, "end")

        self._insert_code(new_code)
        self._insert_review_info(review_mode, model, language)

        self.output_textbox.configure(state="disabled")

    def _insert_review_info(self, review_mode, model, language) -> None:
        """レビューログを挿入"""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        insert_text = (
            f"### レビューログ\n"
            f"- **Timestamp**: {now}\n"
            f"- **Review Mode**: `{review_mode}`\n"
            f"- **AI Model**: {model}\n"
            f"- **Language**: {language}\n"
            f"{'---' * 10}\n\n"
        )
        self.output_textbox.insert("0.0", insert_text)

    def _insert_code(self, code: str) -> None:
        """コードを挿入してハイライト"""
        self.output_textbox.insert("end", code)

        try:
            highlighting.highlight(textbox=self.output_textbox, code=code)
        except Exception as e:
            print(f"Highlight error: {e}")


class SavedTextFrame(customtkinter.CTkFrame):
    """
    保存されたチャットを表示するフレーム
    """

    def __init__(self, master, text_frame_instance, resource, **kwargs):
        super().__init__(master, **kwargs)
        self.images = resource
        self.text_frame = text_frame_instance
        self.text_font_size = (
            self.master.app_data.app_settings.default_text_font_size  # 初期フォントサイズ
        )
        self.source_code_font = (
            self.master.app_data.app_settings.source_code_font  # ソースコードフォント
        )

        self._setup_layout()
        self._create_buttons()
        self._create_textboxes()
        self._create_label()

    def _setup_layout(self):
        """グリッドレイアウトを設定"""
        self.grid_columnconfigure((1, 2), weight=1)
        self.grid_rowconfigure(1, weight=1)

    def _create_buttons(self) -> None:
        """ボタンウィジェットを作成"""
        # 戻るボタン
        self.return_button = self.text_frame.create_icon_button(
            master=self,
            image=self.images["close"],
            command=self._on_return_clicked,
            row=0,
            column=0,
            sticky="w",
        )
        # アーカイブ削除ボタン
        self.delete_archive = self.text_frame.create_icon_button(
            master=self,
            image=self.images["delete_red"],
            command=self.master.delete_selected_label,
            row=0,
            column=3,
            sticky="e",
        )
        # 全画面表示ボタン
        self.open_in_full_button = self.text_frame.create_icon_button(
            master=self,
            image=self.images["open_in_full"],
            command=self._on_open_in_full_clicked,
            row=0,
            column=4,
            sticky="e",
        )

    def _create_label(self) -> None:
        """テキストラベルを作成"""
        self.text_label = self.text_frame.create_label(
            master=self,
            text="アーカイブビュー",
            row=0,
            column=1,
            columnspan=3,
        )

    def _create_textboxes(self) -> None:
        """テキストボックスウィジェットを作成"""
        self.original_textbox = customtkinter.CTkTextbox(
            master=self,
            wrap="word",
            font=(self.source_code_font, self.text_font_size),
            state="disabled",
        )
        self.original_textbox.grid(
            row=1, column=0, padx=(0, 5), pady=0, sticky="nsew", columnspan=2
        )

        self.reviewed_textbox = customtkinter.CTkTextbox(
            master=self,
            wrap="word",
            font=(self.source_code_font, self.text_font_size),
            state="disabled",
        )
        self.reviewed_textbox.grid(
            row=1, column=2, padx=(5, 0), pady=0, sticky="nsew", columnspan=3
        )

    def _on_return_clicked(self) -> None:
        """戻るボタンクリック時の処理"""
        self.master.update_label_style()
        self.master.update_button_state()
        self.master.show_frame(self.master.text_frame)

    def _on_open_in_full_clicked(self) -> None:
        """全画面表示ボタンクリック時の処理"""
        reviewd_code = self.review_code
        self._update_textbox(self.master.fullscreen_frame.textbox, reviewd_code)
        self.master.show_frame(self.master.fullscreen_frame)

    def update_text_display(self, input_code, reviewed_code) -> None:
        """アーカイブテキストボックスの表示を更新"""
        self._update_textbox(self.original_textbox, input_code)
        self._update_textbox(self.reviewed_textbox, reviewed_code)
        self.review_code = reviewed_code  # メンバ変数に一時保存

    def _update_textbox(self, textbox, code) -> None:
        """単一のテキストボックスを更新"""
        textbox.configure(state="normal")
        textbox.delete(0.0, "end")
        textbox.insert("end", code)

        try:
            highlighting.highlight(textbox=textbox, code=code)
        except Exception as e:
            print(f"Highlight error: {e}")
        finally:
            textbox.configure(state="disabled")


class FullScreenTextFrame(customtkinter.CTkFrame):
    """
    フルスクリーン表示用のテキストフレーム
    """

    def __init__(self, master, text_frame_instance, resource, **kwargs):
        super().__init__(master, **kwargs)
        self.images = resource
        self.text_frame = text_frame_instance
        self.text_font_size = (
            self.master.app_data.app_settings.default_text_font_size  # 初期フォントサイズ
        )
        self.source_code_font = (
            self.master.app_data.app_settings.source_code_font  # ソースコードフォント
        )

        self._setup_layout()
        self._create_button()
        self._create_textframe()

    def _setup_layout(self):
        """グリッドレイアウトを設定"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def _create_button(self) -> None:
        """ボタンウィジェットを作成"""
        self.open_in_full_button = self.text_frame.create_icon_button(
            master=self,
            image=self.images["close_fullscreen"],
            command=self._on_close_fullscreen_clicked,
            row=0,
            column=0,
            sticky="e",
        )

    def _create_textframe(self) -> None:
        """テキストボックスウィジェットを作成"""
        self.textbox = customtkinter.CTkTextbox(
            master=self,
            wrap="word",
            font=(self.source_code_font, self.text_font_size),
            state="disabled",
        )
        self.textbox.grid(row=1, column=0, padx=(0, 5), pady=0, sticky="nsew")

    def _on_close_fullscreen_clicked(self) -> None:
        """閉じるボタンクリック時の処理"""
        self.master.show_frame(self.master.saved_text_frame)


if __name__ == "__main__":
    app = App()
    app.mainloop()
