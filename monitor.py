import sys
import os
import requests
import re
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

BASE_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/"
# ログイン画面を表示するURL
LOGIN_PAGE_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"

def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Referer": BASE_URL
    })

    try:
        log("🚪 セッションを開始...")
        session.get(BASE_URL)
        
        log("🔍 ログイン画面のHTMLを解析して『真の送信先』を探します...")
        res = session.get(LOGIN_PAGE_URL)
        res.encoding = 'cp932'
        
        # フォームの action 属性を抽出
        # 例: <form name="LF" method="post" action="mypageLogin.do">
        action_match = re.search(r'action=["\']([^"\']+)["\']', res.text)
        
        if action_match:
            action_path = action_match.group(1)
            log(f"🎯 真の送信先を発見: {action_path}")
            
            # 相対パスを絶対パスに変換
            post_url = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/" + action_path
            
            payload = {
                "uid": os.environ.get("JKK_ID"),
                "passwd": os.environ.get("JKK_PASSWORD"),
                "login.x": "0", "login.y": "0"
            }
            
            log(f"🚀 {post_url} へログインPOSTを実行...")
            # ここでPOST。もしここでも405なら、URLの組み立てを微調整します
            final_res = session.post(post_url, data=payload)
            final_res.encoding = 'cp932'
            
            log(f"📡 ステータス: {final_res.status_code}")
            if "ログアウト" in final_res.text:
                log("🎉 今度こそ本当に突破成功！")
            else:
                log("🚨 ログインに失敗しました。ID/PASSまたはパラメータが違います。")
                log(f"タイトル: {re.search(r'<title>(.*?)</title>', final_res.text).group(1) if '<title>' in final_res.text else '不明'}")
        
        else:
            log("🚨 HTML内に <form action=...> が見つかりませんでした。")
            log(f"取得できたHTML冒頭: {res.text[:300].replace('\\n', ' ')}")

    except Exception as e:
        log(f"❌ エラー: {e}")

if __name__ == "__main__":
    main()
