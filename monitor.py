import os, time, requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# --- 設定 ---
START_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/"
LOGIN_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"
AREA_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/vacancy/area"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
JKK_ID = os.environ.get("JKK_ID", "").strip()
JKK_PASS = os.environ.get("JKK_PASSWORD", "").strip()

def setup_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1280,1024')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def wait_for_login_form(driver, timeout=30):
    print("⏳ ログインフォームの出現を待機中...")
    wait = WebDriverWait(driver, timeout)
    try:
        wait.until(lambda d: d.find_element(By.XPATH, "//input[@type='password']"))
        print("✅ ログインフォームを検出しました。")
        return True
    except:
        print("❌ ログインフォームが表示されませんでした。")
        driver.save_screenshot("login_form_not_found.png")
        return False

def find_and_fill_recursive(driver, jkk_id, jkk_pass):
    try:
        uids = driver.find_elements(By.XPATH, "//input[contains(@name, 'uid') or contains(@id, 'uid') or contains(@name, 'user') or contains(@id, 'Id')]")
        pws = driver.find_elements(By.XPATH, "//input[@type='password']")
        if uids and pws:
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
            driver.switch_to.frame(i)
            if find_and_fill_recursive(driver, jkk_id, jkk_pass):
                return True
            driver.switch_to.parent_frame()
    except Exception:
        pass
    return False

def check_text_recursive(driver):
    try:
        txt = driver.find_element(By.TAG_NAME, "body").text
        if any(k in txt for k in ["ログアウト", "空室", "メニュー", "マイページ"]):
            return True
        frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
        for i in range(len(frames)):
            driver.switch_to.frame(i)
            if check_text_recursive(driver): return True
            driver.switch_to.parent_frame()
    except Exception:
        pass
    return False

def login_and_check(driver):
    print(f"🏁 玄関ページへアクセス: {START_URL}")
    driver.get(START_URL)
    time.sleep(5)

    print("🖱️ ログインページへ移動中...")
    driver.get(LOGIN_URL)

    if not wait_for_login_form(driver):
        return False

    print("⌨️ 全フレームを再帰的に探索してID/PASSを入力中...")
    if find_and_fill_recursive(driver, JKK_ID, JKK_PASS):
        print("✅ ログイン情報の送信に成功しました！")
    else:
        print("❌ どのフレームにも入力欄が見つかりませんでした。")
        driver.save_screenshot("all_frames_failed.png")
        return False

    print("⏳ 処理待ち...")
    time.sleep(15)

    if check_text_recursive(driver):
        print("🚨 ログイン突破成功！！！")
        driver.save_screenshot("login_success.png")
        return True

    print("❌ ログイン後の画面を確認できませんでした。")
    driver.save_screenshot("after_submit_failed.png")
    return False

def select_area_and_scan(driver):
    print("📍 エリア選択画面へ移動します...")
    driver.get(AREA_URL)
    time.sleep(8)

    print("🎯 世田谷区を選択中...")
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
        print("❌ 世田谷区の選択に失敗しました。")
        driver.save_screenshot("area_select_failed.png")
        return False

    print("🔎 空室状況をスキャン中...")
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
    driver = setup_driver()
    try:
        if login_and_check(driver):
            print("🚀 ログイン成功。エリアスキャンを開始します...")
            if select_area_and_scan(driver):
                print("🚨 【空室あり】世田谷区に空室が見つかりました！")
                if DISCORD_WEBHOOK_URL:
                    requests.post(DISCORD_WEBHOOK_URL, json={
                        "content": f"🏠 **JKK世田谷区：空室あり！**\n{datetime.now().strftime('%Y/%m/%d %H:%M:%S')} に検出されました！\nhttps://jhomes.to-kousya.or.jp/search/jkknet/pc/"
                    })
            else:
                print("👀 現在、世田谷区に空室はありません。")
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
