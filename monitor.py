import os
import sys
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
    
    # アンチ・ボット設定（これだけは「おわび」回避に必須なので残します）
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def main():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")

    driver = create_driver()
    wait = WebDriverWait(driver, 30) # CI環境の遅延を考慮して30秒

    try:
        # 手順1: 公式トップ
        log("🚪 手順1: 公式トップへアクセス")
        driver.get("https://www.to-kousya.or.jp/")

        # 手順2: JKKねっとリンクを物理クリック
        log("🌉 手順2: JKKねっとリンクを物理クリック")
        # 確実に「クリック可能」になるまで待つ（User案）
        jkk_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href,'jkk')]")))
        current_handles = len(driver.window_handles)
        jkk_link.click()

        # ウィンドウが増えるのを待って切替（User案）
        wait.until(lambda d: len(d.window_handles) > current_handles)
        driver.switch_to.window(driver.window_handles[-1])
        log(f"📑 JKKページ到達: {driver.title}")

        # 手順3: ログインリンクを物理クリック
        log("🔑 手順3: ログインリンクを物理クリック")
        login_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href,'login')]")))
        current_handles = len(driver.window_handles)
        login_link.click()

        # 再びウィンドウが増えるのを待って切替
        wait.until(lambda d: len(d.window_handles) > current_handles)
        driver.switch_to.window(driver.window_handles[-1])
        log(f"📑 ログイン画面到達: {driver.title}")

        # 手順4: ログインフォーム入力
        log("⌨️ 手順4: ログインフォーム入力")
        
        def fill_form(d):
            targets = [d]
            try:
                # フレーム探索
                frames = d.find_elements(By.TAG_NAME, "frame") + d.find_elements(By.TAG_NAME, "iframe")
                targets.extend(frames)
            except: pass
            
            for t in targets:
                if t != d: d.switch_to.frame(t)
                try:
                    # ここも clickable で待つべきだが、NAME属性は presence で十分なことが多い
                    u = d.find_element(By.NAME, "uid")
                    p = d.find_element(By.NAME, "passwd")
                    u.send_keys(JKK_ID)
                    p.send_keys(JKK_PASSWORD)
                    p.submit()
                    return True
                except:
                    d.switch_to.default_content()
            return False

        wait.until(fill_form)
        log("🚀 ログイン情報を送信完了")

        # 手順5: 成功判定
        log("🏁 成否判定中...")
        wait.until(EC.any_of(
            EC.url_contains("mypage"),
            EC.url_contains("menu"),
            EC.title_contains("おわび")
        ))

        final_url = driver.current_url
        log(f"📍 最終URL: {final_url}")
        
        if "mypage" in final_url or "menu" in final_url:
            log("🎉 ログイン成功！正攻法の物理クリックが勝利しました。")
            if DISCORD_WEBHOOK:
                requests.post(DISCORD_WEBHOOK, json={"content": "✅ JKKログイン成功（物理クリック・安定版）"})
        else:
            log(f"💀 失敗: {driver.title}")

    except Exception as e:
        log(f"❌ エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
