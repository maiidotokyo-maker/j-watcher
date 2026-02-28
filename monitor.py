import sys
import os
import requests
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# ログイン後の「空室検索」などの本丸URL
TARGET_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/emptyConditionSearch"

def main():
    session = requests.Session()
    
    # GitHub Secretsに保存した「生のCookie」をセット
    cookie_value = os.environ.get("JKK_COOKIE")
    if not cookie_value:
        log("🚨 JKK_COOKIE が設定されていません。")
        return

    # サーバーを騙すための最小限のヘッダー
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": f"JSESSIONID={cookie_value}"
    })

    try:
        log("🚀 ログインをスキップして本丸へ直撃します...")
        res = session.get(TARGET_URL)
        res.encoding = 'cp932'
        
        if "おわび" in res.text:
            log("💀 Cookieを注入しても『おわび』。IP制限が強力すぎるか、Cookieが期限切れです。")
        elif "条件入力" in res.text or "空室" in res.text:
            log("🎉 突破成功！ついにログインの壁を越えました。")
            # ここから空室チェックの解析コードを書く
        else:
            log(f"❓ 未知のページ。Title: {res.text[:200]}")

    except Exception as e:
        log(f"❌ エラー: {e}")

if __name__ == "__main__":
    main()
