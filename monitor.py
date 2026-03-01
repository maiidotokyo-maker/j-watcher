import os
import sys
import requests
import time
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
    
    # アンチ・ボット設定
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
    wait = WebDriverWait(driver, 25)

    try:
        # 手順1: 公式トップ
        log("🚪 手順1: 公式トップへアクセス")
        driver.get("https://www.to-kousya.or.jp/")

        # 手順2: JKKねっとリンクをJSで強制クリック
        log("🌉 手順2: JKKねっとリンクを同一タブで展開(JS強制)")
        # リンクが見つかるまで待機
        jkk_link = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href,'jkk') or contains(text(),'JKK')]")))
        
        # 画面内にスクロール ＋ target解除 ＋ 強制クリック
        driver.execute_script("""
            arguments[0].scrollIntoView(true);
            arguments[0].setAttribute('target', '_self');
            arguments[0].click();
        """, jkk_link)

        # 手順3: ログインリンクをJSで強制クリック
        log("🔑 手順3: ログインボタンを同一タブで展開(JS強制)")
        login_link = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href,'login') or contains(text(),'ログイン')]")))
        
        driver.execute_script("""
            arguments[0].scrollIntoView(true);
            arguments[0].setAttribute('target', '_self');
            arguments[0].click();
        """, login_link)

        # 手順4: ログインフォーム入力
        log("⌨️ 手順4: ログインフォーム待機...")
        
        def fill_form(d):
            # メイン画面と全フレームを探索
            targets = [d]
            try:
                frames = d.find_elements(By.TAG_NAME, "frame") + d.find_elements(By.TAG_NAME, "iframe")
                targets.extend(frames)
            except: pass
            
            for t in targets:
                if t != d: d.switch_to.frame(t)
                try:
                    u = d.find_element(By.NAME, "uid")
                    p = d.find_element(By.NAME, "passwd")
                    # 入力も念のためJSで行う（確実性アップ）
                    d.execute_script("arguments[0].value = arguments[1];", u, JKK_ID)
                    d.execute_script("arguments[0].value = arguments[1];", p, JKK_PASSWORD)
                    p.submit()
                    return True
                except:
                    d.switch_to.default_content()
            return False

        wait.until(fill_form)
        log("🚀 ログイン情報を送信")

        # 手順5: 成功判定
        log("🏁 最終成否判定中...")
        wait.until(EC.any_of(
            EC.url_contains("mypage"),
            EC.url_contains("menu"),
            EC.title_contains("おわび")
        ))

        final_url = driver.current_url
        log(f"📍 最終URL: {final_url}")
        
        if "mypage" in final_url or "menu" in final_url:
            log("🎉 ログイン成功！JS強制クリックによる物理制約の突破です。")
            if DISCORD_WEBHOOK:
                requests.post(DISCORD_WEBHOOK, json={"content": "✅ JKKログイン成功（JS強制クリック版）"})
        else:
            log(f"💀 失敗: {driver.title}")

    except Exception as e:
        log(f"❌ エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
