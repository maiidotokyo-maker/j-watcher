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
    """時刻付きでログを出力する関数"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # 🕵️ 人間らしいUser-Agent設定
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    options.add_argument(f'--user-agent={ua}')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # 🛡️ webdriverプロパティを隠蔽してボット検知を回避
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', {get: () => ['ja-JP', 'ja']});
        """
    })
    return driver

def main():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")

    driver = create_driver()
    wait = WebDriverWait(driver, 30)

    try:
        # 手順1: トップから正規Cookie取得
        log("🚪 手順1: トップページへアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        time.sleep(5)

        # 手順2: ログインページへ（リファラを維持して遷移）
        log("🔗 手順2: ログインページへ直接遷移")
        driver.execute_script("window.location.href = 'https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu';")
        
        # ロード時間を確保し、JS実行を待つ
        log("⏳ ロード待機中（30秒）...")
        time.sleep(30)
        driver.save_screenshot("debug_login_check.png")

        # 手順3: iframe探索と入力
        log("⌨️ 手順3: ログインフォームを探索")
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        log(f"発見されたiframe数: {len(frames)}")

        found = False
        for i, frame in enumerate(frames):
            driver.switch_to.frame(frame)
            try:
                # フォームが表示されるまで最大15秒待機
                u_field = WebDriverWait(driver, 15).until(
                    EC.visibility_of_element_located((By.NAME, "uid"))
                )
                p_field = driver.find_element(By.NAME, "passwd")
                
                log(f"✅ iframe[{i}] 内でログインフォームを捕捉しました。")
                
                # JSで値をセット（入力ミス防止）
                driver.execute_script("arguments[0].value = arguments[1];", u_field, JKK_ID)
                driver.execute_script("arguments[0].value = arguments[1];", p_field, JKK_PASSWORD)
                
                driver.save_screenshot("debug_submitting.png")
                p_field.submit()
                found = True
                break
            except:
                driver.switch_to.default_content()

        if not found:
            # iframeが見つからない場合、念のためページ全体から探す
            try:
                u_field = driver.find_element(By.NAME, "uid")
                u_field.send_keys(JKK_ID)
                driver.find_element(By.NAME, "passwd").send_keys(JKK_PASSWORD)
                u_field.submit()
                found = True
            except:
                raise Exception("ログインフォームが見つかりませんでした。JSがロードされていない可能性があります。")

        # 成功判定
        log("🚀 認証結果を確認中...")
        time.sleep(10)
        driver.save_screenshot("debug_after_login.png")
        
        if "mypage" in driver.current_url.lower() or "マイページ" in driver.title:
            log("🎉 ログイン成功！")
            if DISCORD_WEBHOOK:
                requests.post(DISCORD_WEBHOOK, json={"content": "✅ JKKログインに成功しました。"})
        else:
            log(f"⚠️ ログイン後のURLが期待と異なります: {driver.current_url}")

    except Exception as e:
        log(f"❌ エラー: {e}")
        driver.save_screenshot("final_error.png")
    finally:
        driver.quit()
        log("🏁 プロセス終了")

if __name__ == "__main__":
    main()
