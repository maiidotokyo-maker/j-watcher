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
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--single-process")
    options.add_argument("--no-zygote")
    options.add_argument("--window-size=1280,1024")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def force_navigate(driver, wait, xpath_list, step_name):
    """XPathリストからリンクを探してクリックまたは遷移"""
    log(f"🔎 {step_name} のリンクを探索中...")
    element = None
    for xpath in xpath_list:
        try:
            element = driver.find_element(By.XPATH, xpath)
            if element:
                break
        except: continue

    if not element:
        log(f"💀 {step_name} リンク未検出。スクショとHTMLを保存します。")
        driver.save_screenshot(f"debug_{step_name}_not_found.png")
        print(f"--- SOURCE START ---\n{driver.page_source[:2000]}\n--- SOURCE END ---")
        raise Exception(f"{step_name} リンクが見つかりません")

    href = element.get_attribute("href")
    log(f"🔗 ターゲット発見: {href}")
    if href and (href.startswith("http") or href.startswith("/")):
        driver.get(href)
    else:
        driver.execute_script("arguments[0].click();", element)

    # ページ遷移の安定待ち
    time.sleep(5)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

def fill_login_form(driver, uid, pwd):
    """ログインフォーム探索＋入力＋送信"""
    targets = [driver]
    try:
        frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
        targets.extend(frames)
    except: pass

    for t in targets:
        if t != driver:
            driver.switch_to.frame(t)
        try:
            u = driver.find_element(By.NAME, "uid")
            p = driver.find_element(By.NAME, "passwd")
            driver.execute_script("arguments[0].value = arguments[1];", u, uid)
            driver.execute_script("arguments[0].value = arguments[1];", p, pwd)
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
        # ① 公式トップ
        log("🚪 手順1: 公式トップアクセス")
        driver.get("https://www.to-kousya.or.jp/")

        # ② JKKねっとトップへ遷移
        force_navigate(driver, wait, ["//a[contains(@href,'jkk')]"], "JKKトップ")

        # ③ ログイン画面への遷移
        login_xpaths = [
            "//a[contains(@href, 'login')]",
            "//a[contains(@href, 'Login')]",
            "//area[contains(@href, 'login')]",
            "//img[contains(@alt, 'ログイン')]/.."
        ]
        force_navigate(driver, wait, login_xpaths, "ログイン画面")

        # ④ ログインフォーム入力
        log("⌨️ ログイン情報入力")
        driver.save_screenshot("at_login_page.png")
        if not fill_login_form(driver, JKK_ID, JKK_PASSWORD):
            log("💀 フォームが見つかりませんでした")
            driver.save_screenshot("no_form.png")
            return

        # ⑤ 認証後 URL 変化待機
        wait.until(EC.any_of(
            EC.url_contains("mypage"),
            EC.url_contains("menu"),
            EC.title_contains("おわび")
        ))

        final_url = driver.current_url
        log(f"📍 到達URL: {final_url}")

        if "mypage" in final_url or "menu" in final_url:
            log("🎉 ログイン成功！")
            if DISCORD_WEBHOOK:
                requests.post(DISCORD_WEBHOOK, json={"content": "✅ JKKログイン成功！監視を開始します。"})
        else:
            log(f"💀 失敗: {driver.title}")
            driver.save_screenshot("fail.png")

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        try:
            driver.save_screenshot("error.png")
        except: pass
    finally:
        driver.quit()
        log("🏁 プロセス終了")

if __name__ == "__main__":
    main()
