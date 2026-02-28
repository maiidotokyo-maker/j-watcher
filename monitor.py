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

# ログ出力時のエンコーディング設定
sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def notify_discord(message):
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if url:
        try:
            requests.post(url, json={"content": message}, timeout=10)
            log("📢 Discord通知を送信しました。")
        except Exception as e:
            log(f"⚠️ Discord通知失敗: {e}")

def main():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # 画面サイズが小さいとメニューが隠れるため、広めに設定
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # 手順1: 公式サイトのトップから入る（セッション確立のため必須）
        log("🚪 手順1: 公社公式サイト(www)へアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        time.sleep(5)

        # 手順2: 「住宅をお探しの方」メニューをホバーして展開
        log("🔍 手順2: メニューを展開して『JKKねっと』を探索")
        try:
            menu_trigger = driver.find_element(By.XPATH, "//span[contains(text(), '住宅をお探しの方')]/..")
            actions = ActionChains(driver)
            actions.move_to_element(menu_trigger).perform()
            time.sleep(2)
            
            # 展開されたメニューからJKKねっとへのリンクをクリック
            jkk_link = driver.find_element(By.XPATH, "//a[contains(@href, 'jkknet')]")
            log(f"👉 リンク発見: {jkk_link.text}。クリックして遷移します。")
            driver.execute_script("arguments[0].click();", jkk_link)
        except Exception as e:
            log(f"⚠️ メニュー操作に失敗。直接玄関(jkknet/pc/)へ移動します: {e}")
            driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/")
        
        time.sleep(5)

        # 手順3: ログインボタンを物理探索してクリック
        log("🔍 手順3: ページ内のログインボタンを探索")
        # 直接mypageLogin関数を呼ぶか、ボタンを特定
        xpath_login = "//*[@onclick[contains(.,'mypageLogin')] or contains(@href,'mypageLogin')]"
        login_btn = driver.find_element(By.XPATH, xpath_login)
        log("🎯 ログインボタンを発見。クリックしてログイン画面へ。")
        driver.execute_script("arguments[0].click();", login_btn)
        time.sleep(5)

        # 別窓が開いた場合、新しい窓へ切り替え
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            log(f"📑 ログインウィンドウに切り替え: {driver.current_url}")

        # 手順4: ID/PWの投入
        log("⌨️ 手順4: IDとPWを投入します")
        
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

        # メインコンテンツまたはフレーム内をスキャン
        if not input_credentials():
            frames = driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
            for i in range(len(frames)):
                driver.switch_to.frame(i)
                if input_credentials():
                    log(f"🎯 第{i}フレーム内でフォームを発見・入力しました")
                    break
                driver.switch_to.default_content()
        
        log("⏳ ログイン処理の完了を待機中（15秒）...")
        time.sleep(15)

        # 手順5: 最終確認（成功URL: .../service/mypageMenu）
        log(f"📍 最終URL: {driver.current_url}")
        log(f"📄 最終タイトル: {driver.title}")

        if "mypageMenu" in driver.current_url or "マイページ" in driver.title:
            log("🎉 ついに成功！ログインを突破しました！")
            notify_discord("✅ **JKKログイン成功！** ついに『くじら』を倒してマイページに到達しました。")
            # 成功時のHTMLを保存（空室検索ボタンの解析用）
            with open("after_login_success.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
        else:
            log("💀 ログイン失敗。")
            driver.save_screenshot("login_failed_final.png")
            with open("failed_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        driver.save_screenshot("crash_debug.png")
    finally:
        driver.quit()
        log("🏁 終了")

if __name__ == "__main__":
    main()
