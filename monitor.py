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
        
        # 1. まず普通にアクセスして、クッキーを拾う
        log("🚪 セッション初期化中...")
        driver.get(START_URL)
        time.sleep(5)
        
        # 2. 【最重要】レトロサイトが期待する「フレーム名」を強制的に作り出す
        # JKKがよく使う 'main', 'contents', 'menu' といった名前を網羅したダミーを作る
        log("🪄 レトロ・フレームセットを仮想構築します...")
        driver.execute_script(f"""
            document.write('<html><frameset cols="20%,*">');
            document.write('<frame name="leftFrame" src="about:blank">');
            document.write('<frame name="mainFrame" id="mainFrame" src="{TARGET_JSP}">');
            document.write('</frameset></html>');
            document.close();
        """)
        
        # 3. フレームの展開を待つ
        time.sleep(15)
        
        # 4. 構築した 'mainFrame' の中に潜る
        try:
            driver.switch_to.frame("mainFrame")
            log(f"🔎 仮想フレーム内を探索中... Title: {driver.title}")
            
            # ログインフォーム（ID/PASS）を探す
            u_tags = driver.find_elements(By.NAME, "uid")
            p_tags = driver.find_elements(By.XPATH, "//input[@type='password']")
            
            if u_tags and p_tags:
                log("🎯 ついに、生身のログインフォームを捕捉しました！")
                u_tags[0].send_keys(os.environ.get("JKK_ID"))
                p_tags[0].send_keys(os.environ.get("JKK_PASSWORD"))
                
                # 画像ボタン等に対応
                btn = driver.find_element(By.XPATH, "//img[contains(@src, 'login')] | //input[@type='submit'] | //input[@type='image']")
                btn.click()
                
                log("🚀 ログイン情報を送信。成功を祈ります。")
                time.sleep(10)
                log(f"最終URL: {driver.current_url}")
            else:
                log(f"🚨 フォーム未検出。タイトル: {driver.title}")
                # おわびが続くなら名前が違う可能性があるため全フレーム名を出力
                log("--- 現在のフレーム内ソース ---")
                log(driver.page_source[:500])

        except Exception as fe:
            log(f"❌ フレーム遷移エラー: {fe}")

    except Exception as e:
        log(f"❌ 致命的エラー: {e}")
    finally:
        if driver: driver.quit()
        log("🏁 スクリプトを終了します。")

if __name__ == "__main__":
    main()
