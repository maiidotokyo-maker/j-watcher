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
import requests

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def send_discord(message):
    if not DISCORD_WEBHOOK_URL: return
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message}).raise_for_status()
    except: pass

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
        
        # 1. ログイン窓へ移動
        WebDriverWait(driver, 20).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        
        # 2. 強制注入
        log("⌨️ ID/PW注入...")
        current_handles = set(driver.window_handles)
        bomb_script = """
        function inject(doc) {
            var u = doc.getElementsByName('user_id')[0];
            var p = doc.getElementsByName('password')[0];
            if(u && p) {
                u.value = arguments[0];
                p.value = arguments[1];
                doc.defaultView.submitNext();
                return true;
            }
            return false;
        }
        inject(document);
        var fs = document.getElementsByTagName('iframe');
        for(var i=0; i<fs.length; i++) { try { inject(fs[i].contentDocument); } catch(e) {} }
        """
        driver.execute_script(bomb_script, JKK_ID, JKK_PASSWORD)

        # 3. 【重要】ログイン後に開く「真のマイページ窓」を捕まえる
        log("⏳ マイページへの遷移を監視...")
        target_handle = None
        for _ in range(20):
            new_handles = set(driver.window_handles) - current_handles
            if new_handles:
                target_handle = list(new_handles)[0]
                driver.switch_to.window(target_handle)
                break
            time.sleep(2)
        
        # 4. 真っ白画面対策：リフレッシュ
        log("🔄 画面描画を強制リフレッシュ...")
        time.sleep(5)
        driver.refresh()
        time.sleep(5)

        # 5. 第1ゴール：条件から検索ボタンをクリック
        log("🔍 「条件から検索」を探索...")
        found = False
        driver.switch_to.default_content()
        frames = [None] + driver.find_elements(By.TAG_NAME, "iframe")
        for f in frames:
            try:
                if f: driver.switch_to.frame(f)
                btn = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_search_cond')]/parent::a")
                if btn:
                    driver.execute_script("arguments[0].click();", btn[0])
                    found = True; break
            except: continue
            driver.switch_to.default_content()

        if found:
            time.sleep(5)
            driver.save_screenshot("goal_1_success.png")
            log("✨ 第1ゴール突破！世田谷区の選択画面へ到達しました。")
            send_discord("✅ 第1ゴール突破！世田谷区の選択画面に到達しました。")
        else:
            driver.save_screenshot("failed_at_goal_1.png")
            log("❌ 第1ゴール失敗。画面がまだ読み込まれていない可能性があります。")

    except Exception as e:
        log(f"⚠️ エラー: {e}")
        driver.save_screenshot("final_error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
