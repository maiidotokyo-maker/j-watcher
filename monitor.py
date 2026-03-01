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
    # ポップアップとJSの実行を安定させる設定
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--enable-javascript")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        log("🚪 手順1: サイトへアクセス")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        
        # ログイン窓が開くのを待機
        WebDriverWait(driver, 20).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(5)

        # --- 手順2: ログイン実行 ---
        log("⌨️ ログイン情報をセット中...")
        current_handles = set(driver.window_handles)
        
        # iframeを巡回して入力
        frames = [None] + driver.find_elements(By.TAG_NAME, "iframe")
        for f in frames:
            try:
                if f: driver.switch_to.frame(f)
                inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='password'], input[type='tel']")
                if len(inputs) >= 2:
                    driver.execute_script("arguments[0].value = arguments[1];", inputs[0], JKK_ID)
                    driver.execute_script("arguments[0].value = arguments[1];", inputs[1], JKK_PASSWORD)
                    log("🚀 submitNext() を実行します")
                    driver.execute_script("submitNext();")
                    break
            except: continue
            driver.switch_to.default_content()

        # --- 重要：新しいマイページウィンドウを捕まえる ---
        log("⏳ 新しいウィンドウの生成を監視中...")
        target_handle = None
        for _ in range(30): # 最大60秒
            new_handles = set(driver.window_handles) - current_handles
            if new_handles:
                target_handle = list(new_handles)[0]
                driver.switch_to.window(target_handle)
                log("🔄 新ウィンドウを検知。フォーカスを移動しました")
                break
            time.sleep(2)

        # 真っ白な画面対策：ロードが完了するまで最大30秒待機
        log("⏳ マイページの内容が表示されるまで待機...")
        found_search_btn = False
        for _ in range(6):
            # 全フレームを再走査
            driver.switch_to.default_content()
            all_frames = [None] + driver.find_elements(By.TAG_NAME, "iframe")
            for f in all_frames:
                try:
                    if f: driver.switch_to.frame(f)
                    btns = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_search_cond')]/parent::a")
                    if btns:
                        log("🎯 「条件から検索」ボタンを発見！")
                        driver.execute_script("arguments[0].click();", btns[0])
                        found_search_btn = True; break
                except: continue
                driver.switch_to.default_content()
            
            if found_search_btn: break
            log("...まだ読み込み中（または空ページ）。5秒待機...")
            time.sleep(5)
            # 画面が真っ白なら一度だけリフレッシュを試みる
            if _ == 2 and not found_search_btn:
                log("🔄 画面が動かないため、リフレッシュを試みます")
                driver.refresh()

        if found_search_btn:
            time.sleep(10)
            driver.save_screenshot("goal_1_success.png")
            log("✨ 第1ゴール突破！！ 世田谷区が選べる画面に到達しました。")
        else:
            driver.save_screenshot("goal_1_failed_final_check.png")
            log(f"❌ 最終URL: {driver.current_url}")
            log("❌ 第1ゴール失敗。マイページの内容が取得できませんでした。")

    except Exception as e:
        log(f"⚠️ エラー: {e}")
    finally:
        driver.quit()
