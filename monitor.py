import sys
import os
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def main():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1200') # 高さを少し広げる
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)
    
    try:
        # 手順1: トップページ
        log("🚪 手順1: 公社公式サイトへアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        time.sleep(7) # 読み込みを長めに待機

        # 手順2: 「JKKねっと」へのリンクを、文字やhrefで徹底的に探す
        log("🔍 手順2: 『JKKねっと』への入り口を物理探索中...")
        
        # 邪魔なポップアップやCookieバナーがある場合、JSで無視して要素を取得
        links = driver.find_elements(By.XPATH, "//a[contains(text(), 'JKKねっと') or contains(@href, 'jkknet')]")
        
        if links:
            target_link = links[0]
            log(f"🎯 入り口を発見しました。クリックします。")
            # 通常のクリックではなくJSで強制発火（上に何か重なっていても通る）
            driver.execute_script("arguments[0].click();", target_link)
        else:
            log("🚨 リンクが見つかりません。直接玄関を試みますが、くじらのリスクがあります。")
            driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/")
        
        time.sleep(7)

        # 手順3: ログインボタンの探索（ここでもJS実行を優先）
        log("🔍 手順3: ログインボタンを探索")
        try:
            # ページ内の「ログイン」という文字を持つaタグ、またはmypageLogin関数を持つ要素
            login_candidates = driver.find_elements(By.XPATH, "//*[contains(@onclick, 'mypageLogin') or contains(text(), 'ログイン')]")
            
            if login_candidates:
                log("🎯 ログインボタン発見。実行します。")
                driver.execute_script("arguments[0].click();", login_candidates[0])
            else:
                # 最終手段：直接JS関数を叩く
                log("⌨️ 直接JavaScript関数(mypageLogin)を実行します。")
                driver.execute_script("mypageLogin();")
        except Exception as e:
            log(f"⚠️ ログインボタン操作失敗: {e}")

        time.sleep(7)

        # 別窓・フレーム対応
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            log("📑 ログインウィンドウに切り替え完了")

        # 手順4: ID/PW投入
        log("⌨️ 手順4: IDとPWを投入")
        def attempt_input():
            try:
                u = driver.find_element(By.NAME, "uid")
                p = driver.find_element(By.NAME, "passwd")
                u.send_keys(os.environ.get("JKK_ID"))
                p.send_keys(os.environ.get("JKK_PASSWORD"), Keys.ENTER)
                return True
            except:
                return False

        if not attempt_input():
            # フレームを探す
            frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(frames)):
                driver.switch_to.frame(i)
                if attempt_input():
                    log(f"🎯 第{i}フレームで入力成功")
                    break
                driver.switch_to.default_content()

        log("⏳ 処理待ち(15秒)...")
        time.sleep(15)
        
        log(f"📍 最終URL: {driver.current_url}")
        if "mypageMenu" in driver.current_url:
            log("🎉 ついに成功しました！")
            requests.post(os.environ["DISCORD_WEBHOOK_URL"], json={"content": "✅ **JKKログイン成功！**"})
        else:
            log(f"💀 失敗。タイトル: {driver.title}")
            driver.save_screenshot("final_check.png")

    except Exception as e:
        log(f"❌ 重大エラー: {e}")
        driver.save_screenshot("crash_report.png")
    finally:
        driver.quit()
        log("🏁 終了")
