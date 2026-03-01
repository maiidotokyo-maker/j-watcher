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
from selenium.webdriver.common.action_chains import ActionChains
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
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def wait_and_click(driver, wait, by, target):
    """ActionChainsで確実にクリック"""
    elem = wait.until(EC.element_to_be_clickable((by, target)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
    time.sleep(1) # スクロール後の安定待ち
    ActionChains(driver).move_to_element(elem).click().perform()
    log(f"🖱️ Clicked: {target}")

def fill_login_form(driver, wait, uid, pwd):
    """全フレームを探索してログイン。送信ボタンも物理クリックを試行"""
    targets = [driver]
    try:
        targets.extend(driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe"))
    except: pass

    for t in targets:
        if t != driver: driver.switch_to.frame(t)
        try:
            u = driver.find_element(By.NAME, "uid")
            p = driver.find_element(By.NAME, "passwd")
            u.send_keys(uid)
            p.send_keys(pwd)
            # 送信ボタンをNAMEやXPATHで探してクリック。なければsubmit()
            try:
                # JKKのログインボタンの一般的なパターン
                login_btn = driver.find_element(By.XPATH, "//input[@type='submit' or @type='image' or contains(@src, 'login')]")
                login_btn.click()
            except:
                p.submit()
            return True
        except:
            driver.switch_to.default_content()
    return False

def run_monitor():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")

    driver = create_driver()
    wait = WebDriverWait(driver, 45)

    try:
        log("🚪 公式トップアクセス")
        driver.get("https://www.to-kousya.or.jp/")

        log("🌉 JKKねっとリンククリック")
        handles_before = len(driver.window_handles)
        wait_and_click(driver, wait, By.XPATH, "//a[contains(@href,'jkk')]")
        
        # ウィンドウが増えるまで待機してから切替
        wait.until(lambda d: len(d.window_handles) > handles_before)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(2)

        log("🔑 ログインリンククリック")
        handles_before = len(driver.window_handles)
        wait_and_click(driver, wait, By.XPATH, "//a[contains(@href,'login')]")
        
        wait.until(lambda d: len(d.window_handles) > handles_before)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(2)

        log("⌨️ ログインフォーム入力")
        if not fill_login_form(driver, wait, JKK_ID, JKK_PASSWORD):
            log("💀 フォームが見つかりません")
            return

        log("🚀 認証待機...")
        # URLが変わるか、特定要素が出るまで待機
        wait.until(EC.any_of(
            EC.url_contains("mypage"),
            EC.url_contains("menu"),
            EC.title_contains("おわび")
        ))

        if "mypage" in driver.current_url or "menu" in driver.current_url:
            log("🎉 ログイン成功！")
            if DISCORD_WEBHOOK:
                requests.post(DISCORD_WEBHOOK, json={"content": "✅ JKKログイン成功！\n監視を開始します。"})
            
            # TODO: ここに空室検索ロジックを追加
            
        else:
            log(f"💀 失敗: {driver.title}")

    except Exception as e:
        log(f"❌ エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    # 日本時間(JST)で計算 (GitHub Actionsは通常UTCなので注意)
    # UTC 23:00 〜 11:00 が 日本時間 8:00 〜 20:00
    run_monitor() # まずは時間制限なしでテスト
