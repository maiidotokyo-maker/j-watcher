import sys
import os
import time
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
# ログイン画面の本体（JSP）
LOGIN_TARGET = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"

def setup_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,1024')
    options.add_argument('--lang=ja-JP')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = None
    try:
        driver = setup_driver()
        
        log("🚪 玄関ページにアクセスしてCookieを確保...")
        driver.get(START_URL)
        time.sleep(8)
        
        # --- レトロサイト攻略：箱庭（Frameset）の構築 ---
        log("🏗️ 仮想Framesetを構築し、名前付きフレームにログイン画面を召喚します...")
        driver.execute_script(f"""
            document.open();
            document.write('<html><head><title>JKK_REPRO</title></head>');
            document.write('<frameset rows="*">');
            document.write('<frame name="main" id="main" src="{LOGIN_TARGET}">');
            document.write('</frameset></html>');
            document.close();
        """)
        
        # ロードをじっくり待つ
        time.sleep(15)

        # 構築したフレーム 'main' に切り替える
        try:
            driver.switch_to.frame("main")
            log(f"🔎 フレーム内 Title: {driver.title}")
            
            # ログインフォーム（ID/PASS）を探索
            u_tags = driver.find_elements(By.NAME, "uid")
            p_tags = driver.find_elements(By.XPATH, "//input[@type='password']")
            
            if u_tags and p_tags:
                log("🎯 ついにログインフォーム（生身）を捕捉しました！")
                u_tags[0].send_keys(os.environ.get("JKK_ID"))
                p_tags[0].send_keys(os.environ.get("JKK_PASSWORD"))
                
                # 送信（画像ボタンやsubmitを網羅）
                btn = driver.find_elements(By.XPATH, "//input[@type='image'] | //img[contains(@src, 'login')] | //input[@type='submit']")
                if btn:
                    btn[0].click()
                else:
                    p_tags[0].submit()
                
                log("🚀 ログイン情報を送信。成功を祈ります。")
                time.sleep(10)
                log(f"送信後のURL: {driver.current_url}")
            else:
                log(f"🚨 フォーム未検出。タイトル: {driver.title}")
                log("--- フレーム内のソース（冒頭） ---")
                log(driver.page_source[:500])

        except Exception as fe:
            log(f"❌ フレーム遷移エラー: {fe}")

    except Exception as e:
        log(f"❌ 致命的エラー: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
