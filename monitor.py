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

# 玄関URL
START_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/"

def setup_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,1024')
    # 言語設定を「日本語」に固定（Shift-JISサイトには必須）
    options.add_argument('--lang=ja-JP')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = None
    try:
        driver = setup_driver()
        
        log("🚪 玄関ページへ正規アクセス...")
        driver.get(START_URL)
        time.sleep(10) # 完全に読み込みが終わるまで待つ
        
        log("🖱️ サイト内関数 'mypageLogin' を直接呼び出します...")
        # Seleniumのクリックではなく、ブラウザ内部で定義されているはずの関数を叩く
        # これにより、サイトが期待する「正しい遷移パラメータ」が生成されます
        driver.execute_script("if(window.mypageLogin){ mypageLogin(); }")
        
        # 遷移（別窓またはフレーム生成）をじっくり待つ
        time.sleep(20)

        # レトロサイト特有の「窓が切り替わったか」のチェック
        if len(driver.window_handles) > 1:
            log("🪟 別ウィンドウを検知。切り替えます。")
            driver.switch_to.window(driver.window_handles[-1])

        log(f"DEBUG: URL={driver.current_url} Title='{driver.title}'")

        def deep_scan(d):
            # ID/PASS入力欄の探索
            inputs = d.find_elements(By.NAME, "uid") + d.find_elements(By.XPATH, "//input[@type='password']")
            if inputs:
                return True
            # フレーム探索
            fms = d.find_elements(By.TAG_NAME, "frame") + d.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(fms)):
                try:
                    d.switch_to.frame(i)
                    if deep_scan(d): return True
                    d.switch_to.parent_frame()
                except: continue
            return False

        if deep_scan(driver):
            log("🎯 ログインフォームに到達しました！")
            # 入力処理...
        else:
            log("🚨 依然としてフォームが見つかりません。")
            # ソースの末尾まで取得できているか確認
            log(f"ソース末尾: {driver.page_source[-200:]}")

    except Exception as e:
        log(f"❌ エラー: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
