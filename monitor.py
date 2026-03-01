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
        log("🚪 手順1: ログイン開始")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        
        # ウィンドウ切り替え
        WebDriverWait(driver, 20).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(5)

        log("⌨️ 手順2: ログイン情報入力")
        # フレームを意識せず、表示されている入力欄に値をセット
        def fill_and_login():
            inputs = driver.find_elements(By.TAG_NAME, "input")
            text_fields = [i for i in inputs if i.is_displayed() and i.get_attribute("type") in ["text", "password", "tel"]]
            if len(text_fields) >= 2:
                driver.execute_script("arguments[0].value = arguments[1];", text_fields[0], JKK_ID)
                driver.execute_script("arguments[0].value = arguments[1];", text_fields[1], JKK_PASSWORD)
                log("✅ ID/PWを入力しました")
                # ボタンを探すのではなく、フォームを直接送信
                driver.execute_script("document.forms[0].submit();")
                log("🚀 ログインフォームを送信しました")
                return True
            return False

        if not fill_and_login():
            # 見つからない場合はiframe内を探索
            frames = driver.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(frames)):
                driver.switch_to.frame(i)
                if fill_and_login(): break
                driver.switch_to.default_content()

        # ログイン後の遷移を待つ
        log("⏳ マイページの読み込みを待機中（20秒）...")
        time.sleep(20) 
        
        # --- ゴール1: 「条件から検索」をクリック ---
        log("🔍 ゴール1: 「条件から検索」ボタンを探索中")
        driver.switch_to.default_content()
        
        found = False
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        for i in range(len(frames)):
            try:
                driver.switch_to.default_content()
                driver.switch_to.frame(i)
                # 画像のsrc属性に 'btn_search_cond' を含むリンクをクリック
                btns = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_search_cond')]/parent::a")
                if btns:
                    log(f"🎯 発見！frame[{i}] 内の「条件から検索」をクリック")
                    driver.execute_script("arguments[0].click();", btns[0])
                    found = True
                    break
            except: continue

        if found:
            time.sleep(10)
            driver.save_screenshot("goal_1_success.png")
            log("✨ 第1ゴール突破！「世田谷区」を選択する画面へ遷移しました")
        else:
            driver.save_screenshot("goal_1_failed_debug.png")
            log("❌ 第1ゴール失敗。マイページが正しく表示されていない可能性があります")

    except Exception as e:
        log(f"⚠️ エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
