import sys
import os
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1200')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # 手順1: トップページ（セッションの起点）
        log("🚪 手順1: 公社公式サイト(www)へアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        time.sleep(10) # 読み込みを十分に待つ

        # 手順2: リンクを探して「JavaScript」で強制クリック
        log("🔍 手順2: 『JKKねっと』への入り口を物理探索中...")
        # 文字列一致で探す
        links = driver.find_elements(By.XPATH, "//a[contains(text(), 'JKKねっと') or contains(@href, 'jkknet')]")
        
        if links:
            log(f"🎯 入り口発見。JSで強制クリックします。")
            driver.execute_script("arguments[0].click();", links[0])
        else:
            log("🚨 リンク未発見。直接移動を試みます（くじら警戒）")
            driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/")
        
        time.sleep(8)

        # 手順3: ログインボタンの強制発火
        log("🔍 手順3: ログインボタンを探索")
        driver.execute_script("try { mypageLogin(); } catch(e) { console.log('Login function not found'); }")
        time.sleep(8)

        # 別窓対応
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            log("📑 ログイン画面へ切り替えました")

        # 手順4: ID/PW投入
        log("⌨️ 手順4: IDとPWを入力")
        
        def input_field():
            try:
                u = driver.find_element(By.NAME, "uid")
                p = driver.find_element(By.NAME, "passwd")
                u.send_keys(os.environ.get("JKK_ID"))
                p.send_keys(os.environ.get("JKK_PASSWORD"), Keys.ENTER)
                return True
            except:
                return False

        if not input_field():
            frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(frames)):
                driver.switch_to.frame(i)
                if input_field():
                    log(f"🎯 第{i}フレームで入力成功")
                    break
                driver.switch_to.default_content()

        time.sleep(15)
        
        log(f"📍 最終URL: {driver.current_url}")
        if "mypageMenu" in driver.current_url:
            log("🎉 成功！")
            if os.environ.get("DISCORD_WEBHOOK_URL"):
                requests.post(os.environ["DISCORD_WEBHOOK_URL"], json={"content": "✅ JKKログイン成功！"})
        else:
            log(f"💀 ログイン失敗。タイトル: {driver.title}")
            driver.save_screenshot("final_check.png")

    except Exception as e:
        log(f"❌ エラー: {e}")
        driver.save_screenshot("crash_report.png")
    finally:
        driver.quit()
        log("🏁 終了")

if __name__ == "__main__":
    main()
