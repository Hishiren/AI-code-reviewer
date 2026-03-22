from __future__ import annotations
from typing import TYPE_CHECKING
from botocore.exceptions import ClientError
import boto3
import keyring


MODEL_ID_MAP = {
    "Nova 2 Lite": "amazon.nova-lite-v1:0",
    "Claude 3.5 Sonnet": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "Claude Haiku 4.5": "jp.anthropic.claude-haiku-4-5-20251001-v1:0",
    "Gemma 3 12B IT": "google.gemma-3-12b-it",
}
REVIEW_CONFIGS = {
    "Refactoring": {
        "instruction": "コードの内容をリファクタリングしてください。",
        "requirements": "・命名の改善\n・関数の単一責任原則の適用\n・ガード節によるネストの解消",
    },
    "Bug-fix": {
        "instruction": "コード内の潜在的なバグを特定し、修正案を提示してください。",
        "requirements": "・エッジケースでの挙動確認\n・例外処理の不足の指摘\n・型安全性の確認",
    },
    "Security": {
        "instruction": "コードのセキュリティ脆弱性を診断し、対策を講じてください。",
        "requirements": "・OSコマンド注入やSQL注入の有無\n・機密情報のハードコードのチェック\n・不適切な権限管理の確認",
    },
    "Performance": {
        "instruction": "コードの実行効率を改善するための最適化案を提示してください。",
        "requirements": "・計算量の削減（ループの最適化）\n・メモリ使用量の抑制\n・不要なI/OやAPIコールの削減",
    },
}
SERVICE_NAME = "AI-Code-Reviewer"


def review_code(
    language: str,
    model_name: str,
    review_type: str,
    code_prompt: str,
    auth_config: AuthConfig,
):
    """コードレビューを実行し、結果を返す"""
    bedrock_client = _create_bedrock_client(auth_config)
    model_id = _resolve_model_id(model_name)
    review_config = _resolve_review_config(review_type)
    system_prompt = _build_system_prompt(language, review_config)

    return _invoke_bedrock_api(bedrock_client, model_id, system_prompt, code_prompt)


def _resolve_model_id(model_name: str) -> str:
    """モデル名からモデルIDを解決する"""
    model_id = MODEL_ID_MAP.get(model_name)
    if model_id is None:
        available_models = list(MODEL_ID_MAP.keys())
        raise ValueError(
            f"Unknown model: '{model_name}'. Available models: {available_models}"
        )
    return model_id


def _resolve_review_config(review_type: str) -> dict:
    """レビュータイプから設定を解決する"""
    config = REVIEW_CONFIGS.get(review_type)
    if config is None:
        available_types = list(REVIEW_CONFIGS.keys())
        raise ValueError(
            f"Unknown review type: '{review_type}'. Available: {available_types}"
        )
    return config


def _build_system_prompt(language: str, review_config: dict) -> str:
    """システムプロンプトを構築する"""
    return f"""
    # 指示
    あなたは{language}のシニアエンジニアです。{review_config["instruction"]}

    # 要件
    {review_config["requirements"]}

    # 制約事項
    ・ロジックの本質的な入出力は変えないでください。（バグ修正の場合は正しい挙動に修正してください）

    # 出力形式
    1. 指摘の概要
    2. 修正すべき理由
    3. 修正案（コード例）
    """


def _invoke_bedrock_api(
    bedrock_client,
    model_id: str,
    system_prompt: str,
    code_prompt: str,
) -> str:
    """Bedrock APIを呼び出し、レビュー結果を取得する"""
    system = [{"text": system_prompt}]
    messages = [{"role": "user", "content": [{"text": code_prompt}]}]

    try:
        response = bedrock_client.converse(
            modelId=model_id,
            system=system,
            messages=messages,
            inferenceConfig={"maxTokens": 8192, "temperature": 0.3},
        )
    except ClientError as e:
        raise RuntimeError(f"Failed to invoke Bedrock model '{model_id}': {e}") from e

    return response["output"]["message"]["content"][0]["text"]


def _create_bedrock_client(auth_config: AuthConfig):
    """AWS Bedrock クライアントを作成する"""
    aws_access_key_id = auth_config.active_access_key_id
    aws_secret_access_key = _fetch_aws_secret_key(aws_access_key_id=aws_access_key_id)

    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=auth_config.region,
    )
    return session.client("bedrock-runtime")


def _fetch_aws_secret_key(aws_access_key_id: str) -> str:
    """キーリングからAWSシークレットキーを取得する"""
    secret_key = keyring.get_password(SERVICE_NAME, aws_access_key_id)
    if secret_key is None:
        raise ValueError(
            f"AWS secret key not found for access key: {aws_access_key_id}"
        )
    return secret_key


if TYPE_CHECKING:
    from appdata import AuthConfig
