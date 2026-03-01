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
        
        # 1. ログイン窓特定
        WebDriverWait(driver, 30).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        
        # 2. iframeに入って、物理的に入力
        log("⌨️ ID/PWを入力中...")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, "iframe")))
        
        user_field = wait.until(EC.element_to_be_clickable((By.NAME, "user_id")))
        pass_field = driver.find_element(By.NAME, "password")
        
        user_field.clear()
        user_field.send_keys(JKK_ID)
        pass_field.clear()
        pass_field.send_keys(JKK_PASSWORD)
        
        # 3. 物理クリックによる送信
        log("🚀 ログインボタンを物理クリックします")
        current_handles = set(driver.window_handles)
        login_btn = driver.find_element(By.XPATH, "//a[contains(@onclick, 'submitNext')]")
        driver.execute_script("arguments[0].click();", login_btn)

        # 4. ログイン後の新ウィンドウを捕まえる
        log("⏳ マイページ出現を待機...")
        target_handle = None
        for _ in range(20):
            new_handles = set(driver.window_handles) - current_handles
            if new_handles:
                target_handle = list(new_handles)[0]
                driver.switch_to.window(target_handle)
                log("🔄 新ウィンドウに移動しました")
                break
            time.sleep(2)
        
        # 重要：真っ白画面対策として30秒間じっくり待機
        log("⏳ 描画が安定するまで30秒待機します（リフレッシュなし）...")
        time.sleep(30)

        # 5. 第1ゴール：条件から検索ボタンを探索
        log("🔍 「条件から検索」を探索...")
        found = False
        # マイページもiframe構造の可能性があるため全探索
        driver.switch_to.default_content()
        frames = [None] + driver.find_elements(By.TAG_NAME, "iframe")
        for f in frames:
            try:
                if f: driver.switch_to.frame(f)
                btn = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_search_cond')]/parent::a")
                if btn:
                    log("🎯 ボタン発見！クリックします")
                    driver.execute_script("arguments[0].click();", btn[0])
                    found = True; break
            except: continue
            driver.switch_to.default_content()

        if found:
            time.sleep(10)
            driver.save_screenshot("goal_1_success.png")
            log("✨ 第1ゴール突破！世田谷区の選択画面へ到達しました。")
        else:
            driver.save_screenshot("debug_mypage.png")
            log(f"❌ 失敗。現在のURL: {driver.current_url}")

    except Exception as e:
        log(f"⚠️ エラー: {e}")
        driver.save_screenshot("final_error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
