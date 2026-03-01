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
        log("🚪 手順1: ログインポータルへアクセス")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        
        # 別ウィンドウが開くのを最大30秒待機
        WebDriverWait(driver, 30).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        log("🔄 ログインウィンドウに切り替えました。読み込みを10秒待ちます...")
        time.sleep(10)

        # ログイン情報を入力する「まで」何度もリトライするループ
        login_executed = False
        for attempt in range(5):
            log(f"⌨️ 手順2: ログイン試行 {attempt+1}回目...")
            
            # 全てのiframeを巡回して「input」タグを探す
            driver.switch_to.default_content()
            frames = [None] + driver.find_elements(By.TAG_NAME, "iframe")
            
            for f in frames:
                try:
                    if f: driver.switch_to.frame(f)
                    inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='password'], input[type='tel']")
                    if len(inputs) >= 2:
                        inputs[0].clear()
                        inputs[0].send_keys(JKK_ID)
                        inputs[1].clear()
                        inputs[1].send_keys(JKK_PASSWORD)
                        log("✅ ID/PWを入力しました")
                        
                        # ボタンをクリック（画像、リンク、またはEnterキー）
                        login_btn = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_login')]/parent::a")
                        if login_btn:
                            driver.execute_script("arguments[0].click();", login_btn[0])
                        else:
                            inputs[1].send_keys('\n') # Enterキーで代用
                        
                        log("🚀 ログインボタンを押しました")
                        login_executed = True
                        break
                except: continue
                if not f: driver.switch_to.default_content()
            
            if login_executed: break
            time.sleep(5)

        log("⏳ マイページ（条件から検索ボタンがある画面）の出現を待ちます（35秒）")
        time.sleep(35)
        
        # 最新のウィンドウへ（マイページがさらに別枠で開く対策）
        driver.switch_to.window(driver.window_handles[-1])

        # --- 第1ゴール: 「条件から検索」をクリック ---
        log("🔍 第1ゴール: 「条件から検索」ボタンを探索中...")
        found_search = False
        
        # マイページもiframe地獄なので全探索
        driver.switch_to.default_content()
        all_frames = [None] + driver.find_elements(By.TAG_NAME, "iframe")
        for f in all_frames:
            try:
                if f: driver.switch_to.frame(f)
                btns = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_search_cond')]/parent::a")
                if btns:
                    log("🎯 発見！「条件から検索」をクリックします")
                    driver.execute_script("arguments[0].click();", btns[0])
                    found_search = True
                    break
            except: continue
            if not f: driver.switch_to.default_content()

        if found_search:
            time.sleep(10)
            driver.save_screenshot("goal_1_success.png")
            log("✨ 第1ゴール突破！！ 世田谷区が選べる画面に到着しました！")
        else:
            driver.save_screenshot("goal_1_failed_last.png")
            log("❌ 第1ゴール失敗。マイページが見つかりません。")

    except Exception as e:
        log(f"⚠️ エラー: {e}")
    finally:
        driver.quit()
