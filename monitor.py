import sys
import os
import requests
from datetime import datetime

# --- ログ出力 ---
sys.stdout.reconfigure(encoding='utf-8')
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# URL設定
BASE_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/"
LOGIN_POST_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"

def main():
    # 1. セッション（Cookie保持）を開始
    session = requests.Session()
    
    # 2. ヘッダーを「日本のWindowsのChrome」に完璧に偽装
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Referer": BASE_URL
    })

    try:
        # 3. まずは玄関ページを叩いてセッションID（JSESSIONID）を貰う
        log("🚪 玄関ページでCookieを確保中...")
        res_init = session.get(BASE_URL)
        log(f"Cookie取得状況: {session.cookies.get_dict()}")

        # 4. ログインページへアクセス（ここで「おわび」が出るか確認）
        log("📑 ログイン画面のリソースを要求...")
        res_login_page = session.get(LOGIN_POST_URL)
        
        if "おわび" in res_login_page.text:
            log("🚨 通信レベルで『おわび』判定されました。")
            # デバッグ: なぜダメなのか、レスポンスの冒頭を確認
            log(res_login_page.text[:300])
        else:
            log("✨ おわびを回避！ログインフォームの通信に成功しました。")
            
            # 5. POSTデータの構築（レトロサイトの典型的なパラメータ名）
            # 注意: 実際のパラメータ名はサイトのソースに合わせる必要があります
            payload = {
                "uid": os.environ.get("JKK_ID"),
                "passwd": os.environ.get("JKK_PASSWORD"),
                # 他に必要な隠しパラメータ（hidden）があればここに追加
            }
            
            log("🚀 ログイン情報をPOST送信します...")
            res_final = session.post(LOGIN_POST_URL, data=payload)
            
            if res_final.status_code == 200:
                log(f"送信完了。最終URL: {res_final.url}")
                # 成功していれば、ここで空室検索のURLを叩きにいく
            else:
                log(f"❌ 送信エラー: {res_final.status_code}")

    except Exception as e:
        log(f"❌ システムエラー: {e}")

if __name__ == "__main__":
    main()
