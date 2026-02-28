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

def setup_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,1024')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    options.add_argument('--lang=ja-JP')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = None
    try:
        driver = setup_driver()
        
        log("🚪 玄関ページにアクセス中...")
        driver.get(START_URL)
        time.sleep(8)
        
        # 【最重要】レトロサイトの「別窓開き」を封じ、同じタブで開かせる
        log("💉 ポップアップブロックを回避するスクリプトを注入...")
        driver.execute_script("""
            window.open = function(url) {
                window.location.href = url;
                return false;
            };
        """)

        log("🖱️ ログイン処理を開始...")
        # 直接 mypageLogin を叩くが、上の書き換えにより「今の画面」で遷移する
        driver.execute_script("if(typeof mypageLogin === 'function'){ mypageLogin(); }")
        
        log("⏳ 遷移を待機（15秒）...")
        time.sleep(15) 

        log(f"DEBUG: 現在のURL: {driver.current_url}")
        log(f"DEBUG: ページタイトル: '{driver.title}'")

        # もしこれでおわびが消えれば、ID/PASS入力画面がフレーム内に出現します
        if "おわび" not in driver.title:
            log("🎉 突破成功！ログインフォームを探します。")
            # --- ログインフォーム入力ロジック ---
            # フレームを再帰的に探して ID/PASS を入れる
            def fill_login(d):
                pws = d.find_elements(By.XPATH, "//input[@type='password']")
                if pws:
                    log("⌨️ パスワード欄を発見。入力します。")
                    uids = d.find_elements(By.XPATH, "//input[contains(@name, 'uid')]")
                    if uids: uids[0].send_keys(os.environ.get("JKK_ID"))
                    pws[0].send_keys(os.environ.get("JKK_PASSWORD"))
                    pws[0].submit()
                    return True
                
                fms = d.find_elements(By.TAG_NAME, "frame") + d.find_elements(By.TAG_NAME, "iframe")
                for i in range(len(fms)):
                    try:
                        d.switch_to.frame(i)
                        if fill_login(d): return True
                        d.switch_to.parent_frame()
                    except: continue
                return False
            
            fill_login(driver)
            time.sleep(5)
            log(f"✅ ログイン後のURL: {driver.current_url}")
        else:
            log("🚨 まだおわび画面です。別窓ではなくURL直行を試します。")
            driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin")
            time.sleep(10)

    except Exception as e:
        log(f"❌ エラー: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
