import sys
import os
import requests
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# URL構成
BASE_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/"
# 多くのレトロJavaサイトで「本丸」となるログイン実行パス
LOGIN_EXEC_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"

def main():
    session = requests.Session()
    # 日本の一般的なWindows環境を完璧に偽装
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Origin": "https://jhomes.to-kousya.or.jp",
        "Referer": BASE_URL, # 常に紹介元をセット
    })

    try:
        log("🚪 玄関ページで初期セッションを確立...")
        session.get(BASE_URL)
        
        log(f"🔑 セッションID: {session.cookies.get('JSESSIONID')}")

        # ログインPOSTデータの構築
        # レトロサイトが期待する「画像ボタンのクリック座標」もダミーで付与
        payload = {
            "uid": os.environ.get("JKK_ID"),
            "passwd": os.environ.get("JKK_PASSWORD"),
            "login.x": "45", # ログインボタン（画像）のクリック位置を偽装
            "login.y": "15"
        }

        log("🚀 ログイン情報を直接ブチ込みます（POST送信）...")
        # 遷移を挟まず、玄関の勢いそのままにPOST
        res = session.post(LOGIN_EXEC_URL, data=payload)
        res.encoding = 'cp932'

        log(f"📡 レスポンスステータス: {res.status_code}")
        
        # 成功判定：ソース内に「ログアウト」や「マイページ」があれば突破成功
        if "ログアウト" in res.text or "mypage" in res.url:
            log("🎉 ついに突破！マイページへの侵入に成功しました。")
            log(f"現在のURL: {res.url}")
            # ここから空室検索のURL（通常は searchU02Prepare.do など）へ！
        elif "おわび" in res.text:
            log("🚨 サーバーに拒否（おわび）されました。手順がまだ足りないようです。")
        else:
            log("🔎 突破したか不明です。タイトルを確認します。")
            # タイトルタグを抽出
            if "<title>" in res.text:
                title = res.text.split("<title>")[1].split("</title>")[0]
                log(f"ページタイトル: {title}")
            
            # 手がかりのためにHTMLの一部を表示
            log("--- レスポンス内容 (500-1000) ---")
            log(res.text[500:1000].replace('\n', ' '))

    except Exception as e:
        log(f"❌ システムエラー: {e}")

if __name__ == "__main__":
    main()
