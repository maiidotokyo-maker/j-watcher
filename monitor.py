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
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    # --- 【重要】アンチ・ボット設定 ---
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # navigator.webdriver を隠蔽（これをしないと「おわび」率が上がります）
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def safe_screenshot(driver, name):
    if os.environ.get("GITHUB_ACTIONS") != "true":
        driver.save_screenshot(name)

def switch_to_latest_window(driver, wait, expected_count):
    """新しいウィンドウが期待数になるまで待機して切替"""
    wait.until(lambda d: len(d.window_handles) >= expected_count)
    driver.switch_to.window(driver.window_handles[-1])

def fill_login_form(driver, wait, uid, pwd):
    """メイン画面＋全フレームを探索してuid/passwdを入力"""
    # 1. まずメイン画面を試す
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
        pass

    # 2. フレーム内を探索
    frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
    for frame in frames:
        try:
            driver.switch_to.frame(frame)
            uid_field = driver.find_element(By.NAME, "uid")
            pwd_field = driver.find_element(By.NAME, "passwd")
            uid_field.clear()
            uid_field.send_keys(uid)
            pwd_field.clear()
            pwd_field.send_keys(pwd)
            pwd_field.submit()
            return True # フレーム内での送信成功
        except:
            driver.switch_to.default_content() # 失敗したら戻る
    return False

def main():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")

    if not JKK_ID or not JKK_PASSWORD:
        log("❌ ID/PW未設定")
        sys.exit(1)

    driver = create_driver()
    wait = WebDriverWait(driver, 30)

    try:
        # ① 公式トップ
        log("🚪 手順1: 公式トップへアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # ② JKKねっとリンクを物理クリック（User案）
        log("🌉 手順2: JKKねっとリンクを物理クリック")
        jkk_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href,'jkk') or contains(text(),'JKK')]")))
        jkk_link.click()

        # ウィンドウ数 2 を待機
        switch_to_latest_window(driver, wait, 2)
        log(f"📑 JKKページ到達: {driver.title}")

        # ③ ログインリンクをクリック（User案）
        log("🔑 手順3: ログインリンクを物理クリック")
        login_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href,'login') or contains(text(),'ログイン')]")))
        login_link.click()

        # ウィンドウ数 3 を待機
        switch_to_latest_window(driver, wait, 3)
        log(f"📑 ログイン画面到達: {driver.title}")

        # ④ ログインフォーム入力
        log("⌨️ 手順4: ログインフォーム入力")
        if not fill_login_form(driver, wait, JKK_ID, JKK_PASSWORD):
            raise Exception("ログインフォームを検出できませんでした")

        log("🚀 ログイン送信完了")

        # ⑤ 成功判定
        wait.until(EC.any_of(
            EC.url_contains("mypage"),
            EC.url_contains("menu"),
            EC.title_contains("おわび")
        ))

        current_url = driver.current_url
        log(f"📍 最終URL: {current_url}")

        if "mypage" in current_url or "menu" in current_url:
            log("🎉 ログイン成功！")
            if DISCORD_WEBHOOK:
                requests.post(DISCORD_WEBHOOK, json={"content": "✅ JKKログイン成功（正攻法ハイブリッド版）"})
        else:
            log(f"💀 ログイン失敗。タイトル: {driver.title}")
            safe_screenshot(driver, "fail.png")

    except TimeoutException:
        log("⏳ タイムアウト発生（要素が見つからないか、おわび画面で停止）")
        safe_screenshot(driver, "timeout.png")
    except Exception as e:
        log(f"❌ エラー: {e}")
        safe_screenshot(driver, "error.png")
    finally:
        driver.quit()
        log("🏁 プロセス終了")

if __name__ == "__main__":
    main()
