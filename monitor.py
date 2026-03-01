import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
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
        log("🚪 手順1: サイトへアクセス")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        time.sleep(10)

        # 全ウィンドウをループしてログイン画面を探す
        login_done = False
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            # iframe内も含めて入力欄を探す
            frames = [None] + driver.find_elements(By.TAG_NAME, "iframe")
            for f in frames:
                try:
                    if f: driver.switch_to.frame(f)
                    inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='password'], input[type='tel']")
                    if len(inputs) >= 2:
                        log(f"⌨️ ログイン情報を入力します (Window: {handle})")
                        driver.execute_script("arguments[0].value = arguments[1];", inputs[0], JKK_ID)
                        driver.execute_script("arguments[0].value = arguments[1];", inputs[1], JKK_PASSWORD)
                        # 送信 (Enterキー)
                        inputs[1].send_keys('\n')
                        login_done = True; break
                except: continue
                driver.switch_to.default_content()
            if login_done: break

        log("⏳ マイページのロードを待ちます (30秒)")
        time.sleep(30)

        # --- 第1ゴール: 「条件から検索」ボタンを全探索 ---
        log("🔍 第1ゴール: 「条件から検索」ボタンを全ウィンドウ・全フレームから探します")
        found_btn = False
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            frames = [None] + driver.find_elements(By.TAG_NAME, "iframe")
            for f in frames:
                try:
                    if f: driver.switch_to.frame(f)
                    # 画像のsrcに 'btn_search_cond' を含むリンクを探す
                    btns = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_search_cond')]/parent::a")
                    if btns:
                        log("🎯 ボタン発見！クリックして第1ゴールを突破します")
                        driver.execute_script("arguments[0].click();", btns[0])
                        found_btn = True; break
                except: continue
                driver.switch_to.default_content()
            if found_btn: break

        if found_btn:
            time.sleep(10)
            driver.save_screenshot("goal_1_success.png")
            log("✨ 第1ゴール突破！！ 世田谷区が選べる画面を表示させました")
        else:
            driver.save_screenshot("goal_1_failed_debug.png")
            log("❌ 第1ゴール失敗。画面が見つかりません")

    except Exception as e:
        log(f"⚠️ エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
