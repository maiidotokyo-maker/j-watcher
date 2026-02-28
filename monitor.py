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
            log("📢 Discordに成功通知を送信しました！")
        except Exception as e:
            log(f"⚠️ Discord通知失敗: {e}")

def try_login(driver):
    u_fields = driver.find_elements(By.NAME, "uid")
    p_fields = driver.find_elements(By.NAME, "passwd")
    
    if u_fields and p_fields:
        log("🔑 フォーム発見。ID/PWを投入します。")
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
        log("🚪 玄関(TOP)アクセス")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/")
        time.sleep(3)

        log("🚪 ログインページ移動")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin")
        time.sleep(5)

        success = False
        if try_login(driver):
            success = True
        else:
            frames = driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
            for i, frame in enumerate(frames):
                driver.switch_to.frame(i)
                if try_login(driver):
                    success = True
                    break
                driver.switch_to.default_content()

        if success:
            time.sleep(10)
            # 成功判定
            if "マイページ" in driver.title or "ログアウト" in driver.page_source:
                log("🎉 ログイン成功！")
                notify_discord(f"✅ **JKKログイン成功！**\nURL: {driver.current_url}")
            else:
                log(f"💀 ログイン失敗（タイトル: {driver.title}）")
                driver.save_screenshot("login_failed.png")
                log("🖼️ スクリーンショットを保存しました: login_failed.png")
                # デバッグ用にソースも保存
                with open("failed_page.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
        else:
            log("🚨 フォームが見つかりませんでした")
            driver.save_screenshot("no_form.png")

    except Exception as e:
        log(f"❌ エラー: {e}")
        driver.save_screenshot("error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
