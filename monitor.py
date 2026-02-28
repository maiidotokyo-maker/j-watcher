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
    # レトロサイトが「本物のブラウザ」と誤認するUA
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def main():
    driver = None
    try:
        driver = setup_driver()
        
        log("🚪 玄関ページへアクセス...")
        driver.get(START_URL)
        time.sleep(10)
        
        # --- 秘奥義：window.openを「現在のタブでの遷移」に強制上書き ---
        log("💉 遷移ロジックをハック中...")
        driver.execute_script("""
            // レトロサイトの別窓起動を無効化し、今の画面で開かせる
            window.open = function(url) {
                window.location.replace(url);
                return window;
            };
            // フォームのtarget属性も自分自身に書き換える
            Array.from(document.getElementsByTagName('form')).forEach(f => f.target = '_self');
        """)
        
        log("🖱️ ログイン関数 mypageLogin() を実行...")
        driver.execute_script("if(window.mypageLogin){ mypageLogin(); }")
        
        # 遷移とレンダリングをじっくり待つ
        time.sleep(20)

        log(f"DEBUG: URL={driver.current_url} Title='{driver.title}'")

        # ログインフォーム（ID/PASS）を全フレームから再帰探索
        def find_and_fill(d):
            # name属性が uid や passwd であることを想定
            u = d.find_elements(By.NAME, "uid") + d.find_elements(By.ID, "uid")
            p = d.find_elements(By.XPATH, "//input[@type='password']")
            
            if u and p:
                log("🎯 ついにログインフォームを捕捉！")
                u[0].send_keys(os.environ.get("JKK_ID"))
                p[0].send_keys(os.environ.get("JKK_PASSWORD"))
                
                # 送信ボタン（画像ボタンが多い）
                btns = d.find_elements(By.XPATH, "//input[@type='image'] | //img[contains(@src, 'login')] | //input[@type='submit']")
                if btns:
                    btns[0].click()
                else:
                    p[0].submit()
                return True
            
            # 子フレームを掘る
            fms = d.find_elements(By.TAG_NAME, "frame") + d.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(fms)):
                try:
                    d.switch_to.frame(i)
                    if find_and_fill(d): return True
                    d.switch_to.parent_frame()
                except:
                    continue
            return False

        if find_and_fill(driver):
            log("🚀 ログイン情報を送信しました。")
            time.sleep(10)
            log(f"最終URL: {driver.current_url}")
        else:
            log("🚨 フォームが見つかりませんでした。おわび画面を直撃します...")
            driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin")
            time.sleep(10)
            find_and_fill(driver)

    except Exception as e:
        log(f"❌ エラー: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
