import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def main():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # ポップアップブロックを無効化
    options.add_argument("--disable-popup-blocking")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        log("🚪 手順1: サイトへアクセス")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        
        # 最初のログイン窓が出るまで待機
        WebDriverWait(driver, 20).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(5)

        # --- 手順2: ログイン実行 ---
        log("⌨️ ID/PWをセット中...")
        found_form = False
        frames = [None] + driver.find_elements(By.TAG_NAME, "iframe")
        for f in frames:
            try:
                if f: driver.switch_to.frame(f)
                inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='password'], input[type='tel']")
                if len(inputs) >= 2:
                    driver.execute_script("arguments[0].value = arguments[1];", inputs[0], JKK_ID)
                    driver.execute_script("arguments[0].value = arguments[1];", inputs[1], JKK_PASSWORD)
                    
                    current_handles = set(driver.window_handles)
                    log("🚀 submitNext() を実行します")
                    driver.execute_script("submitNext();")
                    found_form = True; break
            except: continue
            driver.switch_to.default_content()

        # --- 重要：新しいウィンドウ（マイページ）が開くのを待つ ---
        log("⏳ マイページウィンドウの出現を待機中...")
        new_window_found = False
        for _ in range(20): # 最大40秒
            if len(driver.window_handles) > len(current_handles):
                new_window_found = True
                new_handle = (set(driver.window_handles) - current_handles).pop()
                driver.switch_to.window(new_handle)
                log("🔄 新しいマイページウィンドウに切り替えました")
                break
            time.sleep(2)

        log("⏳ コンテンツの読み込み待ち（15秒）...")
        time.sleep(15)

        # --- 第1ゴール: 「条件から検索」を探索 ---
        log("🔍 第1ゴール: 「条件から検索」ボタンを全フレーム探索")
        found_btn = False
        # マイページもiframe構造なので全走査
        frames = [None] + driver.find_elements(By.TAG_NAME, "iframe")
        for f in frames:
            try:
                if f: driver.switch_to.frame(f)
                btns = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_search_cond')]/parent::a")
                if btns:
                    log("🎯 ボタン発見！第1ゴールを突破します")
                    driver.execute_script("arguments[0].click();", btns[0])
                    found_btn = True; break
            except: continue
            driver.switch_to.default_content()

        if found_btn:
            time.sleep(10)
            driver.save_screenshot("goal_1_success.png")
            log("✨ 第1ゴール突破！！ 次は世田谷区の選択へ進みます")
        else:
            # 失敗時のデバッグ：今見ているウィンドウのURLとタイトルを出す
            log(f"❌ 失敗時のURL: {driver.current_url}")
            driver.save_screenshot("goal_1_failed_last_resort.png")
            log("❌ 第1ゴール失敗。ウィンドウ切り替えがうまくいっていない可能性があります")

    except Exception as e:
        log(f"⚠️ エラー: {e}")
    finally:
        driver.quit()
