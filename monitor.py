import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
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
    
    try:
        log("🚪 手順1: ログインページへアクセス")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        
        # 最初のウィンドウ切り替え
        WebDriverWait(driver, 20).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(5)

        log("⌨️ 手順2: ログイン入力")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        fields = [i for i in inputs if i.is_displayed() and i.get_attribute("type") in ["text", "password", "tel"]]
        
        if len(fields) >= 2:
            driver.execute_script("arguments[0].value = arguments[1];", fields[0], JKK_ID)
            driver.execute_script("arguments[0].value = arguments[1];", fields[1], JKK_PASSWORD)
            log("✅ 入力完了。ボタンをクリックします...")
            
            try:
                login_btn = driver.find_element(By.XPATH, "//img[contains(@src, 'btn_login')]/parent::a")
                driver.execute_script("arguments[0].click();", login_btn)
            except Exception as e:
                log(f"⚠️ クリック時にエラーが出ましたが続行します: {e}")

        # ログイン後のマイページが表示されるまで、最大40秒じっくり待ちます
        log("⏳ マイページの出現を待機中（40秒）...")
        start_time = time.time()
        found_search_btn = False

        while time.time() - start_time < 40:
            # 全ウィンドウをチェック
            for handle in driver.window_handles:
                driver.switch_to.window(handle)
                # iframe内を含めて「条件から検索」ボタンを探す
                driver.switch_to.default_content()
                frames = driver.find_elements(By.TAG_NAME, "iframe")
                
                # 親フレームをまず確認
                if driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_search_cond')]"):
                    found_search_btn = True; break
                
                # iframe内を確認
                for i in range(len(frames)):
                    try:
                        driver.switch_to.default_content()
                        driver.switch_to.frame(i)
                        if driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_search_cond')]"):
                            found_search_btn = True; break
                    except: continue
                if found_search_btn: break
            
            if found_search_btn:
                log("🎯 第1ゴール直前：マイページと「条件から検索」ボタンを確認しました！")
                search_btn = driver.find_element(By.XPATH, "//img[contains(@src, 'btn_search_cond')]/parent::a")
                driver.execute_script("arguments[0].click();", search_btn)
                break
            time.sleep(5)

        if found_search_btn:
            time.sleep(10)
            driver.save_screenshot("goal_1_success.png")
            log("✨ 第1ゴール突破！検索条件（世田谷区選択）画面に到達しました。")
        else:
            driver.save_screenshot("goal_1_failed_debug.png")
            log("❌ 第1ゴール失敗。マイページに辿り着けませんでした。")

    except Exception as e:
        log(f"❌ 重大なエラー: {e}")
        driver.save_screenshot("fatal_error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
