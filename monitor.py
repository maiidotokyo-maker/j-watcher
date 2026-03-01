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
from selenium.common.exceptions import TimeoutException
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
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    # ボット検知回避
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    # navigator.webdriver 隠蔽
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def safe_screenshot(driver, name):
    if os.environ.get("GITHUB_ACTIONS") != "true":
        driver.save_screenshot(name)

def fill_login_form(driver, uid, pwd):
    """メイン画面＋全フレームを探索してログイン"""
    targets = [driver]
    try:
        frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
        targets.extend(frames)
    except:
        pass

    for t in targets:
        if t != driver:
            driver.switch_to.frame(t)
        try:
            uid_field = driver.find_element(By.NAME, "uid")
            pwd_field = driver.find_element(By.NAME, "passwd")
            uid_field.clear()
            uid_field.send_keys(uid)
            pwd_field.clear()
            pwd_field.send_keys(pwd)
            pwd_field.submit()
            return True
        except:
            driver.switch_to.default_content()
    return False

def main():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")

    if not JKK_ID or not JKK_PASSWORD:
        log("❌ ID/PW未設定")
        sys.exit(1)

    driver = create_driver()
    wait = WebDriverWait(driver, 30)  # CI環境の遅延考慮

    try:
        # ① トップアクセス
        log("🚪 公式トップアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # ② JKKねっとリンクを同一タブでクリック
        log("🌉 JKKねっとリンククリック")
        jkk_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href,'jkk')]")))
        driver.execute_script("arguments[0].setAttribute('target','_self'); arguments[0].click();", jkk_link)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # ③ ログインリンクを同一タブでクリック
        log("🔑 ログインリンククリック")
        login_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href,'login')]")))
        driver.execute_script("arguments[0].setAttribute('target','_self'); arguments[0].click();", login_link)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # ④ ログインフォーム入力
        log("⌨️ ログインフォーム入力")
        if not fill_login_form(driver, JKK_ID, JKK_PASSWORD):
            raise Exception("ログインフォーム検出失敗")

        log("🚀 ログイン送信完了")

        # ⑤ 成否判定
        wait.until(EC.any_of(
            EC.url_contains("mypage"),
            EC.url_contains("menu"),
            EC.title_contains("おわび")
        ))

        final_url = driver.current_url
        log(f"📍 最終URL: {final_url}")

        if "mypage" in final_url or "menu" in final_url:
            log("🎉 ログイン成功")
            if DISCORD_WEBHOOK:
                requests.post(DISCORD_WEBHOOK, json={"content": "✅ JKKログイン成功（安定版同一タブ）"})
        else:
            log(f"💀 ログイン失敗: {driver.title}")
            safe_screenshot(driver, "fail.png")

    except TimeoutException:
        log("⏳ タイムアウト発生")
        safe_screenshot(driver, "timeout.png")
    except Exception as e:
        log(f"❌ エラー: {e}")
        safe_screenshot(driver, "error.png")
    finally:
        driver.quit()
        log("🏁 プロセス終了")

if __name__ == "__main__":
    main()
