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
LOGIN_JSP = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"

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
        
        # 1. まず玄関でCookieを貰う
        log("🚪 玄関ページにアクセス中...")
        driver.get(START_URL)
        time.sleep(5)
        
        # 2. 【秘奥義】JavaScriptで「名前付きの別窓」を無理やり作り出し、そこにログイン画面を召喚する
        log("🪄 偽装ウィンドウ 'JKK_WIN' を生成してログイン画面を呼び出します...")
        driver.execute_script(f"window.open('{LOGIN_JSP}', 'JKK_WIN');")
        time.sleep(5)
        
        # 3. 生成した 'JKK_WIN' ウィンドウに切り替える
        handles = driver.window_handles
        if len(handles) > 1:
            driver.switch_to.window(handles[1])
            log(f"🪟 ウィンドウ切り替え成功: {driver.execute_script('return window.name;')}")
        
        # 4. 読み込みを待機（JSPが名前を検知してフォームを吐き出すのを待つ）
        log("⏳ フォームの生成を待機（20秒）...")
        time.sleep(20)
        
        log(f"DEBUG: 現在のURL: {driver.current_url}")
        log(f"DEBUG: ページタイトル: '{driver.title}'")

        def login_process(d):
            # 全フレーム（Frameset対応）から入力欄を徹底捜索
            inputs = d.find_elements(By.NAME, "uid")
            passes = d.find_elements(By.XPATH, "//input[@type='password']")
            
            if inputs and passes:
                log("🎯 ついにログインフォームを捕捉しました！")
                inputs[0].send_keys(os.environ.get("JKK_ID"))
                passes[0].send_keys(os.environ.get("JKK_PASSWORD"))
                
                # 送信ボタン（画像ボタンかsubmit）
                btn = d.find_elements(By.XPATH, "//input[@type='image'] | //img[contains(@src, 'login')] | //input[@type='submit']")
                if btn:
                    btn[0].click()
                else:
                    passes[0].submit()
                return True
            
            # 再帰的に全フレームを掘る
            frames = d.find_elements(By.TAG_NAME, "frame") + d.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(frames)):
                try:
                    d.switch_to.frame(i)
                    if login_process(d): return True
                    d.switch_to.parent_frame()
                except: continue
            return False

        if login_process(driver):
            log("🚀 ログイン情報を送信しました！")
            time.sleep(10)
            log(f"送信後のURL: {driver.current_url}")
            log(f"送信後のTitle: {driver.title}")
            # ここで「空室検索」画面へのリンクを探すロジックへ続く...
        else:
            log("🚨 依然としてフォームが見つかりません。")
            log(f"最終ソースの末尾: {driver.page_source[-300:]}")

    except Exception as e:
        log(f"❌ 致命的エラー: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
