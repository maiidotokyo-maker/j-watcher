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
        time.sleep(5)
        
        # --- 秘奥義：レトロ・ウィンドウ・エミュレーション ---
        log("💉 ターゲットウィンドウを偽装構築中...")
        driver.execute_script("""
            // 1. 自分自身の名前を、JKKが期待する名前に固定
            window.name = "JKK_WIN"; 
            
            // 2. window.open をフックして、別窓ではなく「今の窓」で開かせる
            // その際、無理やり名前を維持させる
            window.open = function(url, name, features) {
                window.name = name || "JKK_WIN";
                window.location.href = url;
                return window;
            };
        """)
        
        log("🖱️ ログインボタン起動（mypageLogin実行）...")
        driver.execute_script("if(window.mypageLogin){ mypageLogin(); }")
        
        # 遷移とレンダリングを最大30秒待つ
        log("⏳ ページ生成を待機中（最大30秒）...")
        for i in range(6):
            time.sleep(5)
            log(f"DEBUG: URL={driver.current_url} Title='{driver.title}'")
            if "おわび" not in driver.title and driver.title != "":
                break

        # フレームの徹底捜索と入力
        def search_and_login(d):
            # ID/PASS入力欄を探す
            u = d.find_elements(By.NAME, "uid")
            p = d.find_elements(By.XPATH, "//input[@type='password']")
            if u and p:
                log("🎯 ついに生身のフォームを捉えました！")
                u[0].send_keys(os.environ.get("JKK_ID"))
                p[0].send_keys(os.environ.get("JKK_PASSWORD"))
                # 送信ボタン（画像ボタン）をクリック
                btn = d.find_elements(By.XPATH, "//input[@type='image'] | //img[contains(@src, 'login')]")
                if btn: btn[0].click()
                else: p[0].submit()
                return True
            
            # 子フレームを再帰的に探す
            fms = d.find_elements(By.TAG_NAME, "frame") + d.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(fms)):
                try:
                    d.switch_to.frame(i)
                    if search_and_login(d): return True
                    d.switch_to.parent_frame()
                except: continue
            return False

        if search_and_login(driver):
            log("🚀 ログイン情報を送信しました！")
            time.sleep(10)
            log(f"最終到達URL: {driver.current_url}")
        else:
            log("🚨 フォームが見つかりません。")
            # 最後の悪あがき：ページ全体をキャプチャして内容を確認
            log(f"最終Title: {driver.title}")
            log(f"Page Source Preview: {driver.page_source[:500]}")

    except Exception as e:
        log(f"❌ エラー: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
