from dataclasses import dataclass, field

@dataclass
class AppSettings:
    source_code_font: str = "Meiryo"
    review_mode: str = "Refactoring"
    ai_model: str = "Nova 2 Lite"
    source_code_language: str = "Python"
    default_text_font_size: int = 15

@dataclass
class AuthConfig:
    active_access_key_id: str = ""
    region: str = "ap-northeast-1"

@dataclass
class ReviewEntry:
    label_id: int
    # review_log: str = "sample log"
    input_code: str
    reviewed_code: str

@dataclass
class AppData:
    app_settings: AppSettings = field(default_factory=AppSettings)
    auth_config: AuthConfig = field(default_factory=AuthConfig)
    user_data: list[ReviewEntry] = field(default_factory=list)