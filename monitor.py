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
LOGIN_ENDPOINT = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"

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
        
        log("🚪 玄関ページにアクセス（Cookieの基点を確立）...")
        driver.get(START_URL)
        time.sleep(5)
        
        # --- 秘奥義：AJAXによる「本丸」の強制吸い出し ---
        log("💉 玄関ページを維持したまま、ログイン画面をAJAXで吸い出します...")
        script = f"""
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '{LOGIN_ENDPOINT}', false); // 同期通信で取得
            xhr.send(null);
            document.open();
            document.write(xhr.responseText); // 取得した内容をそのまま画面に上書き
            document.close();
            window.name = "JKK_WIN"; // レトロな名前チェック対策
        """
        driver.execute_script(script)
        
        time.sleep(10)
        log(f"🔎 ページ上書き後のTitle: {driver.title}")

        # フォームの探索と入力（フレームを考慮）
        def find_and_fill(d):
            u = d.find_elements(By.NAME, "uid")
            p = d.find_elements(By.XPATH, "//input[@type='password']")
            if u and p:
                log("🎯 ついに生身のフォームを捕捉！")
                u[0].send_keys(os.environ.get("JKK_ID"))
                p[0].send_keys(os.environ.get("JKK_PASSWORD"))
                btn = d.find_elements(By.XPATH, "//input[@type='image']|//img[contains(@src,'login')]")
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
            log("🚀 ログイン情報を送信しました！")
            time.sleep(10)
            log(f"最終URL: {driver.current_url}")
        else:
            log("🚨 依然としてフォームがありません。おわびの呪縛が強固です。")
            log(f"ソース断片: {driver.page_source[:500]}")

    except Exception as e:
        log(f"❌ 時代遅れのエラー: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
