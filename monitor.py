import sys
import os
import requests
import time
from datetime import datetime

# --- ログ出力 ---
sys.stdout.reconfigure(encoding='utf-8')
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# URL設定
BASE_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/"
LOGIN_PAGE = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"

def main():
    # 1. セッション（Cookie保持）を開始
    session = requests.Session()
    
    # 2. ヘッダーを「日本のWindowsのChrome」に完璧に偽装
    # レトロサイトはReferer（どこからリンクを踏んだか）を厳しく見ます
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Referer": BASE_URL,
        "Connection": "keep-alive"
    }
    session.headers.update(headers)

    try:
        # 3. まず玄関(BASE_URL)を叩いて、サーバーからJSESSIONIDを貰う
        log("🚪 玄関ページでCookieを確保中...")
        res1 = session.get(BASE_URL, timeout=15)
        log(f"Cookie取得: {session.cookies.get_dict()}")

        # 4. ログインページ本体をリクエスト
        log("📑 ログイン画面をリクエスト...")
        # 玄関から来たフリを維持したまま遷移
        res2 = session.get(LOGIN_PAGE, timeout=15)
        
        if "おわび" in res2.text:
            log("🚨 通信レベルで『おわび』判定されました。")
            # デバッグ: サーバーが返してきたHTMLの冒頭を出力
            log(f"Response (part): {res2.text[:300]}")
        elif "uid" in res2.text or "password" in res2.text or "mypageLogin" in res2.text:
            log("✨ おわびを回避！ログインフォームの通信に成功しました。")
            # ここでログインPOSTを構築（name属性に合わせる）
            payload = {
                "uid": os.environ.get("JKK_ID"),
                "passwd": os.environ.get("JKK_PASSWORD"),
                # 他に隠しパラメータ(hidden)があればここに追加
            }
            log("🚀 ログイン実行（POST）...")
            res3 = session.post(LOGIN_PAGE, data=payload)
            log(f"結果URL: {res3.url}")
        else:
            log("❓ 予期しないレスポンスです。ソースを確認してください。")
            log(res2.text[:500])

    except Exception as e:
        log(f"❌ 通信エラー: {e}")

if __name__ == "__main__":
    main()
