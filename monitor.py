import os, time, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# 設定
LOGIN_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"
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
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def login_and_check(driver, wait):
    print("🔑 ログイン開始...")
    driver.get(LOGIN_URL)
    time.sleep(5) # 読み込み待ち

    # 1. 直接JavaScriptでIDとパスワードを入力してログイン
    print("⌨️ ID/PASSを入力中...")
    login_success = driver.execute_script(f"""
        try {{
            // 要素を特定（JKKの一般的なID/Name属性をカバー）
            let uid = document.querySelector('input[id*="user"], input[name*="user"]');
            let upw = document.querySelector('input[type="password"]');
            let btn = document.querySelector('img[src*="btn_login"], input[src*="btn_login"], a[onclick*="login"]');
            
            if (uid && upw) {{
                uid.value = "{JKK_ID}";
                upw.value = "{JKK_PASS}";
                if (btn) {{
                    btn.click();
                    return true;
                }}
            }}
            return false;
        }} catch(e) {{ return false; }}
    """)

    if not login_success:
        print("⚠️ JS入力に失敗しました。ActionChainsで予備試行します...")
        actions = ActionChains(driver)
        actions.send_keys(Keys.TAB).send_keys(Keys.TAB).send_keys(JKK_ID).send_keys(Keys.TAB).send_keys(JKK_PASS).send_keys(Keys.ENTER).perform()

    # 2. ログイン成功の検知（マイページ特有の単語を探す）
    print("⏳ ログイン後の遷移を待機中...")
    time.sleep(7)
    driver.save_screenshot("login_result.png") # 状況確認用
    
    try:
        # 「ログアウト」「空室」「メニュー」のいずれかが出るまで待機
        wait.until(lambda d: d.execute_script("""
            let t = document.body.innerText;
            return t.includes('ログアウト') || t.includes('空室') || t.includes('メニュー') || t.includes('マイページ');
        """))
        print("✅ ログイン成功を確認しました。")
    except:
        print("❌ ログイン失敗、または遷移が遅れています。login_result.png を確認してください。")
        return False

    # 3. メニュー移動
    print("📍 メニューから検索画面へ移動中...")
    driver.execute_script("""
        let btn = Array.from(document.querySelectorAll('a, img, input')).find(el => 
            (el.innerText && el.innerText.includes('空室')) || 
            (el.src && el.src.includes('btn_search_cond')) ||
            (el.onclick && el.onclick.toString().includes('submitNext'))
        );
        if(btn) btn.click(); else if(typeof submitNext === 'function') submitNext();
    """)
    
    time.sleep(10)

    # 4. エリア選択（世田谷区）
    print("🎯 エリア選択（世田谷区）を実行中...")
    area_found = driver.execute_script("""
        function selectArea(w) {
            try {
                let cb = w.document.querySelector("input[value='113']");
                if (cb) {
                    cb.click();
                    let sBtn = w.document.querySelector('img[src*="btn_search"], a[onclick*="doSearch"]');
                    if (sBtn) { sBtn.click(); } 
                    else if (typeof w.doSearch === 'function') { w.doSearch(); }
                    return true;
                }
                for (let i = 0; i < w.frames.length; i++) {
                    if (selectArea(w.frames[i])) return true;
                }
            } catch (e) { return false; }
            return false;
        }
        return selectArea(window);
    """)

    if not area_found:
        print("❌ エリア選択に失敗しました。")
        return False
    print("✅ 世田谷区を選択し、検索を開始しました。")

    # 5. ウィンドウ切り替え
    main_handle = driver.current_window_handle
    switched = False
    for i in range(15):
        if len(driver.window_handles) > 1:
            driver.switch_to.window([h for h in driver.window_handles if h != main_handle][0])
            print(f"🪟 ウィンドウ切り替え完了: {driver.title}")
            switched = True
            break
        time.sleep(1)

    # 6. スキャン判定
    print("🔎 空室スキャンを開始...")
    time.sleep(5)
    
    found_vacant = False
    all_target_frames = [None] + driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
    
    for target_f in all_target_frames:
        try:
            if target_f: driver.switch_to.frame(target_f)
            res = driver.execute_script("""
                function scan(w) {
                    try {
                        const keywords = ['DK', 'LDK', '1DK', '2DK', '1LDK', '2LDK', 'K', '１ＤＫ', '２ＤＫ', '１ＬＤＫ', '２ＬＤＫ', '詳細'];
                        let bodyText = w.document.body.innerText.toUpperCase();
                        if (keywords.some(k => bodyText.includes(k))) return true;
                        for (let i = 0; i < w.frames.length; i++) {
                            if (scan(w.frames[i])) return true;
                        }
                    } catch (e) { return false; }
                    return false;
                }
                return scan(window);
            """)
            if res:
                found_vacant = True
                break
        except: pass
        finally: driver.switch_to.default_content()

    return found_vacant

def main():
    driver = setup_driver()
    wait = WebDriverWait(driver, 30)
    try:
        if login_and_check(driver, wait):
            print("🚨 空室発見！")
            requests.post(DISCORD_WEBHOOK_URL, json={
                "content": "🏠 **JKK世田谷区：空室あり！**\nすぐ確認してください！\nhttps://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"
            })
        else:
            print("👀 空室はありませんでした。")
    except Exception as e:
        print(f"❌ エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
