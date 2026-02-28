import sys
import os
import time
import random
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- ログ出力 ---
sys.stdout.reconfigure(encoding='utf-8')
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# --- 環境変数 ---
START_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/"
JKK_ID = os.environ.get("JKK_ID", "").strip()
JKK_PASS = os.environ.get("JKK_PASSWORD", "").strip()
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def setup_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def find_and_click_login_brute_force(driver):
    """
    全フレームを巡回し、ログインに関連しそうな要素を
    テキスト、属性、タグ名から徹底的に探してクリックする
    """
    # 探索対象のキーワード
    keywords = ["login", "ログイン", "mypage", "マイページ"]
    
    # 1. 現在の階層で要素を探す
    elements = driver.find_elements(By.XPATH, "//*[self::a or self::area or self::img or self::button or self::input]")
    
    for el in elements:
        try:
            # 要素の各種属性をチェック
            attr_text = (el.text + (el.get_attribute("onclick") or "") + (el.get_attribute("alt") or "") + (el.get_attribute("src") or "") + (el.get_attribute("href") or "")).lower()
            
            if any(k in attr_text for k in keywords):
                log(f"🎯 ログイン要素らしきものを発見: {el.tag_name} (判定: {attr_text[:50]}...)")
                # 物理クリック
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                time.sleep(1)
                ActionChains(driver).move_to_element(el).pause(0.5).click().perform()
                return True
        except:
            continue

    # 2. 子フレームを再帰探索
    frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
    for i in range(len(frames)):
        try:
            driver.switch_to.frame(i)
            if find_and_click_login_brute_force(driver):
                return True
            driver.switch_to.parent_frame()
        except:
            driver.switch_to.parent_frame()
    return False

def main():
    driver = None
    try:
        driver = setup_driver()
        log(f"🏁 玄関ページ: {START_URL}")
        driver.get(START_URL)
        time.sleep(8)

        log("🔎 ログインボタンを絨毯爆弾スキャン中...")
        if not find_and_click_login_brute_force(driver):
            log("❌ 全フレーム探索しましたが、ログイン関連要素が皆無です。")
            # デバッグ用に今のページのソースの一部を出力
            log(f"DEBUG: ページタイトル: {driver.title}")
            return

        log("⏳ 遷移待ち (15秒)...")
        time.sleep(15)
        
        # 遷移後、別ウィンドウが開いていないか確認
        if len(driver.window_handles) > 1:
            log("🪟 別ウィンドウが開いたので、そちらに切り替えます。")
            driver.switch_to.window(driver.window_handles[-1])

        log(f"DEBUG: 現在のURL: {driver.current_url}")
        log(f"DEBUG: ページタイトル: {driver.title}")

        if "おわび" in driver.title:
            log("🚨 またもや『おわび』画面です。")
        else:
            log("✨ 成功か？ おわび画面ではありません！")
            # 以降、ID/パスワード入力ロジックへ...

    except Exception as e:
        log(f"❌ エラー発生: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
