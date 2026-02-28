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

START_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/"

def setup_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,1024')
    
    # 【最重要】レトロサイトが安心する「普通のブラウザ」設定
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    options.add_argument('--lang=ja-JP')
    
    # オートメーション検知を完全にOFF（レトロな監視に引っかからないため）
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # 物理的なブラウザに見せかける
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

def main():
    driver = None
    try:
        driver = setup_driver()
        
        # 1. まずは玄関ページを「ゆっくり」読み込む
        log("🚪 玄関ページにアクセスして、セッションを焼いています...")
        driver.get(START_URL)
        
        # レトロなサーバーが「よし、人間が来たな」と認識するまで待つ
        time.sleep(10)
        
        # 2. この時点でCookieが正しく焼けているか確認（デバッグ）
        all_cookies = driver.get_cookies()
        log(f"🍪 取得されたCookieの数: {len(all_cookies)}")
        
        # 3. トップにある「ログイン」というリンクを「テキスト」で探して物理的に踏む
        # これが「mypageLogin」へ直行するよりも安全な「正規ルート」です
        log("🖱️ ページ内のログインリンクを探索してクリックします...")
        try:
            # aタグ、areaタグ、imgタグの中から「ログイン」を探す
            login_el = driver.find_element(By.XPATH, "//*[contains(text(), 'ログイン') or contains(@alt, 'ログイン') or contains(@onclick, 'mypageLogin')]")
            driver.execute_script("arguments[0].click();", login_el)
            log("✅ ログインリンクをクリックしました。")
        except:
            log("⚠️ リンクが見つからないため、JS実行で遷移を試みます...")
            driver.execute_script("if(typeof mypageLogin === 'function'){ mypageLogin(); }")

        # 4. 遷移をじっくり待つ
        time.sleep(15) 

        log(f"DEBUG: 現在のURL: {driver.current_url}")
        log(f"DEBUG: ページタイトル: '{driver.title}'")

        if "おわび" in driver.title:
            log("🚨 まだ『おわび』です。ソースの冒頭を確認...")
            log(driver.page_source[:300])
        else:
            log("🎉 突破！ログインフォームを探します。")
            # ここでID/PASS入力へ

    except Exception as e:
        log(f"❌ エラー: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
