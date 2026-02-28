import sys
import os
import requests
import re
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

BASE_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/"
LOGIN_PAGE_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"

def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Referer": BASE_URL
    })

    try:
        log("🚪 セッション開始...")
        session.get(BASE_URL)
        
        log("🔍 ログイン画面を解析して『真の送信先』を抽出します...")
        res = session.get(LOGIN_PAGE_URL)
        res.encoding = 'cp932'
        
        # フォームの action を抽出（大文字小文字を問わない）
        action_match = re.search(r'action=["\']([^"\']+)["\']', res.text, re.I)
        
        if action_match:
            action_path = action_match.group(1)
            log(f"🎯 送信先を発見: {action_path}")
            
            # URLを結合（パスが / から始まるかチェック）
            if action_path.startswith('/'):
                post_url = "https://jhomes.to-kousya.or.jp" + action_path
            else:
                post_url = BASE_URL + action_path
            
            # ID/PASSのPOSTデータ
            # JKKは "uid" と "passwd" を使うことが多いです
            payload = {
                "uid": os.environ.get("JKK_ID"),
                "passwd": os.environ.get("JKK_PASSWORD"),
                "login.x": "0", 
                "login.y": "0"
            }
            
            log(f"🚀 POST送信実行 -> {post_url}")
            final_res = session.post(post_url, data=payload)
            final_res.encoding = 'cp932'
            
            log(f"📡 ステータス: {final_res.status_code}")
            
            # ログイン成否の確認
            if "ログアウト" in final_res.text or "マイページ" in final_res.text:
                log("🎉 ついに突破！ログインに成功しました。")
                log(f"到達URL: {final_res.url}")
            else:
                log("🚨 ログイン失敗。おわび画面か、入力エラーです。")
                # ページタイトルだけ抜いてみる
                title_match = re.search(r'<title>(.*?)</title>', final_res.text, re.I)
                if title_match:
                    log(f"ページタイトル: {title_match.group(1)}")
        else:
            log("🚨 <form action=...> が見つかりませんでした。")
            # エラーの原因になった部分を安全に出力
            log("取得したソースの一部:")
            print(res.text[:500], flush=True)

    except Exception as e:
        log(f"❌ 実行エラー: {e}")

if __name__ == "__main__":
    main()
