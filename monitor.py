import os
import sys
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

def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # ポップアップブロックを無効化
    options.add_argument("--disable-popup-blocking")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def main():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    
    driver = create_driver()
    
    try:
        log("🚪 手順1: ログイン開始ページへアクセス")
        # 直接このURLにアクセスすると window.open が走る
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        
        # 🚨 重要：新しいウィンドウが開くのを待機
        log("⏳ 新しいウィンドウの生成を待機中...")
        wait = WebDriverWait(driver, 20)
        wait.until(lambda d: len(d.window_handles) > 1)
        
        # 新しいウィンドウに切り替え
        new_window = driver.window_handles[-1]
        driver.switch_to.window(new_window)
        log("🔄 新しいウィンドウに操作を切り替えました")
        
        # JSがフォームを生成するのを待つ
        time.sleep(10)
        driver.save_screenshot("debug_new_window.png")

        # 手順3: ログインフォーム探索（iframe内）
        log("⌨️ 手順3: ログインフォームを探索")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        
        for frame in frames:
            driver.switch_to.frame(frame)
            try:
                u_field = driver.find_element(By.NAME, "uid")
                p_field = driver.find_element(By.NAME, "passwd")
                
                log("✅ フォーム発見。入力します。")
                u_field.send_keys(JKK_ID)
                p_field.send_keys(JKK_PASSWORD)
                driver.save_screenshot("debug_submitting.png")
                p_field.submit()
                
                # ログイン完了待機
                time.sleep(10)
                log(f"結果URL: {driver.current_url}")
                driver.save_screenshot("debug_final.png")
                break
            except:
                driver.switch_to.default_content()

    except Exception as e:
        log(f"❌ エラー: {e}")
        driver.save_screenshot("error_capture.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
