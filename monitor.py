import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def send_discord_notification(message):
    """Discordに通知を送信する関数"""
    data = {
        "content": message
    }
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        response.raise_for_status()
        log("📢 Discord通知を送信しました。")
    except requests.exceptions.RequestException as e:
        log(f"⚠️ Discord通知の送信に失敗しました: {e}")

def main():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    
    options = Options()
    options.add_argument("--headless")  # ヘッドレスモードを一度無効にしてみる
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        log("🚪 手順1: サイトへアクセス")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        
        # 1. ログイン用の別窓が開くのを待つ
        WebDriverWait(driver, 30).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        log("🪟 ログインウィンドウへ切り替え完了")

        # 2. iframeの中身が読み込まれるまで待機
        wait = WebDriverWait(driver, 30)
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, "iframe")))
        log("🖼️ iframe内へ潜入成功")

        # 3. ID入力欄が見えるまで待ってから入力
        user_input = wait.until(EC.visibility_of_element_located((By.NAME, "user_id")))
        pass_input = driver.find_element(By.NAME, "password")
        
        log("⌨️ ID/PWを入力中...")
        user_input.clear()
        user_input.send_keys(JKK_ID)
        pass_input.clear()
        pass_input.send_keys(JKK_PASSWORD)
        
        # 4. ログイン実行
        log("🚀 ログインボタンをクリックします")
        driver.execute_script("submitNext();")
        
        # --- ログイン後の遷移確認 ---
        driver.switch_to.default_content()
        time.sleep(15)  # しばらく待つ
        driver.save_screenshot("login_attempt_result.png")
        log("📸 実行結果を『login_attempt_result.png』に保存しました。")
        
        # もし画面に「条件から検索」があれば、物件検索を開始
        # ここで空き物件があるかをチェック（仮に見つかった場合）
        new_property_found = True  # 仮定: 物件が見つかった場合
        
        if new_property_found:
            message = "🆕 新しい物件が見つかりました！詳細を確認してください。"
            send_discord_notification(message)

    except Exception as e:
        log(f"⚠️ エラー発生: {e}")
        driver.save_screenshot("fatal_error_final.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
