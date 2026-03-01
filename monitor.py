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

        log("⌨️ 手順2: ログイン入力 & ボタンクリック")
        # 入力欄を埋める
        inputs = driver.find_elements(By.TAG_NAME, "input")
        fields = [i for i in inputs if i.is_displayed() and i.get_attribute("type") in ["text", "password", "tel"]]
        if len(fields) >= 2:
            driver.execute_script("arguments[0].value = arguments[1];", fields[0], JKK_ID)
            driver.execute_script("arguments[0].value = arguments[1];", fields[1], JKK_PASSWORD)
            log("✅ 入力完了")
            
            # 青いログインボタンを画像名で特定してクリック
            login_imgs = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_login')]")
            if login_imgs:
                driver.execute_script("arguments[0].click();", login_imgs[0])
                log("🚀 ログインボタンをクリックしました")
            else:
                # 画像で見つからない場合は親のリンクを探す
                driver.execute_script("submitNext();")
        
        log("⏳ 遷移待ち（25秒）... ここでマイページが開くのをじっくり待ちます")
        time.sleep(25)
        
        # マイページが別ウィンドウで開く場合があるため、再度ハンドルを確認
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            log("🔄 最新ウィンドウに切り替えました")

        # --- ゴール1: 「条件から検索」をクリック ---
        log("🔍 ゴール1: 「条件から検索」ボタンを探索中")
        
        def try_click_search_btn():
            driver.switch_to.default_content()
            # 1. 直接探す
            btns = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_search_cond')]/parent::a")
            if btns:
                driver.execute_script("arguments[0].click();", btns[0])
                return True
            # 2. iframe内を探す
            frames = driver.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(frames)):
                try:
                    driver.switch_to.default_content()
                    driver.switch_to.frame(i)
                    btns = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_search_cond')]/parent::a")
                    if btns:
                        log(f"🎯 iframe[{i}] 内でボタンを発見")
                        driver.execute_script("arguments[0].click();", btns[0])
                        return True
                except: continue
            return False

        if try_click_search_btn():
            time.sleep(10)
            driver.save_screenshot("goal_1_success.png")
            log("✨ 第1ゴール突破！「世田谷区」を選択する画面に到達しました")
        else:
            driver.save_screenshot("goal_1_failed_final_check.png")
            log("❌ 第1ゴール失敗。画面の状態を確認してください")

    except Exception as e:
        log(f"⚠️ エラー: {e}")
        driver.save_screenshot("fatal_debug.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
