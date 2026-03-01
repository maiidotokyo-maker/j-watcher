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
    # 最新のHeadlessモードを指定
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    # ボット検知回避
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def force_navigate(driver, wait, xpath):
    """要素からURLを抜き取り、JSで現在のタブを強制移動させる"""
    element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    url = element.get_attribute("href")
    log(f"🔗 遷移先URL取得: {url}")
    # location.hrefの書き換えは、Refererを維持しつつ「この窓」で開く最強の手法
    driver.execute_script(f"window.location.href = '{url}';")
    # ページ遷移後のbody出現を待機
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2)

def fill_login_form(driver, uid, pwd):
    """メイン画面 + 全フレームを探索してログイン実行"""
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
            # 入力もJSで確実に行う
            driver.execute_script("arguments[0].value = arguments[1];", u, uid)
            driver.execute_script("arguments[0].value = arguments[1];", p, pwd)
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
    wait = WebDriverWait(driver, 30)

    try:
        # ① 公式トップ
        log("🚪 手順1: トップアクセス")
        driver.get("https://www.to-kousya.or.jp/")

        # ② JKKねっとへ遷移（物理クリックを避け、URL抽出型へ）
        log("🌉 手順2: JKKねっとへ同一タブ遷移")
        force_navigate(driver, wait, "//a[contains(@href,'jkk')]")

        # ③ ログイン画面へ遷移
        log("🔑 手順3: ログイン画面へ同一タブ遷移")
        force_navigate(driver, wait, "//a[contains(@href,'login')]")

        # ④ ログインフォーム入力
        log("⌨️ 手順4: ログインフォーム入力")
        if not fill_login_form(driver, JKK_ID, JKK_PASSWORD):
            log("💀 フォームが見つかりませんでした")
            driver.save_screenshot("no_form.png")
            return

        log("🚀 認証待機中...")
        # URLの変化または特定文字列の出現を待つ
        wait.until(EC.any_of(
            EC.url_contains("mypage"),
            EC.url_contains("menu"),
            EC.title_contains("おわび")
        ))

        final_url = driver.current_url
        log(f"📍 最終URL: {final_url}")

        if "mypage" in final_url or "menu" in final_url:
            log("🎉 ログイン成功！")
            if DISCORD_WEBHOOK:
                requests.post(DISCORD_WEBHOOK, json={"content": "✅ JKKログイン成功（CI特化・URL抽出版）"})
        else:
            log(f"💀 失敗: {driver.title}")
            driver.save_screenshot("fail.png")

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        driver.save_screenshot("error.png")
    finally:
        driver.quit()
        log("🏁 プロセス終了")

if __name__ == "__main__":
    main()
