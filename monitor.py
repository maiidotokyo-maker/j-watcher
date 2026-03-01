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

# 標準出力をUTF-8に設定
sys.stdout.reconfigure(encoding="utf-8")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def get_japan_proxy():
    """日本の無料プロキシリストから1つ取得を試みる（予備用）"""
    try:
        log("🌐 日本のプロキシサーバーを探索中...")
        # 公開API等から取得するロジック（簡易版：固定リストや特定のAPI）
        # ※無料プロキシは不安定なため、失敗した場合はプロキシなしで続行します
        return None 
    except:
        return None

def create_driver(proxy=None):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
        log(f"🛰️ プロキシを使用します: {proxy}")

    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    options.add_argument(f'--user-agent={ua}')
    options.add_argument("--disable-blink-features=AutomationControlled")
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

    # 1. 実行環境のIPを確認（デバッグ用）
    try:
        ip_info = requests.get("https://ipinfo.io/json", timeout=5).json()
        log(f"🌍 実行環境: {ip_info.get('ip')} ({ip_info.get('country')}, {ip_info.get('region')})")
    except:
        log("⚠️ IP情報の取得に失敗しました")

    driver = create_driver()
    wait = WebDriverWait(driver, 30)

    try:
        # 手順1: トップページアクセス
        log("🚪 手順1: JKK東京トップページへアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        time.sleep(5)

        # 手順2: ログインページへ直接遷移
        log("🔗 手順2: ログインページへ直接遷移")
        driver.execute_script("window.location.href = 'https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu';")
        
        # JSロード待機（海外IPだとここでフォームが消える）
        log("⏳ JSロードおよび描画待機（30秒）...")
        time.sleep(30)
        driver.save_screenshot("debug_result.png")

        # 手順3: iframe探索
        log("⌨️ 手順3: ログインフォームを探索")
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        log(f"発見されたiframe数: {len(frames)}")

        if len(frames) == 0:
            log("❌ フォームが生成されませんでした。海外IP制限の可能性があります。")
            # ここでページソースを出力して原因を特定
            with open("page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            raise Exception("Login form not rendered (Possible Geo-blocking)")

        found = False
        for i, frame in enumerate(frames):
            driver.switch_to.frame(frame)
            try:
                u_field = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.NAME, "uid")))
                p_field = driver.find_element(By.NAME, "passwd")
                
                log(f"✅ iframe[{i}] 内にフォームを捕捉。ログインを試行します。")
                driver.execute_script("arguments[0].value = arguments[1];", u_field, JKK_ID)
                driver.execute_script("arguments[0].value = arguments[1];", p_field, JKK_PASSWORD)
                
                driver.save_screenshot("debug_submitting.png")
                p_field.submit()
                found = True
                break
            except:
                driver.switch_to.default_content()

        if not found:
            raise Exception("フォームは見つかりましたが、入力に失敗しました。")

        # 4. ログイン成功判定
        log("🚀 ログイン後の遷移を確認中...")
        time.sleep(10)
        if "mypage" in driver.current_url.lower() or "マイページ" in driver.title:
            log("🎉 ログイン成功！")
            if DISCORD_WEBHOOK:
                requests.post(DISCORD_WEBHOOK, json={"content": "✅ JKKログインに成功しました。"})
        else:
            log(f"⚠️ 現在のURL: {driver.current_url}")
            driver.save_screenshot("debug_after_submit.png")

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        driver.save_screenshot("final_error.png")
    finally:
        driver.quit()
        log("🏁 プロセス終了")

if __name__ == "__main__":
    main()
