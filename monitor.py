import sys
import os
import time
import random
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- ログ出力 ---
sys.stdout.reconfigure(encoding='utf-8')
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# --- 環境変数 ---
START_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/"
JKK_ID = os.environ.get("JKK_ID", "").strip()
JKK_PASS = os.environ.get("JKK_PASSWORD", "").strip()
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def setup_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,1024')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def main():
    driver = None
    try:
        driver = setup_driver()
        
        log(f"🏁 レトロな玄関口へアクセス: {START_URL}")
        driver.get(START_URL)
        
        # 【重要】レトロサイトは「待ち」が命。フレームが組み上がるのを待つ。
        time.sleep(12) 

        log(f"DEBUG: Title='{driver.title}'")

        # 「おわび」が出た場合、それは「トップページそのものがエラー」ではなく
        # 「フレームの読み込み順序」の問題である可能性があります。
        if "おわび" in driver.title:
            log("🚨 おわび画面ですが、強引にトップを再ロードしてCookieを定着させます...")
            driver.delete_all_cookies()
            driver.get(START_URL)
            time.sleep(10)

        log("🔎 全フレームを巡回して『ログイン』の文字を探します...")
        
        def find_login_in_frames(d):
            # 現在のフレーム内の全テキストを確認
            if "ログイン" in d.page_source or "mypageLogin" in d.page_source:
                return True
            # 子フレームへ
            fms = d.find_elements(By.TAG_NAME, "frame") + d.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(fms)):
                try:
                    d.switch_to.frame(i)
                    if find_login_in_frames(d): return True
                    d.switch_to.parent_frame()
                except: continue
            return False

        if find_login_in_frames(driver):
            log("✨ ついにログイン要素を捕捉しました！")
            # ここで入力処理へ
        else:
            log("❌ レトロな壁は厚かった... フレーム内にログインが見つかりません。")
            driver.save_screenshot("retro_debug.png")

    except Exception as e:
        log(f"❌ エラー: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
