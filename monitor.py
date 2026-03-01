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
        
        # ウィンドウ切り替え
        WebDriverWait(driver, 20).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(5)

        log("⌨️ 手順2: ログイン実行 (iframe 内部探索モード)")
        
        def try_login_in_frame():
            # ID/PW入力欄を探す
            inputs = driver.find_elements(By.TAG_NAME, "input")
            fields = [i for i in inputs if i.is_displayed() and i.get_attribute("type") in ["text", "password", "tel"]]
            if len(fields) >= 2:
                driver.execute_script("arguments[0].value = arguments[1];", fields[0], JKK_ID)
                driver.execute_script("arguments[0].value = arguments[1];", fields[1], JKK_PASSWORD)
                # ログインボタン(aタグまたはimg)を探してクリック
                btns = driver.find_elements(By.XPATH, "//a[contains(@onclick, 'submitNext')] | //img[contains(@src, 'btn_login')]/parent::a")
                if btns:
                    driver.execute_script("arguments[0].click();", btns[0])
                    return True
            return False

        # まず親フレームで試行
        if not try_login_in_frame():
            # 失敗したら全 iframe を巡回
            frames = driver.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(frames)):
                driver.switch_to.default_content()
                driver.switch_to.frame(i)
                if try_login_in_frame():
                    log(f"✅ iframe[{i}] 内でログインを実行しました")
                    break

        log("⏳ マイページの出現を待ちます（30秒）...")
        time.sleep(30)
        
        # ログイン後に別ウィンドウが開いたか再確認
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])

        # --- ゴール1: 「条件から検索」をクリック ---
        log("🔍 ゴール1: 「条件から検索」ボタンを探します")
        
        found_goal_1 = False
        # マイページも iframe 構造なので同様に探索
        for _ in range(2): # 読み込み待ちを含めて2回トライ
            driver.switch_to.default_content()
            frames = driver.find_elements(By.TAG_NAME, "iframe")
            
            # iframe内を探索
            for i in range(len(frames)):
                try:
                    driver.switch_to.default_content()
                    driver.switch_to.frame(i)
                    cond_btns = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_search_cond')]/parent::a")
                    if cond_btns:
                        log(f"🎯 発見！iframe[{i}] 内の「条件から検索」をクリック")
                        driver.execute_script("arguments[0].click();", cond_btns[0])
                        found_goal_1 = True
                        break
                except: continue
            if found_goal_1: break
            time.sleep(5)

        if found_goal_1:
            time.sleep(8)
            driver.save_screenshot("goal_1_success.png")
            log("✨ 第1ゴール突破！世田谷区を選択する画面に到達しました。")
        else:
            driver.save_screenshot("goal_1_failed_debug.png")
            log("❌ 第1ゴール失敗。マイページが見つかりません。")

    except Exception as e:
        log(f"⚠️ エラー: {e}")
    finally:
        driver.quit()
