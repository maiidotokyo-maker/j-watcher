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
    options.add_argument("--disable-popup-blocking")
    # 念のため自動操作フラグを隠蔽
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def main():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    
    driver = create_driver()
    wait = WebDriverWait(driver, 15)
    
    try:
        log("🚪 手順1: ログイン開始ページへアクセス")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        
        # ウィンドウ切り替え
        wait.until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        log("🔄 新しいウィンドウに切り替え完了")
        
        time.sleep(7) # 描画を待機
        
        log("⌨️ 手順3: ログインフォームを探索")
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        log(f"発見されたiframe数: {len(frames)}")

        found = False
        for i, frame in enumerate(frames):
            log(f"🔎 iframe[{i}] をチェック中...")
            driver.switch_to.frame(frame)
            
            try:
                # 戦略1: input要素をすべて取得して、type="text" と type="password" に流し込む
                inputs = driver.find_elements(By.TAG_NAME, "input")
                text_fields = [i for i in inputs if i.get_attribute("type") in ["text", "password"]]
                
                if len(text_fields) >= 2:
                    log(f"✅ iframe[{i}] 内に入力フィールドを発見しました。")
                    # JavaScriptで確実に値をセット
                    driver.execute_script("arguments[0].value = arguments[1];", text_fields[0], JKK_ID)
                    driver.execute_script("arguments[0].value = arguments[1];", text_fields[1], JKK_PASSWORD)
                    
                    driver.save_screenshot("debug_filling.png")
                    
                    # ログインボタン（青いボタン）を探してクリック
                    try:
                        login_btn = driver.find_element(By.XPATH, "//a[contains(@onclick, 'login') or .//img[contains(@src, 'btn_login')]]")
                        login_btn.click()
                    except:
                        text_fields[1].submit()
                        
                    found = True
                    break
            except Exception as e:
                log(f"   iframe[{i}] 内でエラー: {e}")
            
            driver.switch_to.default_content()

        if not found:
            raise Exception("ログインフォームの入力フィールドを特定できませんでした。")

        # 最終確認
        log("🚀 ログイン処理の完了を待機中...")
        time.sleep(10)
        driver.save_screenshot("debug_final_result.png")
        log(f"現在のURL: {driver.current_url}")

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        driver.save_screenshot("final_fatal_error.png")
    finally:
        driver.quit()
        log("🏁 プロセス終了")

if __name__ == "__main__":
    main()
