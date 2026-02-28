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

START_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/"
TARGET_JSP = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"

def setup_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,1024')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    options.add_argument('--lang=ja-JP')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = None
    try:
        driver = setup_driver()
        
        log("🚪 玄関ページにアクセス中...")
        driver.get(START_URL)
        time.sleep(5)
        
        # --- 魔法の一手：偽装フレーム構築 ---
        log("🪄 仮想フレームを構築し、中身を直接召喚します...")
        driver.execute_script(f"""
            document.body.innerHTML = '<iframe id="retro-frame" src="{TARGET_JSP}" style="width:100%;height:100vh;border:none;"></iframe>';
        """)
        
        time.sleep(15) # 中身のJSPがロードされるのを待つ
        
        # フレームの中に潜る
        try:
            driver.switch_to.frame("retro-frame")
            log(f"🔎 フレーム内部のURL: {driver.current_url}")
            
            # フォームを探索
            u_tags = driver.find_elements(By.NAME, "uid")
            p_tags = driver.find_elements(By.XPATH, "//input[@type='password']")
            
            if u_tags and p_tags:
                log("🎯 ついに生身のログインフォームを捕捉しました！")
                u_tags[0].send_keys(os.environ.get("JKK_ID"))
                p_tags[0].send_keys(os.environ.get("JKK_PASSWORD"))
                
                # 送信ボタンをクリック
                btn = driver.find_element(By.XPATH, "//img[contains(@src, 'login')] | //input[@type='submit']")
                btn.click()
                
                log("🚀 ログイン情報を送信。成功を祈ります...")
                time.sleep(10)
                driver.switch_to.default_content() # 元に戻る
                log(f"最終到達URL: {driver.current_url}")
                
            else:
                log("🚨 フレーム内にもフォームがありません。おわびが継続しています。")
                log(f"フレーム内Title: {driver.title}")
                # 最終デバッグ：全ソース
                log("--- SOURCE START ---")
                log(driver.page_source[:1000])
                log("--- SOURCE END ---")
                
        except Exception as fe:
            log(f"❌ フレーム操作エラー: {fe}")

    except Exception as e:
        log(f"❌ 致命的エラー: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
