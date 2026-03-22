# AI Code Reviewer

AIの力を活用して、コードの品質向上を支援するデスクトップアプリケーションです。入力したコードに対して、4つの異なる視点からAIが詳細なレビューを行い、元のコードと比較しながら確認できます。

---

## 🚀 主な機能

- **マルチモードレビュー**: 4つの専門的なレビューモードを選択可能
    - **Refactoring**: コードの可読性や構造の改善案を提示
    - **Bug Fix**: 潜在的なバグの特定と修正案の提案
    - **Security**: 脆弱性のチェックとセキュリティ対策の助言
    - **Performance**: 処理速度やリソース効率の最適化案を提示
- **直感的な比較UI**: 元のコードとAIの回答を左右に並べて表示し、変更箇所をひと目で把握
- **アーカイブ機能**: 過去のレビュー結果をJSON形式で保存・管理し、いつでも後で見返すことが可能
- **クリップボード連携**: `pyperclip`を活用し、スムーズなコードのコピー＆ペーストに対応

## 🛠 使用技術

### 開発環境・言語
- **Python**: 3.14.2

### ライブラリ・フレームワーク
- **GUI**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (モダンなダークモード対応UI)
- **AWS SDK**: [Boto3](https://aws.amazon.com/jp/sdk-for-python/) (AWS Bedrockとの連携)
- **Utility**: `pyperclip` (クリップボード操作), `json` (データ保存)

### AI / インフラ
- **AWS Bedrock**: 高性能な基盤モデルによるコード解析
- **PyInstaller**: 実行ファイル（.exe / .app）化による配布

## 📦 インストールと実行方法

~~最新の [Releases](https://github.com/Hishiren/AI-code-reviewer/releases) から `v1.0.0` のexeファイルをダウンロードして実行してください。~~ 準備中
