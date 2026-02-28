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

def notify_discord(message):
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if url:
        try:
            requests.post(url, json={"content": message}, timeout=10)
            log("📢 Discord通知を送信しました。")
        except Exception as e:
            log(f"⚠️ Discord通知失敗: {e}")

def try_login(driver):
    u_fields = driver.find_elements(By.NAME, "uid")
    p_fields = driver.find_elements(By.NAME, "passwd")
    if u_fields and p_fields:
        log("🔑 フォームを発見。入力を開始します。")
        u_fields[0].send_keys(os.environ.get("JKK_ID"))
        p_fields[0].send_keys(os.environ.get("JKK_PASSWORD"))
        time.sleep(1)
        p_fields[0].send_keys(Keys.ENTER)
        return True
    return False

def main():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,1024')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        log("🚪 手順1: 玄関(TOP)にアクセス")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/")
        time.sleep(5)

        log("🔍 手順2: ログインボタンを探索")
        found_btn = None
        xpath_list = [
            "//a[contains(@onclick, 'mypageLogin')]",
            "//area[contains(@onclick, 'mypageLogin')]",
            "//img[contains(@src, 'login')]/..",
            "//a[contains(text(), 'ログイン')]"
        ]
        
        for xpath in xpath_list:
            btns = driver.find_elements(By.XPATH, xpath)
            if btns:
                found_btn = btns[0]
                break

        if found_btn:
            log("👉 ボタンをクリックしてログインページへ遷移します")
            driver.execute_script("arguments[0].scrollIntoView(true);", found_btn)
            driver.execute_script("arguments[0].click();", found_btn)
            time.sleep(5)
        else:
            log("🚨 ログインボタンが見つかりませんでした。スクショを保存します。")
            driver.save_screenshot("no_login_button.png")
            return

        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            log(f"📑 新しい窓に切り替えました: {driver.current_url}")

        log("🔍 手順3: ログインフォームを確認します")
        success = False
        if try_login(driver):
            success = True
        else:
            frames = driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
            for i in range(len(frames)):
                driver.switch_to.frame(i)
                if try_login(driver):
                    log(f"🎯 第{i}フレームでフォームを発見")
                    success = True
                    break
                driver.switch_to.default_content()

        if success:
            log("⏳ ログイン処理の完了を待機（10秒）...")
            time.sleep(10)
            
            # 【重要】成功・失敗に関わらず、解析のためにHTMLを保存
            page_filename = "after_login.html" if "マイページ" in driver.title or "ログアウト" in driver.page_source else "failed_page.html"
            with open(page_filename, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            log(f"💾 ページソースを {page_filename} に保存しました。")

            if "マイページ" in driver.title or "ログアウト" in driver.page_source:
                log("🎉 ログイン成功！")
                notify_discord(f"✅ JKKログイン成功！\nURL: {driver.current_url}")
            else:
                log(f"💀 ログイン失敗。タイトル: {driver.title}")
                driver.save_screenshot("login_failed.png")
        else:
            log("🚨 フォームが見つかりませんでした（くじらページ等の可能性）")
            driver.save_screenshot("no_form.png")

    except Exception as e:
        log(f"❌ エラー: {e}")
        driver.save_screenshot("error.png")
    finally:
        driver.quit()
        log("🏁 終了")

if __name__ == "__main__":
    main()
