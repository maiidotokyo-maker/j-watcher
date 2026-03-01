import os
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

JKK_ID = os.environ.get("JKK_ID")
JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def send_discord(message, file_path=None):
    if not DISCORD_WEBHOOK_URL: return
    try:
        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as f:
                requests.post(DISCORD_WEBHOOK_URL, data={"content": message}, files={"file": f})
        else:
            requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
    except: pass

def main():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 30)
    
    try:
        log("🚪 サイトアクセス")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        
        wait.until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        log("🪟 ログイン窓捕捉")

        # 1. 全フレームをしらみつぶしに探す (トリプル・アタック)
        log("🕵️ 入力エリアを探索開始...")
        time.sleep(5) # 描画安定待ち
        
        found = False
        # 全てのiframeをリストアップ
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        for f in frames:
            driver.switch_to.frame(f)
            # さらに中のフレームも探す
            sub_frames = driver.find_elements(By.TAG_NAME, "iframe")
            targets = [driver]
            for sf in sub_frames:
                driver.switch_to.frame(sf)
                targets.append(driver)

            for t in targets:
                # 名前、ID、CSSセレクタの順で試行
                u_selectors = [ (By.NAME, "user_id"), (By.ID, "user_id"), (By.CSS_SELECTOR, "input[type='text']") ]
                for sel_type, sel_val in u_selectors:
                    try:
                        u = t.find_elements(sel_type, sel_val)
                        if u and u[0].is_displayed():
                            log(f"🎯 発見: {sel_val}")
                            u[0].clear()
                            u[0].send_keys(JKK_ID)
                            p = t.find_element(By.NAME, "password")
                            p.clear()
                            p.send_keys(JKK_PASSWORD)
                            # 送信
                            btn = t.find_element(By.XPATH, "//a[contains(@onclick, 'submitNext')]")
                            driver.execute_script("arguments[0].click();", btn)
                            found = True
                            break
                    except: continue
                if found: break
            if found: break
            driver.switch_to.default_content()
            driver.switch_to.frame(f) # 親に戻る

        if found:
            log("🚀 送信成功。遷移待ち...")
            time.sleep(15)
            driver.switch_to.default_content()
            driver.save_screenshot("final_result.png")
            send_discord("✅ ログイン操作完了！結果を確認してください。", "final_result.png")
        else:
            raise Exception("入力欄を特定できませんでした。")

    except Exception as e:
        log(f"⚠️ エラー: {e}")
        driver.save_screenshot("last_error.png")
        send_discord(f"❌ エラー: {e}", "last_error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
