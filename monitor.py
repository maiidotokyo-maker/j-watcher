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
    options.add_argument("--headless=new") # 最新のヘッドレスモード
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # 🕵️ 重要：完全に人間を装うための設定
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    options.add_argument(f'--user-agent={user_agent}')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument('--lang=ja-JP') # 言語を日本語に固定

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # 🕵️ 重要：JavaScriptレベルでの自動化判定を削除
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
        """
    })
    return driver

def main():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")

    driver = create_driver()
    wait = WebDriverWait(driver, 30)

    try:
        # ① 直接「お部屋探し」トップではなく、もう少し深い階層から入る
        # (404回避のため、まずはトップページを一度踏む)
        log("🚪 手順1: JKK東京公式サイトへアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        time.sleep(5)
        
        # ② JavaScriptで強制的に「JKKねっと」入り口へ移動
        # (ボタンが見つからない場合も考慮し、直接遷移とクリックを併用)
        log("🔗 手順2: JKKねっと(jhomes)へ遷移中...")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        time.sleep(8)
        
        driver.save_screenshot("after_redirect.png")

        # ③ フォーム入力（iframe/JS対策込み）
        log("⌨️ 手順3: ログインフォーム探索")
        
        # フォームが出るまで最大30秒待つ（海外サーバーからの遅延対策）
        u_field = wait.until(EC.presence_of_element_located((By.NAME, "uid")))
        p_field = driver.find_element(By.NAME, "passwd")

        driver.execute_script("arguments[0].value = arguments[1];", u_field, JKK_ID)
        driver.execute_script("arguments[0].value = arguments[1];", p_field, JKK_PASSWORD)
        
        log("🚀 送信実行")
        driver.save_screenshot("submitting.png")
        p_field.submit()

        # ④ 認証成功確認
        wait.until(EC.any_of(
            EC.url_contains("mypage"),
            EC.url_contains("Menu")
        ))

        log(f"🎉 ログイン成功！ 現在URL: {driver.current_url}")
        if DISCORD_WEBHOOK:
            requests.post(DISCORD_WEBHOOK, json={"content": "✅ JKKログインに成功しました。監視を開始します。"})

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        driver.save_screenshot("last_fatal_error.png")
        # 404が出ているか確認するためにタイトルを表示
        print(f"DEBUG - Page Title: {driver.title}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
