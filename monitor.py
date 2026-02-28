import sys
import os
import time

# --- 冒頭に追加：ログのバッファリングを無効化 ---
sys.stdout.reconfigure(encoding='utf-8')
print("🚀 スクリプトを開始します...", flush=True)

try:
    from selenium import webdriver
    # ... 他のインポート ...
    print("✅ ライブラリの読み込み完了", flush=True)
except Exception as e:
    print(f"❌ ライブラリ読み込みエラー: {e}", flush=True)
    sys.exit(1)

# --- 中略：これまでのロジック ---

def main():
    # ID/PASSが空じゃないかチェック
    if not JKK_ID or not JKK_PASS:
        print("❌ エラー: JKK_ID または JKK_PASSWORD が設定されていません。", flush=True)
        return

    driver = None
    try:
        driver = setup_driver()
        print("✅ ブラウザの起動に成功", flush=True)
        # ログイン処理へ...
        if login_and_check(driver):
            print("🚨 ログイン突破成功！！！", flush=True)
            # スキャン処理へ...
    except Exception as e:
        print(f"❌ 実行中に予期せぬエラーが発生しました: {e}", flush=True)
    finally:
        if driver:
            driver.quit()
        print("🏁 スクリプトを終了します。", flush=True)

if __name__ == "__main__":
    main()
