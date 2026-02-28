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
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def main():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # 手順1: 大本のトップページ（ここからすべてが始まる）
        log("🚪 手順1: 公社公式サイト(www)へアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        time.sleep(5)

        # 手順2: 「住宅をお探しの方」メニューをホバーして展開
        log("🔍 手順2: メニューをホバーして『JKKねっと』を探します")
        menu_trigger = driver.find_element(By.XPATH, "//span[contains(text(), '住宅をお探しの方')]/..")
        actions = ActionChains(driver)
        actions.move_to_element(menu_trigger).perform()
        time.sleep(2)

        # 手順3: 展開されたメニューから「JKKねっと」をクリック
        jkk_entrance = driver.find_element(By.XPATH, "//a[contains(@href, 'jkknet')]")
        log(f"👉 リンク発見: {jkk_entrance.text}。クリックして遷移します。")
        driver.execute_script("arguments[0].click();", jkk_entrance)
        time.sleep(5)

        # 手順4: 遷移後のページでログインボタンを物理探索
        log("🔍 手順4: ページ内のログインボタンを探索")
        login_btn = driver.find_element(By.XPATH, "//*[@onclick[contains(.,'mypageLogin')] or contains(@href,'mypageLogin')]")
        log("🎯 ボタン発見。物理的にクリックしてログイン画面を呼び出します。")
        driver.execute_script("arguments[0].click();", login_btn)
        time.sleep(5)

        # 別窓が開いた場合に備えてハンドルを移動
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            log(f"📑 ログインウィンドウに切り替えました: {driver.current_url}")

        # 手順5: ID/PWの投入（ここで『くじら』が出ていないことを祈る！）
        log("⌨️ 手順5: IDとPWを投入します")
        
        # フレーム内にフォームがある場合を想定した関数
        def input_credentials():
            u = driver.find_elements(By.NAME, "uid")
            p = driver.find_elements(By.NAME, "passwd")
            if u and p:
                u[0].clear()
                u[0].send_keys(os.environ.get("JKK_ID"))
                p[0].clear()
                p[0].send_keys(os.environ.get("JKK_PASSWORD"), Keys.ENTER)
                return True
            return False

        if not input_credentials():
            # フレームを探す
            frames = driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
            for i in range(len(frames)):
                driver.switch_to.frame(i)
                if input_credentials():
                    log(f"🎯 第{i}フレーム内で入力に成功しました")
                    break
                driver.switch_to.default_content()
        
        log("⏳ ログイン処理の完了を待ちます（15秒）...")
        time.sleep(15)

        # 手順6: 最終確認（マイページURLに到達したか）
        target_url_part = "mypageMenu"
        log(f"📍 最終URL: {driver.current_url}")
        
        if target_url_part in driver.current_url or "マイページ" in driver.title:
            log("🎉 ついに突破！ログイン成功です！")
            requests.post(os.environ["DISCORD_WEBHOOK_URL"], json={"content": "✅ **JKKログイン成功！** ついに『くじら』を倒しました。"})
        else:
            log("💀 ログイン失敗。現在の画面を保存します。")
            driver.save_screenshot("login_failed_final.png")
            with open("failed_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        driver.save_screenshot("crash_debug.png")
    finally:
        driver.quit()
        log("🏁 終了")
