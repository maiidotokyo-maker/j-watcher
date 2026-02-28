import sys
import os
import time
import random
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

log("🚀 スクリプトを開始します（ゆらぎ待機モード）...")

# --- 環境変数の取得 ---
START_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
JKK_ID = os.environ.get("JKK_ID", "").strip()
JKK_PASS = os.environ.get("JKK_PASSWORD", "").strip()

def setup_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    # 自動操作フラグを隠蔽
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 一般的なブラウザのユーザーエージェント
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # navigator.webdriver を隠す
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
                time.sleep(random.uniform(0.5, 1.5)) # 入力にもゆらぎ
                uids[0].send_keys(jkk_id)
                pws[0].clear()
                time.sleep(random.uniform(0.5, 1.5))
                pws[0].send_keys(jkk_pass)
                
                # ログインボタン
                btns = driver.find_elements(By.XPATH, "//img[contains(@src, 'login')] | //input[@type='image'] | //input[@type='submit'] | //button")
                time.sleep(random.uniform(1.0, 3.0))
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
        time.sleep(random.uniform(3.0, 5.0))
    return False

def select_area_and_scan(driver):
    log("📍 エリア選択画面へ移動...")
    driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/vacancy/area")
    time.sleep(random.uniform(8.0, 12.0))

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
    time.sleep(random.uniform(10.0, 15.0))

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
        
        # 人間らしく振る舞う：少し待ってからスクロール
        time.sleep(random.uniform(5.0, 8.0))
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(random.uniform(2.0, 4.0))

        log("🖱️ ログインシーケンス開始（JavaScript実行）...")
        # ボタンを直接叩く前に、少しページをいじる
        driver.execute_script("""
            let target = document.querySelector("a[onclick*='mypageLogin'], area[onclick*='mypageLogin']");
            if (target) {
                target.scrollIntoView();
                target.click();
            } else if (typeof mypageLogin === 'function') {
                mypageLogin();
            }
        """)
        
        # 遷移をじっくり待つ
        time.sleep(random.uniform(10.0, 15.0))
        
        if not wait_for_login_form_recursive(driver):
            log(f"DEBUG: 現在のURL: {driver.current_url}")
            log(f"DEBUG: ページタイトル: {driver.title}")
            
            # 「おわび」画面が出た場合のCookieリセット
            if "おわび" in driver.title:
                log("🚨 'おわび'画面を検知。Cookieを削除して再試行...")
                driver.delete_all_cookies()
                driver.get(START_URL)
                time.sleep(10)
            
            log("⚠️ 最終手段：URL直接アクセス...")
            driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin")
            time.sleep(random.uniform(10.0, 15.0))
            
            if not wait_for_login_form_recursive(driver):
                driver.save_screenshot("error_final.png")
                log("❌ ログインフォームを特定できませんでした。")
                return

        log("⌨️ ログイン情報を入力中...")
        driver.switch_to.default_content()
        if find_and_fill_recursive(driver, JKK_ID, JKK_PASS):
            log("✅ 送信完了。ログイン判定待ち...")
            time.sleep(20) # ログイン処理は重いので長めに待機
            
            if select_area_and_scan(driver):
                log("🚨 【空室あり】世田谷区に見つかりました！")
                if DISCORD_WEBHOOK_URL:
                    now = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
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
