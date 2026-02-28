import sys
import os
import time
import random
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
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
    options.add_argument('--window-size=1920,1080')
    # Bot検知回避の徹底
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

def physical_click(driver, element):
    """要素の真上までマウスを動かしてクリックする擬態"""
    try:
        actions = ActionChains(driver)
        actions.move_to_element(element)
        actions.pause(random.uniform(0.5, 1.0))
        actions.click()
        actions.perform()
        return True
    except:
        return False

def find_login_button_and_click(driver):
    """玄関ページでログインボタンを物理的に探して押す"""
    # 複数の候補（画像、リンク、エリアタグ）を探索
    selectors = [
        "//area[contains(@onclick, 'mypageLogin')]",
        "//a[contains(@onclick, 'mypageLogin')]",
        "//img[contains(@alt, 'ログイン')]",
        "//a[contains(text(), 'ログイン')]"
    ]
    for sel in selectors:
        btns = driver.find_elements(By.XPATH, sel)
        if btns and btns[0].is_displayed():
            log(f"🎯 ボタン発見 ({sel})。クリックします...")
            return physical_click(driver, btns[0])
    return False

def main():
    driver = None
    try:
        driver = setup_driver()
        log("🏁 玄関ページへアクセス...")
        driver.get(START_URL)
        time.sleep(random.uniform(5, 8))

        # 1. 物理クリックを試みる
        if not find_login_button_and_click(driver):
            log("⚠️ ボタンが見つかりません。JS実行に切り替えます...")
            driver.execute_script("if(window.mypageLogin) mypageLogin();")
        
        # 2. 遷移待ち（ここでおわびが出ないかチェック）
        time.sleep(15)
        log(f"DEBUG: URL={driver.current_url} Title={driver.title}")

        if "おわび" in driver.title:
            log("🚨 おわび画面。最後の悪あがき：リロードを試行...")
            driver.refresh()
            time.sleep(10)

        # 3. 以降、フレーム内探索（既存ロジック）
        # (ここから先はログインフォームを探すコードを繋げる)
        # ※ 長くなるため、まずこの「おわび回避」が通るか確認しましょう

    except Exception as e:
        log(f"❌ エラー: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
