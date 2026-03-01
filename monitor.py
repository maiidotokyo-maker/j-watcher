import os
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 環境変数
JKK_ID = os.environ.get("JKK_ID")
JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def send_discord(message, file_path=None):
    """Discordへの通知送信 (改善点: エラーハンドリングの強化)"""
    if not DISCORD_WEBHOOK_URL:
        return
    try:
        payload = {"content": message}
        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as f:
                requests.post(DISCORD_WEBHOOK_URL, data=payload, files={"file": f})
        else:
            requests.post(DISCORD_WEBHOOK_URL, json=payload)
        log("📢 Discord通知を送信しました。")
    except Exception as e:
        log(f"⚠️ Discord送信失敗: {e}")

def solve_login(driver):
    """レトロなiframe迷宮を突破するログイン処理"""
    wait = WebDriverWait(driver, 20) # 改善点: 明示的待機
    
    # 1. ログイン窓への遷移 (改善点: ウィンドウ管理の厳格化)
    base_handles = driver.window_handles
    wait.until(lambda d: len(d.window_handles) > 1)
    driver.switch_to.window(driver.window_handles[-1])
    log("🪟 ログイン窓を捕捉しました。")

    # 2. iframeの階層を突破
    log("🕵️ iframe階層を探索中...")
    # 1段目のフレーム待機とスイッチ
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, "iframe")))
    
    # レトロサイト特有の「入れ子」をチェック
    sub_frames = driver.find_elements(By.TAG_NAME, "iframe")
    if sub_frames:
        driver.switch_to.frame(sub_frames[0])
        log("⛏️ 深層のiframeへ潜入しました。")

    # 3. 入力 (改善点: element_to_be_clickableを使用)
    user_field = wait.until(EC.element_to_be_clickable((By.NAME, "user_id")))
    pass_field = driver.find_element(By.NAME, "password")
    
    log("⌨️ ID/PWを入力しています...")
    user_field.send_keys(JKK_ID)
    pass_field.send_keys(JKK_PASSWORD)
    
    # 4. 物理的な送信
    login_btn = driver.find_element(By.XPATH, "//a[contains(@onclick, 'submitNext')]")
    driver.execute_script("arguments[0].click();", login_btn)
    log("🚀 ログイン情報を送信しました。")

def main():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # 改善点: webdriver_managerによる自動管理
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        log("🚪 手順1: サイトへアクセス")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        
        # ログイン実行
        solve_login(driver)
        
        # ログイン後の遷移待機
        time.sleep(10)
        driver.switch_to.default_content()
        
        # 成功判定 (マイページ特有の要素を探す)
        if "mypage" in driver.current_url.lower() or len(driver.find_elements(By.ID, "search-button")) > 0:
            log("✅ ログイン成功！")
            driver.save_screenshot("success_mypage.png")
            send_discord("✅ JKKログイン成功！世田谷区の監視を開始できます。", "success_mypage.png")
            # ここに世田谷区検索ロジックを追加可能
        else:
            raise Exception("ログイン後の期待されるページに遷移しませんでした。")

    except Exception as e:
        log(f"⚠️ エラー発生: {e}")
        error_img = "error_evidence.png"
        driver.save_screenshot(error_img)
        # 改善点: Discordへのエラー通知（画像付き）
        send_discord(f"❌ 【JKK監視エラー】\n内容: {e}", error_img)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
