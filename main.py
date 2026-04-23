#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 必要なライブラリのインストール:
# pip install pyautogui pyperclip

import time
import sys
import os
import platform

import pyautogui
import pyperclip

# OS判定（Windowsの場合は 'ctrl'、macの場合は 'command'）
PASTE_KEY = "command" if platform.system() == "Darwin" else "ctrl"

# ============================================================
# 定数
# ============================================================
LIBRARY_FILENAME = "library.txt"
WAIT_BEFORE_START = 3       # 入力開始前の猶予時間（秒）
WAIT_CLIPBOARD    = 0.1     # クリップボード反映待ち（秒）
WAIT_PASTE        = 0.2     # ペースト完了待ち（秒）
WAIT_INTERVAL     = 0.3     # 次の入力までのインターバル（秒）


# ============================================================
# ライブラリファイルの読み込み
# ============================================================
def load_library(filepath: str) -> dict[str, list[str]]:
    """
    library.txt を読み込み、タグをキー、文字列リストを値とする辞書を返す。

    フォーマット例:
        /tag-1::音楽 ロック ギター 疾走感
        /tag-2::映画 洋画 アクション
    """
    if not os.path.exists(filepath):
        print(f"[エラー] ライブラリファイルが見つかりません: {filepath}", file=sys.stderr)
        sys.exit(1)

    library: dict[str, list[str]] = {}

    with open(filepath, encoding="utf-8") as f:
        for lineno, raw_line in enumerate(f, start=1):
            line = raw_line.strip()

            # 空行・コメント行はスキップ
            if not line or line.startswith("#"):
                continue

            if "::" not in line:
                print(
                    f"[警告] フォーマットエラー (行 {lineno}): '::' が見つかりません → スキップします",
                    file=sys.stderr,
                )
                continue

            tag, _, words_str = line.partition("::")
            tag = tag.strip()
            words = [w for w in words_str.split(" ") if w]  # 空トークンを除去

            if not tag:
                print(
                    f"[警告] フォーマットエラー (行 {lineno}): タグが空です → スキップします",
                    file=sys.stderr,
                )
                continue

            if not words:
                print(
                    f"[警告] フォーマットエラー (行 {lineno}): 文字列群が空です → スキップします",
                    file=sys.stderr,
                )
                continue

            library[tag] = words

    if not library:
        print("[エラー] ライブラリが空か、有効な定義が1件もありません。", file=sys.stderr)
        sys.exit(1)

    return library


# ============================================================
# ユーザー入力の受付
# ============================================================
def show_tag_list(library: dict[str, list[str]]) -> None:
    """利用可能なタグ一覧を表示する。"""
    print("\n利用可能なタグ一覧:")
    for tag, words in library.items():
        print(f"  {tag}  →  {' '.join(words)}")
    print()


def prompt_tag(library: dict[str, list[str]]) -> str:
    """
    有効なタグが入力されるまでプロンプトを繰り返す。
    Ctrl+C で安全に終了できる。
    """
    while True:
        try:
            user_input = input("タグを入力（例: /tag-1 / 終了: q）: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[中断] スクリプトを終了します。")
            sys.exit(0)

        if user_input.lower() == "q":
            print("スクリプトを終了します。")
            sys.exit(0)

        if user_input in library:
            return user_input

        print(f"[警告] タグ '{user_input}' は定義されていません。もう一度入力してください。\n")


# ============================================================
# 実行待機
# ============================================================
def countdown(seconds: int) -> None:
    """カウントダウン表示付きのスリープ。"""
    print(
        f"\n{seconds}秒後に入力を開始します。"
        "対象の入力欄をアクティブ（クリック）にしてください...",
        flush=True,
    )
    for i in range(seconds, 0, -1):
        print(f"  {i}...", flush=True)
        time.sleep(1)
    print("入力を開始します！\n", flush=True)


# ============================================================
# 自動入力ループ
# ============================================================
def auto_type(words: list[str]) -> None:
    """
    文字列リストをクリップボード経由で順番にペースト & エンター送信する。
    pyautogui.FailSafeException (マウスを四隅へ移動) で緊急停止する。
    """
    total = len(words)
    for idx, word in enumerate(words, start=1):
        print(f"  [{idx}/{total}] 入力中: {word}", flush=True)

        # 1. クリップボードにコピー
        pyperclip.copy(word)

        # 2. クリップボード反映待ち
        time.sleep(WAIT_CLIPBOARD)

        # 3. ペースト
        pyautogui.hotkey(PASTE_KEY, "v")

        # 4. ペースト完了待ち
        time.sleep(WAIT_PASTE)

        # 5. Enter キーを送信
        pyautogui.press("enter")

        # 6. 次の入力までのインターバル
        time.sleep(WAIT_INTERVAL)


# ============================================================
# メイン関数
# ============================================================
def main() -> None:
    # ---- ライブラリ読み込み ----
    script_dir   = os.path.dirname(os.path.abspath(__file__))
    library_path = os.path.join(script_dir, LIBRARY_FILENAME)
    library      = load_library(library_path)

    # ---- タグ一覧を表示 ----
    show_tag_list(library)

    # ---- メインループ（繰り返しタグ選択 → 自動入力） ----
    while True:
        # ---- タグ選択 ----
        selected_tag = prompt_tag(library)
        words        = library[selected_tag]
        print(f"\nタグ '{selected_tag}' を選択しました。入力文字列: {words}")

        # ---- カウントダウン ----
        countdown(WAIT_BEFORE_START)

        # ---- 自動入力 ----
        try:
            auto_type(words)
        except pyautogui.FailSafeException:
            print(
                "\n[緊急停止] マウスが画面の四隅に移動したため、安全に停止しました。",
                file=sys.stderr,
            )
            sys.exit(1)

        print("\n処理が完了しました。")
        print("-" * 40)


# ============================================================
# エントリーポイント
# ============================================================
if __name__ == "__main__":
    main()

