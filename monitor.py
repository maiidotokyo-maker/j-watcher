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
    
    try:
        log("🚪 手順1: ログイン開始")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        
        # ウィンドウ切り替え待ち
        WebDriverWait(driver, 20).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(5)

        # ログイン入力
        inputs = driver.find_elements(By.TAG_NAME, "input")
        text_fields = [i for i in inputs if i.is_displayed() and i.get_attribute("type") in ["text", "password", "tel"]]
        if len(text_fields) >= 2:
            driver.execute_script("arguments[0].value = arguments[1];", text_fields[0], JKK_ID)
            driver.execute_script("arguments[0].value = arguments[1];", text_fields[1], JKK_PASSWORD)
            log("⌨️ ID/PW入力完了")
            # ログインボタンクリック
            login_btn = driver.find_element(By.XPATH, "//a[contains(@onclick, 'submitNext')] | //img[contains(@src, 'btn_login')]/parent::a")
            driver.execute_script("arguments[0].click();", login_btn)

        log("🚀 ログイン送信。マイページ読み込みをじっくり待ちます...")
        # ここで焦らず、マイページ特有の要素が出るまで最大30秒待機
        time.sleep(20) 
        
        # --- 次のゴール: 「条件から検索」をクリック ---
        log("🔍 ゴール1: 「条件から検索」ボタンを探します")
        driver.switch_to.default_content()
        
        search_btn = None
        # マイページ内のiframeをくまなく探す
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        for i in range(len(frames)):
            try:
                driver.switch_to.frame(i)
                # ピンクのボタンを探す
                btns = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_search_cond')]/parent::a")
                if btns:
                    search_btn = btns[0]
                    log(f"🎯 発見！frame[{i}] 内の「条件から検索」をクリックします")
                    driver.execute_script("arguments[0].click();", search_btn)
                    break
                driver.switch_to.default_content()
            except:
                driver.switch_to.default_content()
                continue

        if search_btn:
            time.sleep(10)
            driver.save_screenshot("goal_1_success.png")
            log("✨ 第1ゴール突破！検索条件入力画面（世田谷区の選択肢があるはず）に到達しました")
        else:
            driver.save_screenshot("goal_1_failed.png")
            log("❌ 第1ゴール失敗。ボタンが見つかりませんでした")

    except Exception as e:
        log(f"⚠️ エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
