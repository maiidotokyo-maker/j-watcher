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
    # 解像度を上げてPCレイアウトを強制
    options.add_argument("--window-size=1920,1080")
    
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    options.add_argument(f'--user-agent={user_agent}')
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
    wait = WebDriverWait(driver, 30)

    try:
        # 1. トップページで正規Cookieを取得
        log("🚪 手順1: トップページへアクセス（Cookie取得）")
        driver.get("https://www.to-kousya.or.jp/")
        time.sleep(5)
        
        # 2. ログインページへ直接ジャンプ（リファラを維持）
        log("🔗 手順2: ログインページへ直接遷移")
        driver.execute_script("window.location.href = 'https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu';")
        
        # JSロードと画面描画を十分に待つ（真っ白画面対策）
        log("⏳ JSロード待機中（20秒）...")
        time.sleep(20)
        driver.save_screenshot("debug_login_page.png")

        # 3. iframe探索とフォーム入力
        log("⌨️ 手順3: ログインフォームを探索")
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        found = False

        for i, frame in enumerate(frames):
            driver.switch_to.frame(frame)
            try:
                # 10秒待機して uid 入力欄を探す
                u_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "uid")))
                p_field = driver.find_element(By.NAME, "passwd")
                
                log(f"✅ iframe[{i}] 内にフォームを発見")
                driver.execute_script("arguments[0].value = arguments[1];", u_field, JKK_ID)
                driver.execute_script("arguments[0].value = arguments[1];", p_field, JKK_PASSWORD)
                
                p_field.submit()
                found = True
                break
            except:
                driver.switch_to.default_content()

        if not found:
            raise Exception("ログインフォームが見つかりませんでした。")

        # 4. 成功判定
        log("🚀 認証結果を確認中...")
        wait.until(EC.any_of(
            EC.url_contains("mypage"),
            EC.title_contains("マイページ")
        ))
        
        log("🎉 ログイン成功！")
        if DISCORD_WEBHOOK:
            requests.post(DISCORD_WEBHOOK, json={"content": "✅ ログインに成功しました。監視を継続します。"})

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        driver.save_screenshot("final_error_report.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
