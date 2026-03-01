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

# 標準出力をUTF-8に
sys.stdout.reconfigure(encoding="utf-8")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def create_driver():
    options = Options()
    # CI向け安定ヘッドレス
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,1024")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    # ボット検知回避
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
    wait = WebDriverWait(driver, 45)

    try:
        # ① 公式トップアクセス
        log("🚪 手順1: 公式トップアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        
        # ② 「JKKねっと」へのリンクを「ドメイン指定」で探す（FAQサイトを回避）
        log("🔎 手順2: JKKねっと（本物）のリンクを探索中...")
        # FAQサイト(support.to-kousya...)ではなく inter-jkk.or.jp を含むリンクを狙い撃ち
        jkk_net_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'inter-jkk.or.jp')]")))
        log(f"🔗 ターゲットURL発見: {jkk_net_link.get_attribute('href')}")
        jkk_net_link.click()

        # ③ ログインボタンを「画像属性」で探す（日本語テキストを使わない）
        log("🔎 手順3: ログイン画面への遷移ボタンを探索中...")
        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'Logon') or contains(@href, 'login')]")))
        login_btn.click()

        # ④ ログインフォーム入力
        log("⌨️ 手順4: ログインフォーム入力")
        wait.until(EC.presence_of_element_located((By.NAME, "uid")))
        
        u_field = driver.find_element(By.NAME, "uid")
        p_field = driver.find_element(By.NAME, "passwd")
        
        # JSで確実に入力
        driver.execute_script("arguments[0].value = arguments[1];", u_field, JKK_ID)
        driver.execute_script("arguments[0].value = arguments[1];", p_field, JKK_PASSWORD)
        
        driver.save_screenshot("before_submit.png")
        p_field.submit()

        # ⑤ 認証後の待機
        log("🚀 認証待機中...")
        wait.until(EC.any_of(
            EC.url_contains("Menu"),
            EC.url_contains("Mypage"),
            EC.title_contains("おわび")
        ))

        final_url = driver.current_url
        log(f"📍 到着URL: {final_url}")

        if "Menu" in final_url or "Mypage" in final_url or "menu" in final_url:
            log("🎉 ログイン成功！")
            if DISCORD_WEBHOOK:
                requests.post(DISCORD_WEBHOOK, json={"content": "✅ JKKログイン成功！監視を開始します。"})
        else:
            log(f"💀 失敗: {driver.title}")
            driver.save_screenshot("fail_page.png")

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        driver.save_screenshot("error_final.png")
        print(f"--- SOURCE DEBUG ---\n{driver.page_source[:1000]}")
    finally:
        driver.quit()
        log("🏁 プロセス終了")

if __name__ == "__main__":
    main()
