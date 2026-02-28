import sys
import os
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

sys.stdout.reconfigure(encoding='utf-8')
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def main():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--lang=ja-JP')
    # あなたのブラウザのUAに似せる（一応の保険）
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        log("🚪 玄関からログインを開始します...")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/")
        time.sleep(5)

        # 1. ログインページへ（JS実行）
        driver.execute_script("if(typeof mypageLogin === 'function') mypageLogin();")
        time.sleep(5)
        
        # 2. 窓の切り替え
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])

        # 3. ログイン実行
        u = driver.find_elements(By.NAME, "uid")
        if u:
            log("🔑 ID/PWを入力中...")
            u[0].send_keys(os.environ.get("JKK_ID"))
            driver.find_element(By.NAME, "passwd").send_keys(os.environ.get("JKK_PASSWORD"))
            driver.find_element(By.XPATH, "//input[@type='image']|//img[contains(@src,'login')]").click()
            time.sleep(8)
            log(f"🔓 ログイン後のURL: {driver.current_url}")

            # --- ここからが「成功」への鍵：Cookieを抜き取ってrequestsへ ---
            session = requests.Session()
            for cookie in driver.get_cookies():
                session.cookies.set(cookie['name'], cookie['value'])
            
            # 4. 本丸（空室検索）へアクセス
            # URLが動的に変わる可能性があるので、もしダメならここを調整
            TARGET_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/emptyConditionSearch"
            res = session.get(TARGET_URL)
            res.encoding = 'cp932'

            if "条件入力" in res.text or "空室" in res.text:
                log("🎉 完璧です！正常な画面を捕捉しました。")
                # ここで res.text を解析して空室を探す
            else:
                log(f"🚨 突破しましたが期待した画面ではありません。Title: {driver.title}")
        else:
            log("🚨 ログインフォームにたどり着けませんでした。")

    except Exception as e:
        log(f"❌ エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
