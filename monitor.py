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
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = None
    try:
        driver = setup_driver()
        
        log("🚪 玄関ページにアクセス...")
        driver.get(START_URL)
        time.sleep(10)
        
        # --- レトロサイト攻略の「核」：ウィンドウ名の偽装 ---
        log("💉 ウィンドウ名を固定し、window.open をカレント遷移にフックします...")
        driver.execute_script("""
            // ウィンドウ自体に名前を付ける（これがレトロサイトのチェック対象）
            window.name = "JKKNET_WINDOW"; 
            
            // window.openが呼ばれたら、今の画面で開きつつ、名前を維持する
            window.open = function(url, name, features) {
                console.log('Opening: ' + url + ' with name: ' + name);
                if(name) window.name = name; 
                window.location.href = url;
                return window;
            };
        """)
        
        log("🖱️ ログイン関数を実行...")
        driver.execute_script("if(window.mypageLogin){ mypageLogin(); }")
        
        time.sleep(20) # 遷移とJS実行をじっくり待つ

        log(f"DEBUG: 現在のURL: {driver.current_url}")
        log(f"DEBUG: タイトル: {driver.title}")
        log(f"DEBUG: ウィンドウ名: {driver.execute_script('return window.name;')}")

        # フォーム探索（全フレーム）
        def find_and_fill(d):
            # ID/PASSを探す（name='uid'、type='password'）
            u = d.find_elements(By.NAME, "uid")
            p = d.find_elements(By.XPATH, "//input[@type='password']")
            if u and p:
                log("🎯 ついにログインフォームを捕捉しました！")
                u[0].send_keys(os.environ.get("JKK_ID"))
                p[0].send_keys(os.environ.get("JKK_PASSWORD"))
                btn = d.find_elements(By.XPATH, "//input[@type='image'] | //img[contains(@src, 'login')] | //input[@type='submit']")
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

        if not find_and_fill(driver):
            log("🚨 フォーム未検出。おわびが続く場合は、直接URLを叩いて名前を維持します...")
            driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin")
            time.sleep(10)
            find_and_fill(driver)

    except Exception as e:
        log(f"❌ エラー: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
