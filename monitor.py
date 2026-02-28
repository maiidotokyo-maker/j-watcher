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
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

def find_and_click_login_recursive(driver):
    """全フレームを巡回して、物理的なログインボタンを探してクリックする"""
    # 探索対象のセレクタ（優先度順）
    selectors = [
        "//area[contains(@onclick, 'mypageLogin')]",
        "//a[contains(@onclick, 'mypageLogin')]",
        "//img[contains(@alt, 'ログイン')]",
        "//button[contains(text(), 'ログイン')]"
    ]
    
    for sel in selectors:
        try:
            btns = driver.find_elements(By.XPATH, sel)
            for btn in btns:
                if btn.is_displayed():
                    log(f"🎯 ボタン発見: {sel}")
                    # 人間らしくマウス移動してクリック
                    actions = ActionChains(driver)
                    actions.move_to_element(btn).pause(random.uniform(0.5, 1.2)).click().perform()
                    return True
        except:
            continue

    # 子フレームを再帰探索
    frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
    for i in range(len(frames)):
        try:
            driver.switch_to.frame(i)
            if find_and_click_login_recursive(driver):
                return True
            driver.switch_to.parent_frame()
        except:
            driver.switch_to.parent_frame()
    return False

def main():
    driver = None
    try:
        driver = setup_driver()
        log(f"🏁 玄関ページへアクセス: {START_URL}")
        driver.get(START_URL)
        time.sleep(random.uniform(6, 10))

        log("🖱️ ログインボタンをフレーム内から探索中...")
        if not find_and_click_login_recursive(driver):
            log("❌ ボタンがどこにも見つかりませんでした。")
            driver.save_screenshot("button_not_found.png")
            return

        log("⏳ 遷移待ち...")
        time.sleep(15)
        log(f"DEBUG: URL={driver.current_url} Title={driver.title}")

        if "おわび" in driver.title:
            log("🚨 物理クリックしたのにおわび画面です。CookieまたはIPの制約が極めて強いです。")
            return

        # ここから先、ID/PASS入力（以前の完成ロジックへ続く）
        # ... (略) ...
        
    except Exception as e:
        log(f"❌ エラー: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
