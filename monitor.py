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
    if url and "✅" in message:
        try:
            requests.post(url, json={"content": message}, timeout=10)
            log("📢 Discord通知を送信しました。")
        except:
            pass

def main():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1280,1024')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # 手順1: サイトのルートから入る（リファラ対策）
        log("🚪 手順1: 公社サイトのルートにアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        time.sleep(3)

        # 手順2: ログインページへ（直接移動ではなく、遷移を意識）
        log("🚪 手順2: ログインページへ移動")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin")
        time.sleep(5)

        # ページ内にフレームがあるか確認し、あれば中に入る
        frames = driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
        if frames:
            log(f"📦 {len(frames)}個のフレームを検知。最初のフレームに切り替えます。")
            driver.switch_to.frame(0)

        # 手順3: 入力欄の特定と入力（ここを強化！）
        log("🔍 手順3: IDとPWの入力欄を厳密に特定します")
        
        # ID欄の特定 (name='uid' または type='text')
        id_field = driver.find_element(By.NAME, "uid")
        # PW欄の特定 (name='passwd' または type='password')
        pw_field = driver.find_element(By.NAME, "passwd")

        if id_field and pw_field:
            # 1. 念のため既存の文字を全削除
            id_field.clear()
            pw_field.clear()
            
            # 2. 値の投入（ Secrets から正確に取得）
            jkk_id = os.environ.get("JKK_ID")
            jkk_pw = os.environ.get("JKK_PASSWORD")
            
            log(f"⌨️ ID欄に入力します（長さ: {len(jkk_id)}文字）")
            id_field.send_keys(jkk_id)
            
            log(f"⌨️ PW欄に入力します（長さ: {len(jkk_pw)}文字）")
            pw_field.send_keys(jkk_pw)
            
            time.sleep(1)
            
            # 3. Enterではなく「ログイン」ボタンを明示的に探してクリックしてみる
            log("🖱️ ログイン実行ボタンを探索中...")
            login_btn = driver.find_elements(By.XPATH, "//input[@type='image']|//img[contains(@src,'login')]|//input[@type='submit']")
            
            if login_btn:
                log("🎯 実行ボタンをクリックします")
                driver.execute_script("arguments[0].click();", login_btn[0])
            else:
                log("⌨️ ボタンが見つからないためEnterキーで代用します")
                pw_field.send_keys(Keys.ENTER)
            
            time.sleep(10)
            
            # 最終確認
            log(f"✅ 遷移後のタイトル: {driver.title}")
            with open("after_action.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)

            if "マイページ" in driver.title or "ログアウト" in driver.page_source:
                log("🎉 成功！")
                notify_discord("✅ JKKログイン成功！")
            else:
                log("💀 ログインできませんでした。入力ミスか、ページが弾かれています。")
                driver.save_screenshot("input_check.png")
        else:
            log("🚨 入力欄が見つかりません。")

    except Exception as e:
        log(f"❌ エラー: {e}")
        driver.save_screenshot("fatal_error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
