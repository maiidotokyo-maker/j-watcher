import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def main():
    # 1. 準備 (GitHub Secrets)
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 5) # 待機は必要最小限の5秒設定（見つかれば即実行）
    
    try:
        # 2. 直撃アクセス
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        
        # 3. ログイン窓へ瞬時に切り替え
        wait.until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        
        # 4. iframeへ入り、ID/PWを入力してEnter
        # 画面に出た瞬間に操作を開始します
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, "iframe")))
        
        user_el = wait.until(EC.visibility_of_element_located((By.NAME, "user_id")))
        user_el.send_keys(JKK_ID)
        driver.find_element(By.NAME, "password").send_keys(JKK_PASSWORD)
        
        # ログイン実行
        driver.execute_script("submitNext();")
        
        # 5. 結果を即座に保存して終了
        import time; time.sleep(3) # 遷移の時間だけ確保
        driver.switch_to.default_content()
        driver.save_screenshot("fast_login_result.png")
        print("Done.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
