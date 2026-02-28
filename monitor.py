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

def setup_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,1024')
    options.add_argument('--lang=ja-JP')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    # ポップアップブロックを完全に無効化する設定
    options.add_experimental_option("prefs", {"profile.default_content_settings.popups": 1})
    
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = None
    try:
        driver = setup_driver()
        
        log("🚪 玄関ページにアクセス...")
        driver.get(START_URL)
        time.sleep(10)
        
        # --- レトロサイト攻略の核：window.openのフック ---
        log("💉 window.open を無効化し、カレントウィンドウでの遷移に書き換えます...")
        driver.execute_script("""
            window.open = function(url, name, features) {
                console.log('Redirecting to: ' + url);
                window.location.href = url;
                return window;
            };
        """)
        
        log("🖱️ ログイン関数を実行...")
        driver.execute_script("if(window.mypageLogin){ mypageLogin(); }")
        
        # 遷移を待つ（ここが勝負）
        time.sleep(15)

        log(f"DEBUG: 現在のURL: {driver.current_url}")
        log(f"DEBUG: タイトル: {driver.title}")

        if "おわび" in driver.title:
            log("🚨 まだ『おわび』です。URL直撃に切り替えます...")
            driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin")
            time.sleep(10)

        # ログインフォームを全フレームから探す
        def find_and_fill(d):
            # name='uid' や type='password' を探す
            u = d.find_elements(By.NAME, "uid")
            p = d.find_elements(By.XPATH, "//input[@type='password']")
            if u and p:
                log("🎯 ついにログインフォームを捕捉！")
                u[0].send_keys(os.environ.get("JKK_ID"))
                p[0].send_keys(os.environ.get("JKK_PASSWORD"))
                # submit
                btn = d.find_elements(By.XPATH, "//input[@type='image'] | //img[contains(@src, 'login')]")
                if btn: btn[0].click()
                else: p[0].submit()
                return True
            
            fms = d.find_elements(By.TAG_NAME, "frame") + d.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(fms)):
                try:
                    d.switch_to.frame(i)
                    if find_and_fill(d): return True
                    d.switch_to.parent_frame()
                except: continue
            return False

        if find_and_fill(driver):
            log("✅ ログイン成功の兆し。送信完了。")
            time.sleep(10)
            log(f"最終URL: {driver.current_url}")
        else:
            log("❌ フォームがありませんでした。")

    except Exception as e:
        log(f"❌ エラー: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
