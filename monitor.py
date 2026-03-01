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
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        log("🚪 手順1: ログインページへアクセス")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        
        # ログイン画面のウィンドウへ切り替え
        WebDriverWait(driver, 25).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(7)

        log("⌨️ 手順2: ログイン実行 (iframe 潜入開始)")
        
        # ログイン入力欄とボタンを探す関数
        def do_login():
            inputs = driver.find_elements(By.TAG_NAME, "input")
            fields = [i for i in inputs if i.is_displayed() and i.get_attribute("type") in ["text", "password", "tel"]]
            if len(fields) >= 2:
                driver.execute_script("arguments[0].value = arguments[1];", fields[0], JKK_ID)
                driver.execute_script("arguments[0].value = arguments[1];", fields[1], JKK_PASSWORD)
                # ログインボタン(imgの親のaタグ)をクリック
                login_btn = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_login')]/parent::a")
                if login_btn:
                    driver.execute_script("arguments[0].click();", login_btn[0])
                    return True
            return False

        # iframeを1つずつチェック
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        login_success = False
        for i in range(len(frames)):
            driver.switch_to.default_content()
            driver.switch_to.frame(i)
            if do_login():
                log(f"✅ iframe[{i}] 内でログイン情報を入力・送信しました")
                login_success = True
                break
        
        if not login_success:
            driver.save_screenshot("login_failed_no_frame.png")
            raise Exception("ログインフォームが見つかりませんでした")

        log("⏳ マイページの読み込みを待機（35秒）...")
        time.sleep(35)
        
        # ログイン後にさらに新ウィンドウが開く場合があるため、最新へ
        driver.switch_to.window(driver.window_handles[-1])

        # --- 第1ゴール: 「条件から検索」をクリック ---
        log("🔍 第1ゴール: 「条件から検索」ボタンを探索中")
        
        found_search_cond = False
        # マイページもiframe構造のため、全フレームを再走査
        for _ in range(3): # 読み込みを考慮して3回リトライ
            driver.switch_to.default_content()
            all_frames = driver.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(all_frames)):
                try:
                    driver.switch_to.default_content()
                    driver.switch_to.frame(i)
                    # ピンク色の「条件から検索」ボタンを特定
                    btns = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_search_cond')]/parent::a")
                    if btns:
                        log(f"🎯 発見！iframe[{i}] 内の「条件から検索」をクリック")
                        driver.execute_script("arguments[0].click();", btns[0])
                        found_search_cond = True
                        break
                except: continue
            if found_search_cond: break
            time.sleep(5)

        if found_search_cond:
            time.sleep(10)
            driver.save_screenshot("goal_1_success.png")
            log("✨ 第1ゴール突破！「世田谷区」を選択する画面へ進みました")
        else:
            driver.save_screenshot("goal_1_failed_final.png")
            log("❌ 第1ゴール失敗。マイページの中身が取得できませんでした")

    except Exception as e:
        log(f"⚠️ エラー発生: {e}")
        driver.save_screenshot("fatal_error_log.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
