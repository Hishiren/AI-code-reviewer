import keyword
import tokenize
from io import BytesIO
import builtins as builtins_module


def highlight(textbox, code):
    """
    テキストボックスのコードをシンタックスハイライトする

    Args:
        textbox: Tkinter Text widget
        code: ハイライト対象のコード文字列
    """
    # 既存タグ削除
    for tag in textbox.tag_names():
        textbox.tag_remove(tag, "1.0", "end")

    # 入力値の検証
    if not isinstance(code, str):
        return

    if not code.strip():  # 空のコードは処理しない
        return

    # 改行コードを置き換え
    clean_code = "\n".join(code.splitlines())

    textbox.tag_config("keyword", foreground="#569CD6")  # Control Flow
    textbox.tag_config("string", foreground="#CE9178")  # 文字列
    textbox.tag_config("comment", foreground="#6A9955")  # コメント
    textbox.tag_config("number", foreground="#B5CEA8")  # 数値
    textbox.tag_config("builtin", foreground="#DCDCAA")  # 関数・メソッド
    textbox.tag_config("operator", foreground="#D4D4D4")  # 記号・演算子

    # 組み込み関数の安全な取得
    try:
        # builtinsモジュールから直接取得（型安定性を確保）
        builtins_set = set(dir(builtins_module))
    except Exception:
        builtins_set = set()

    def index_from_pos(line, col):
        """行・列からTkinterインデックスを生成"""
        return f"{line + 1}.{col}"

    try:
        # トークナイザーの初期化
        readline = BytesIO(clean_code.encode("utf-8")).readline
        tokens = tokenize.tokenize(readline)

        for token in tokens:
            try:
                tok_type = token.type
                tok_str = token.string
                (sline, scol) = token.start
                (eline, ecol) = token.end

                # インデックス計算時のバリデーション
                if sline < 1 or eline < 1 or scol < 0 or ecol < 0:
                    continue

                start = index_from_pos(sline - 1, scol)
                end = index_from_pos(eline - 1, ecol)

                # タグの適用
                if tok_type == tokenize.COMMENT:
                    textbox.tag_add("comment", start, end)

                elif tok_type == tokenize.STRING:
                    textbox.tag_add("string", start, end)

                elif tok_type == tokenize.NUMBER:
                    textbox.tag_add("number", start, end)

                elif tok_type == tokenize.NAME:
                    if tok_str in keyword.kwlist:
                        textbox.tag_add("keyword", start, end)
                    elif tok_str in builtins_set:
                        textbox.tag_add("builtin", start, end)

                elif tok_type == tokenize.OP:
                    textbox.tag_add("operator", start, end)

            except (ValueError, IndexError, tokenize.TokenError):
                # 個別トークンの処理エラーは無視して続行
                continue

    except (tokenize.TokenError, IndentationError, UnicodeDecodeError):
        # トークナイザーのエラーは無視（部分的なハイライトは適用済み）
        pass
    except Exception:
        # 予期しないエラーも無視
        pass
