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
        
        # ログイン画面のウィンドウへ切り替え
        WebDriverWait(driver, 20).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(5)

        log("⌨️ 手順2: ログイン情報入力")
        # 直接ID/PWを入力して、サイトの submitNext 関数を実行する
        driver.execute_script(f"""
            var inputs = document.querySelectorAll('input[type="text"], input[type="password"], input[type="tel"]');
            if(inputs.length >= 2){{
                inputs[0].value = '{JKK_ID}';
                inputs[1].value = '{JKK_PASSWORD}';
                submitNext(); // サイト独自の関数を呼び出す
            }}
        """)
        log("🚀 ログイン処理(submitNext)を実行しました")

        # ログイン後にさらに新しいウィンドウが開く可能性があるため、ハンドルを確認
        log("⏳ マイページの展開を待機中...")
        time.sleep(15)
        
        # 最新のウィンドウに切り替え
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            log("🔄 最新のウィンドウ（マイページ）に切り替えました")

        # --- ゴール1: 「条件から検索」ボタンを探す ---
        log("🔍 ゴール1: 「条件から検索」ボタンを探索中")
        
        def find_and_click_search_btn():
            # 親フレームと全iframeをチェック
            driver.switch_to.default_content()
            # まずは直下を探す
            btns = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_search_cond')]/parent::a")
            if btns:
                driver.execute_script("arguments[0].click();", btns[0])
                return True
            
            # iframe内を探す
            frames = driver.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(frames)):
                try:
                    driver.switch_to.default_content()
                    driver.switch_to.frame(i)
                    btns = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_search_cond')]/parent::a")
                    if btns:
                        log(f"🎯 iframe[{i}] 内でボタンを発見しクリックしました")
                        driver.execute_script("arguments[0].click();", btns[0])
                        return True
                except: continue
            return False

        if find_and_click_search_btn():
            time.sleep(10)
            driver.save_screenshot("goal_1_success.png")
            log("✨ 第1ゴール突破！検索条件（世田谷区選択）画面へ到達しました")
        else:
            driver.save_screenshot("goal_1_failed_check.png")
            log("❌ 第1ゴール失敗。マイページ内のボタンが見つかりません")

    except Exception as e:
        log(f"⚠️ エラー: {e}")
        driver.save_screenshot("error_detail.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
