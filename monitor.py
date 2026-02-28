import sys
import os
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

sys.stdout.reconfigure(encoding='utf-8')
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def notify_discord(message):
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if url:
        try:
            requests.post(url, json={"content": message}, timeout=10)
            log("📢 Discord通知を送信しました。")
        except:
            pass

def main():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # 手順1: 公式サイトから入りセッションを確立
        log("🚪 手順1: 公社公式サイトへアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        time.sleep(3)

        # 手順2: ログイン画面を呼び出す
        log("🚪 手順2: ログインページへ遷移（JS実行）")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin")
        time.sleep(5)

        # 手順3: ID/PW入力
        log("⌨️ 手順3: IDとPWを入力します")
        
        # フレーム対応
        frames = driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
        if frames:
            driver.switch_to.frame(0)
            log("📦 フレーム内に切り替えました")

        u_field = driver.find_element(By.NAME, "uid")
        p_field = driver.find_element(By.NAME, "passwd")
        
        u_field.clear()
        u_field.send_keys(os.environ.get("JKK_ID"))
        p_field.clear()
        p_field.send_keys(os.environ.get("JKK_PASSWORD"), Keys.ENTER)
        
        log("⏳ ログイン処理中（15秒待機）...")
        time.sleep(15)

        # 手順4: 成功判定（教えていただいたURLでチェック！）
        target_url = "https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu"
        current_url = driver.current_url
        
        log(f"📍 現在のURL: {current_url}")
        log(f"📄 現在のタイトル: {driver.title}")

        # デバッグ用HTML保存
        with open("after_login_attempt.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        if target_url in current_url or "マイページ" in driver.title:
            log("🎉 成功！指定のマイページURLに到達しました。")
            notify_discord(f"✅ JKKログイン成功！\nマイページに到達しました。\nURL: {current_url}")
        else:
            log("💀 失敗。マイページにリダイレクトされませんでした。")
            driver.save_screenshot("login_failed_final.png")
            # 「おわび」が出ているか確認
            if "おわび" in driver.title:
                log("⚠️ サーバー混雑（おわび画面）により弾かれました。")

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        driver.save_screenshot("fatal_error.png")
    finally:
        driver.quit()
        log("🏁 終了")

if __name__ == "__main__":
    main()
