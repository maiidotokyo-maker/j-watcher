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
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # 日本の一般的な環境を偽装
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    options.add_argument(f'--user-agent={user_agent}')
    options.add_argument('--lang=ja-JP')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

def main():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")

    driver = create_driver()
    wait = WebDriverWait(driver, 45) # 待機をさらに延長

    try:
        # 1. 検索条件入力ページへ（ここでシステム全体のCookieをセットさせる）
        log("🚪 手順1: 空室検索ページでセッションを確立")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/initS01")
        time.sleep(10) # コンテンツのロードをじっくり待つ

        # 2. 検索ページが開けているか確認（空っぽならここで終了）
        driver.save_screenshot("step1_search_page.png")
        
        # 3. ログインページへ移動
        log("🔗 手順2: ログインページへ切り替え")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        time.sleep(10)
        driver.save_screenshot("step2_login_form.png")

        # 4. フォーム入力（iframe対応）
        log("⌨️ 手順3: ログインフォーム入力")
        
        # iframeが複数ある可能性を考慮し、中身を探す
        if len(driver.find_elements(By.TAG_NAME, "iframe")) > 0:
            log("📦 iframe切り替え実行")
            # コンテンツが入っているiframeを特定してスイッチ
            frames = driver.find_elements(By.TAG_NAME, "iframe")
            driver.switch_to.frame(frames[0])

        # uidが出るまで待機
        u_field = wait.until(EC.presence_of_element_located((By.NAME, "uid")))
        p_field = driver.find_element(By.NAME, "passwd")

        driver.execute_script("arguments[0].value = arguments[1];", u_field, JKK_ID)
        driver.execute_script("arguments[0].value = arguments[1];", p_field, JKK_PASSWORD)
        
        log("🚀 送信")
        p_field.submit()

        # 5. 成功判定
        wait.until(EC.any_of(
            EC.url_contains("mypage"),
            EC.title_contains("マイページ")
        ))
        log("🎉 ログイン成功！")

    except Exception as e:
        log(f"❌ エラー: {e}")
        driver.save_screenshot("error_detail.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
