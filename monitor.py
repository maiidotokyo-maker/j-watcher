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
from webdriver_manager.chrome import ChromeDriverManager

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def main():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # 1. 公式サイトへ
        log("🚪 手順1: 公社公式サイト(www)へアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        time.sleep(10)

        # 2. 邪魔なバナーをJSで強制削除
        log("🧹 障害物（Cookieバナー等）を強制排除します")
        driver.execute_script("""
            var elements = document.querySelectorAll('.cc-window, .cookie-banner, #cookie-consent');
            for(var i=0; i<elements.length; i++){ elements[i].style.display='none'; }
        """)
        time.sleep(2)

        # 3. 「住宅をお探しの方」メニューから「JKKねっと」を文字で探してクリック
        log("🔍 手順2: 正規ルートのリンクを探索中...")
        # 画面上の「JKKねっと」という文字を頼りに探す
        try:
            target_link = driver.find_element(By.PARTIAL_LINK_TEXT, "JKKねっと")
            log(f"🎯 入り口発見: {target_link.text}")
            driver.execute_script("arguments[0].click();", target_link)
        except:
            log("⚠️ テキストで見つからないため、hrefから再探索")
            target_link = driver.find_element(By.XPATH, "//a[contains(@href, 'jkknet')]")
            driver.execute_script("arguments[0].click();", target_link)
        
        time.sleep(8)

        # 4. ログインボタン（mypageLogin）をJSで実行
        log("🔍 手順3: ログイン画面を呼び出します")
        driver.execute_script("mypageLogin();")
        time.sleep(8)

        # 5. 別窓対応
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            log("📑 ログイン画面にフォーカスしました")

        # 6. ID/PW投入（ここまできたら、おわびは出ないはず）
        log("⌨️ 手順4: IDとPWを入力")
        
        def fill():
            try:
                # 確実にフォームを待機
                u = driver.find_element(By.NAME, "uid")
                p = driver.find_element(By.NAME, "passwd")
                u.send_keys(os.environ.get("JKK_ID"))
                p.send_keys(os.environ.get("JKK_PASSWORD"), Keys.ENTER)
                return True
            except: return False

        if not fill():
            for frame in driver.find_elements(By.TAG_NAME, "frame"):
                driver.switch_to.frame(frame)
                if fill(): break
                driver.switch_to.default_content()

        log("⏳ 最終リダイレクト待ち...")
        time.sleep(15)
        
        # 7. 成功判定
        log(f"📍 最終URL: {driver.current_url}")
        if "mypageMenu" in driver.current_url or "マイページ" in driver.title:
            log("🎉 成功！完全突破しました！")
            if os.environ.get("DISCORD_WEBHOOK_URL"):
                requests.post(os.environ["DISCORD_WEBHOOK_URL"], json={"content": "✅ **JKKログイン成功！** 全ての障害を突破しました。"})
        else:
            log(f"💀 失敗。タイトル: {driver.title}")
            driver.save_screenshot("final_check.png")

    except Exception as e:
        log(f"❌ エラー: {e}")
        driver.save_screenshot("crash_report.png")
    finally:
        driver.quit()
        log("🏁 終了")
