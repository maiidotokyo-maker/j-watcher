import sys
import os
import requests
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

BASE_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/"
# 中継URL
LOGIN_MIDDLE_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"

def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Referer": BASE_URL
    })

    try:
        log("🚪 玄関ページでセッション開始...")
        session.get(BASE_URL)
        log(f"Cookie確保: {session.cookies.get_dict()}")

        log("📑 中継ページ（mypageLogin）を解析...")
        res = session.get(LOGIN_MIDDLE_URL)
        
        # 【重要】レトロサイトの文字コード(Shift-JIS)を強制適用
        res.encoding = 'cp932' 
        
        # ソースの中に「本丸」のパスが隠れていないか探す
        # レトロサイトはよく action="XXXX.do" のような形式を使います
        html = res.text
        log(f"取得データサイズ: {len(html)} bytes")

        if "uid" in html or "password" in html:
            log("🎯 本物のフォームを発見！")
        else:
            log("🔎 フォームがまだ見つかりません。自動で『本丸URL』を推測します...")
            # JKKのパターン：mypageLogin の後ろにアクションが付くケース
            action_url = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin.do"
            log(f"🚀 本丸と思われるURLに直接アタック: {action_url}")
            
            res_final = session.get(action_url)
            res_final.encoding = 'cp932'
            
            if "利用者ID" in res_final.text or "uid" in res_final.text:
                log("✨ 本物のログイン画面（JSP/Servlet）に到達しました！")
                # ここで payload = {"uid": ..., "passwd": ...} を POST する準備が整います
            else:
                log("🚨 依然として本丸に辿り着けません。ソースの断片:")
                log(res_final.text[:500].replace('\n', ' '))

    except Exception as e:
        log(f"❌ エラー: {e}")

if __name__ == "__main__":
    main()
