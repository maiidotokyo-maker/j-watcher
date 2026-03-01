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
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20) # 最大20秒待つが、見つかれば即実行
    
    try:
        log("🚪 ログイン開始")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        
        # 1. ログイン窓へ即座に切り替え
        wait.until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])

        # 2. iframeの中身が出るまで待機してスイッチ（ここが最重要）
        log("⏳ フォーム読み込み待機...")
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, "iframe")))
        
        # 3. 入力欄が見えた瞬間に値をセット
        user_field = wait.until(EC.element_to_be_clickable((By.NAME, "user_id")))
        pass_field = driver.find_element(By.NAME, "password")
        
        log("⌨️ ID/PW入力")
        user_field.send_keys(JKK_ID)
        pass_field.send_keys(JKK_PASSWORD)
        
        # 4. ログインボタンをクリック
        login_btn = driver.find_element(By.XPATH, "//a[contains(@onclick, 'submitNext')]")
        driver.execute_script("arguments[0].click();", login_btn)
        log("🚀 ログイン実行")

        # 5. ログイン後の遷移確認（ここは数秒待ちます）
        time.sleep(5)
        driver.switch_to.default_content()
        driver.save_screenshot("quick_check.png")
        log("📸 『quick_check.png』を確認してください。")

    except Exception as e:
        log(f"⚠️ エラー: {e}")
        driver.save_screenshot("error_shot.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
