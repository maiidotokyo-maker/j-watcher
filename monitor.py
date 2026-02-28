import sys
import os
import time
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

# JKKのレトロなURL構造に合わせた「初期化」用URL
# /pc/ ではなく、あえて index.jsp や直接のログイン窓口を狙う
ALT_START_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"

def setup_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # レトロサイトは画面サイズにうるさいので、あえて少し小さめの「当時の標準」にする
    options.add_argument('--window-size=1024,768')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def main():
    driver = None
    try:
        driver = setup_driver()
        
        # 玄関ページ（/pc/）を飛ばし、直接「ログインセッション開始」のURLへ
        log(f"⚡ レトロセッションを強制起動: {ALT_START_URL}")
        driver.get(ALT_START_URL)
        
        # ロードをじっくり待つ
        time.sleep(15) 

        log(f"DEBUG: 現在のURL: {driver.current_url}")
        log(f"DEBUG: ページタイトル: '{driver.title}'")

        if "おわび" in driver.title:
            log("🚨 まだ『おわび』です。URLに index.jsp を付与して再試行...")
            driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/index.jsp")
            time.sleep(10)

        # ログインフォーム（ID/PASS）があるか、全フレームを絨毯爆弾スキャン
        def scan_for_input(d):
            inputs = d.find_elements(By.TAG_NAME, "input")
            if any(i.get_attribute("type") == "password" for i in inputs):
                return True
            
            fms = d.find_elements(By.TAG_NAME, "frame") + d.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(fms)):
                try:
                    d.switch_to.frame(i)
                    if scan_for_input(d): return True
                    d.switch_to.parent_frame()
                except: continue
            return False

        if scan_for_input(driver):
            log("🎯 ついにログインフォーム（生身）を捉えました！")
            # ここで入力実行
        else:
            log("❌ フォームが見つかりません。現在のHTMLソース（冒頭）:")
            log(driver.page_source[:500])

    except Exception as e:
        log(f"❌ エラー: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
