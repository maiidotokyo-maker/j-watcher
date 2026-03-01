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

        # --- 手順2: ログイン実行 (JS関数直接叩き) ---
        login_triggered = False
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            frames = [None] + driver.find_elements(By.TAG_NAME, "iframe")
            for f in frames:
                try:
                    if f: driver.switch_to.frame(f)
                    inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='password'], input[type='tel']")
                    if len(inputs) >= 2:
                        log(f"⌨️ ID/PWをセット中...")
                        driver.execute_script("arguments[0].value = arguments[1];", inputs[0], JKK_ID)
                        driver.execute_script("arguments[0].value = arguments[1];", inputs[1], JKK_PASSWORD)
                        
                        # 重要：サイト独自の submitNext() 関数を直接実行してログインを強行する
                        log("🚀 submitNext() を直接実行してログインします")
                        driver.execute_script("submitNext();")
                        login_triggered = True; break
                except: continue
                driver.switch_to.default_content()
            if login_triggered: break

        log("⏳ マイページ展開を待機 (40秒)...")
        time.sleep(40)

        # --- 第1ゴール: 「条件から検索」ボタンを全探索 ---
        log("🔍 第1ゴール: ボタンを探索中...")
        found_btn = False
        # ログイン後はウィンドウが増えるので、新しい順にチェック
        for handle in reversed(driver.window_handles):
            driver.switch_to.window(handle)
            frames = [None] + driver.find_elements(By.TAG_NAME, "iframe")
            for f in frames:
                try:
                    if f: driver.switch_to.frame(f)
                    # ピンク色の「条件から検索」ボタンを探す
                    btns = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_search_cond')]/parent::a")
                    if btns:
                        log("🎯 ボタン発見！第1ゴール突破のためクリックします")
                        driver.execute_script("arguments[0].click();", btns[0])
                        found_btn = True; break
                except: continue
                driver.switch_to.default_content()
            if found_btn: break

        if found_btn:
            time.sleep(10)
            driver.save_screenshot("goal_1_success.png")
            log("✨ 第1ゴール突破！！ 世田谷区が選べる画面に到着しました")
        else:
            driver.save_screenshot("goal_1_failed_final.png")
            log("❌ 第1ゴール失敗。マイページへの遷移が確認できません")

    except Exception as e:
        log(f"⚠️ エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
