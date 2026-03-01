import os
import sys
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

sys.stdout.reconfigure(encoding="utf-8")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    # --- 【採用】アンチ・ボット検知オプション ---
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # --- 【採用】navigator.webdriver の隠蔽 ---
    driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
    """)
    return driver

def safe_screenshot(driver, name):
    if os.environ.get("GITHUB_ACTIONS") != "true":
        driver.save_screenshot(name)

def main():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")

    if not JKK_ID or not JKK_PASSWORD:
        log("❌ ID/PW未設定")
        sys.exit(1)

    driver = create_driver()
    wait = WebDriverWait(driver, 20)

    try:
        # 手順1: 公式トップ（セッション開始）
        log("🚪 手順1: 公式トップへアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        time.sleep(3)

        # 手順2: ブリッジ遷移（物理クリックのシミュレート）
        log("🌉 手順2: ブリッジ遷移実行（Referer確立）")
        bridge_script = """
            let a = document.createElement('a');
            a.id = 'bridge_link';
            a.href = 'https://jhomes.to-kousya.or.jp/search/jkknet/pc/';
            a.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;z-index:9999;opacity:0.01;';
            document.body.appendChild(a);
        """
        driver.execute_script(bridge_script)
        driver.find_element(By.ID, "bridge_link").click()

        # 手順3: 同一タブ・ハイジャック（別窓を阻止しセッションを維持）
        log("🔑 手順3: 同一タブでログイン画面を強制展開（ポップアップ阻止）")
        hijack_script = """
            window.open = function(url) { window.location.href = url; };
            if(typeof mypageLogin === 'function') { mypageLogin(); }
        """
        driver.execute_script(hijack_script)
        
        # URLの切り替わりを待機
        time.sleep(7)

        # 手順4: ログインフォーム入力（安全なsend_keys方式）
        log("⌨️ 手順4: ログイン情報の安全な投入")
        
        def try_fill(d):
            try:
                u = d.find_element(By.NAME, "uid")
                p = d.find_element(By.NAME, "passwd")
                u.clear()
                u.send_keys(JKK_ID)
                p.clear()
                p.send_keys(JKK_PASSWORD)
                p.submit()
                return True
            except:
                return False

        if not try_fill(driver):
            log("📦 フレーム内を探索します")
            frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
            for frame in frames:
                driver.switch_to.frame(frame)
                if try_fill(driver):
                    log("🎯 フレーム内で入力成功")
                    break
                driver.switch_to.default_content()

        # 手順5: 成功判定
        log("🚀 最終判定中...")
        wait.until(EC.any_of(EC.url_contains("mypage"), EC.url_contains("menu")))
        
        log(f"📍 最終URL: {driver.current_url}")
        if "mypage" in driver.current_url or "menu" in driver.current_url:
            log("🎉 ついに突破！ボット検知を出し抜きました！")
            if DISCORD_WEBHOOK:
                requests.post(DISCORD_WEBHOOK, json={"content": "✅ **JKKログイン完全突破！**\nボット隠蔽設定 ＋ 同一タブ戦略の合わせ技で勝利しました。"})
        else:
            log(f"💀 失敗。タイトル: {driver.title}")
            safe_screenshot(driver, "fail.png")

    except Exception as e:
        log(f"❌ エラー: {e}")
        safe_screenshot(driver, "error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
