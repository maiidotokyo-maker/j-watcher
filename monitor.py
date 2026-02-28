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
from webdriver_manager.chrome import ChromeDriverManager

# --- ログ出力の強化 ---
sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

log("🚀 スクリプトを開始します（検知回避モード）...")

# --- 環境変数の取得 ---
START_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
JKK_ID = os.environ.get("JKK_ID", "").strip()
JKK_PASS = os.environ.get("JKK_PASSWORD", "").strip()

def setup_driver():
    options = Options()
    options.add_argument('--headless=new') # 最新のヘッドレスモード
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    # 【重要】自動操作であることを隠す設定
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # ユーザーエージェントを一般的なWindows Chromeに偽装
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # 【重要】navigator.webdriverを隠蔽するスクリプトを注入
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    return driver

def find_and_fill_recursive(driver, jkk_id, jkk_pass, dry_run=False):
    try:
        pws = driver.find_elements(By.XPATH, "//input[@type='password']")
        if pws:
            if dry_run: return True
            uids = driver.find_elements(By.XPATH, "//input[contains(@name, 'uid') or contains(@id, 'uid') or contains(@name, 'user')]")
            if uids:
                uids[0].clear()
                uids[0].send_keys(jkk_id)
                pws[0].clear()
                pws[0].send_keys(jkk_pass)
                btns = driver.find_elements(By.XPATH, "//img[contains(@src, 'login')] | //input[@type='image'] | //input[@type='submit'] | //button")
                if btns:
                    btns[0].click()
                else:
                    pws[0].send_keys(Keys.RETURN)
                return True

        frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
        for i in range(len(frames)):
            try:
                driver.switch_to.frame(i)
                if find_and_fill_recursive(driver, jkk_id, jkk_pass, dry_run):
                    return True
                driver.switch_to.parent_frame()
            except:
                driver.switch_to.parent_frame()
                continue
    except:
        pass
    return False

def wait_for_login_form_recursive(driver, timeout=30):
    log("⏳ ログインフォームを全フレームから探索中...")
    end_time = time.time() + timeout
    while time.time() < end_time:
        driver.switch_to.default_content()
        if find_and_fill_recursive(driver, "", "", dry_run=True):
            log("✅ ログインフォームを検出しました！")
            return True
        time.sleep(3)
    return False

def select_area_and_scan(driver):
    log("📍 エリア選択画面へ移動...")
    driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/vacancy/area")
    time.sleep(8)

    log("🎯 世田谷区(113)を選択中...")
    selected = driver.execute_script("""
        function selectRecursive(w) {
            try {
                let cb = w.document.querySelector("input[value='113']");
                if (cb) {
                    cb.click();
                    let btn = w.document.querySelector('img[src*="search"], a[onclick*="doSearch"]');
                    if (btn) btn.click(); else if (w.doSearch) w.doSearch();
                    return true;
                }
                for (let i = 0; i < w.frames.length; i++) {
                    if (selectRecursive(w.frames[i])) return true;
                }
            } catch(e) {}
            return false;
        }
        return selectRecursive(window);
    """)

    if not selected:
        log("❌ 世田谷区の選択に失敗しました。")
        return False

    log("🔎 空室状況をスキャン中...")
    time.sleep(10)

    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])

    found = driver.execute_script("""
        function scanRecursive(w) {
            try {
                const keywords = ['DK', 'LDK', '1DK', '2DK', '詳細'];
                let text = w.document.body.innerText.toUpperCase();
                if (keywords.some(k => text.includes(k))) return true;
                for (let i = 0; i < w.frames.length; i++) {
                    if (scanRecursive(w.frames[i])) return true;
                }
            } catch(e) {}
            return false;
        }
        return scanRecursive(window);
    """)
    return found

def main():
    if not JKK_ID or not JKK_PASS:
        log("❌ エラー: JKK_ID または JKK_PASSWORD が不足しています。")
        return

    driver = None
    try:
        driver = setup_driver()
        log("✅ ブラウザ起動完了")

        log(f"🏁 玄関ページへアクセス: {START_URL}")
        driver.get(START_URL)
        time.sleep(5)

        log("🖱️ ログインシーケンス開始（JavaScript実行）...")
        driver.execute_script("""
            if (typeof mypageLogin === 'function') {
                mypageLogin();
            } else {
                let lnk = document.querySelector("a[onclick*='mypageLogin'], area[onclick*='mypageLogin']");
                if (lnk) lnk.click();
            }
        """)
        time.sleep(5)
        
        if not wait_for_login_form_recursive(driver):
            log(f"DEBUG: 現在のURL: {driver.current_url}")
            log(f"DEBUG: ページタイトル: {driver.title}")
            log("⚠️ 最終手段：URL直接アクセス...")
            driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin")
            if not wait_for_login_form_recursive(driver):
                driver.save_screenshot("error_final.png")
                log("❌ ログインフォームを特定できませんでした。")
                return

        log("⌨️ ログイン情報を入力中...")
        driver.switch_to.default_content()
        if find_and_fill_recursive(driver, JKK_ID, JKK_PASS):
            log("✅ 送信完了。ログイン判定待ち...")
            time.sleep(15)
            
            if select_area_and_scan(driver):
                log("🚨 【空室あり】世田谷区に見つかりました！")
                if DISCORD_WEBHOOK_URL:
                    now = datetime.now().strftime('%H/%m/%d %H:%M:%S')
                    msg = {"content": f"🏠 **JKK世田谷区：空室あり！**\n🕒 検出: {now}\n🔗 {START_URL}"}
                    requests.post(DISCORD_WEBHOOK_URL, json=msg)
            else:
                log("👀 現在、世田谷区に空室はありません。")

    except Exception as e:
        log(f"❌ 予期せぬエラー: {e}")
    finally:
        if driver:
            driver.quit()
        log("🏁 スクリプトを終了します。")

if __name__ == "__main__":
    main()
