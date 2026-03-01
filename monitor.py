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
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--single-process")
    options.add_argument("--no-zygote")
    options.add_argument("--window-size=1280,1024")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def fill_login_form(driver, uid, pwd):
    """ログインフォームを探索し入力 + 送信"""
    targets = [driver]
    try:
        frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
        targets.extend(frames)
    except: pass

    for t in targets:
        if t != driver: driver.switch_to.frame(t)
        try:
            u = driver.find_element(By.NAME, "uid")
            p = driver.find_element(By.NAME, "passwd")
            # JSで確実に値をセット
            driver.execute_script("arguments[0].value = arguments[1];", u, uid)
            driver.execute_script("arguments[0].value = arguments[1];", p, pwd)
            
            # 送信ボタンを探してクリック（submit()より確実な場合があるため）
            try:
                btn = driver.find_element(By.XPATH, "//input[@type='submit' or @type='image']")
                btn.click()
            except:
                p.submit()
            return True
        except:
            driver.switch_to.default_content()
    return False

def main():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")

    driver = create_driver()
    wait = WebDriverWait(driver, 45)

    try:
        # ✅ 正しいJKKねっとログイン画面へのダイレクトアクセス
        login_url = "https://www.inter-jkk.or.jp/NASApp/kk01/ActionController?id=I_Logon"
        log(f"🔑 ログイン画面へアクセス: {login_url}")
        driver.get(login_url)
        
        # フォームの出現を待つ
        wait.until(EC.presence_of_element_located((By.NAME, "uid")))
        time.sleep(2)

        log("⌨️ ログイン情報を入力中...")
        if not fill_login_form(driver, JKK_ID, JKK_PASSWORD):
            log("💀 フォームが見つかりませんでした")
            driver.save_screenshot("no_form.png")
            return

        log("🚀 認証待機中...")
        # 成功時の遷移先URLに含まれるキーワードを待機
        wait.until(EC.any_of(
            EC.url_contains("Menu"),
            EC.url_contains("Mypage"),
            EC.url_contains("menu"),
            EC.title_contains("おわび")
        ))

        final_url = driver.current_url
        log(f"📍 到着URL: {final_url}")

        if any(x in final_url for x in ["Menu", "Mypage", "menu"]):
            log("🎉 ログイン成功！")
            if DISCORD_WEBHOOK:
                requests.post(DISCORD_WEBHOOK, json={"content": "✅ JKKログイン成功！監視を開始します。"})
        else:
            log(f"💀 失敗: {driver.title}")
            driver.save_screenshot("fail.png")

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        try: driver.save_screenshot("error.png")
        except: pass
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
