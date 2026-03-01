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

# UTF-8 出力
sys.stdout.reconfigure(encoding="utf-8")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def create_driver():
    options = Options()
    options.add_argument("--headless")  # CI環境でも安定
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--single-process")
    options.add_argument("--no-zygote")
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

def fill_login_form(driver, uid, pwd):
    """ログインフォーム入力と送信"""
    try:
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.NAME, "uid")))
        u_field = driver.find_element(By.NAME, "uid")
        p_field = driver.find_element(By.NAME, "passwd")
        driver.execute_script("arguments[0].value = arguments[1];", u_field, uid)
        driver.execute_script("arguments[0].value = arguments[1];", p_field, pwd)
        driver.save_screenshot("before_submit.png")
        p_field.submit()
        return True
    except Exception as e:
        log(f"💀 フォーム入力失敗: {e}")
        driver.save_screenshot("login_form_error.png")
        return False

def main():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")

    driver = create_driver()
    wait = WebDriverWait(driver, 45)

    try:
        # ① ログインページに直接アクセス
        LOGIN_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu"
        log(f"🚪 ログインページにアクセス: {LOGIN_URL}")
        driver.get(LOGIN_URL)

        # ② ログインフォーム入力
        log("⌨️ ログインフォーム入力中...")
        if not fill_login_form(driver, JKK_ID, JKK_PASSWORD):
            log("❌ ログインフォームにアクセスできませんでした")
            return

        # ③ 認証後の URL またはタイトル変化を待機
        log("🚀 認証待機中...")
        wait.until(EC.any_of(
            EC.url_contains("mypageMenu"),
            EC.title_contains("おわび")
        ))

        final_url = driver.current_url
        log(f"📍 到着URL: {final_url}")

        if "mypageMenu" in final_url:
            log("🎉 ログイン成功！")
            if DISCORD_WEBHOOK:
                requests.post(DISCORD_WEBHOOK, json={"content": "✅ JKKログイン成功！監視を開始します。"})
        else:
            log(f"💀 ログイン失敗: {driver.title}")
            driver.save_screenshot("fail_page.png")

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        try:
            driver.save_screenshot("error_final.png")
            print(f"--- SOURCE DEBUG ---\n{driver.page_source[:1000]}")
        except: pass
    finally:
        driver.quit()
        log("🏁 プロセス終了")

if __name__ == "__main__":
    main()
