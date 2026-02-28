import os, time, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# --- 設定（GitHub ActionsのSecretsから読み込み） ---
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
    time.sleep(3)
    main_handle = driver.current_window_handle

    # 1. ログイン入力（ActionChainsで確実に）
    actions = ActionChains(driver)
    actions.send_keys(Keys.TAB).send_keys(Keys.TAB).send_keys(JKK_ID).send_keys(Keys.TAB).send_keys(JKK_PASS).perform()
    time.sleep(1)
    driver.execute_script("let btn = document.querySelector('img[src*=\"btn_login\"]'); if (btn) btn.click();")

    # デバッグ用に状態を保存
    time.sleep(7)
    driver.save_screenshot("login_result.png")
    print("📸 ログイン後の状態を保存しました(login_result.png)")

    # 1.6 ログイン成功の検知
    try:
        wait.until(lambda d: d.execute_script("return document.body.innerText.includes('空室') || document.body.innerText.includes('メニュー')"))
        print("✅ ログイン成功を確認しました。")
    except:
        print("❌ ログイン失敗、または遷移が遅れています。")
        return False

    # 2. メニュー移動（空室検索へ）
    print("📍 メニューから検索画面へ移動中...")
    driver.execute_script("""
        let btn = Array.from(document.querySelectorAll('a, img, input')).find(el => 
            (el.innerText && el.innerText.includes('空室')) || 
            (el.src && el.src.includes('btn_search_cond')) ||
            (el.onclick && el.onclick.toString().includes('submitNext'))
        );
        if(btn) btn.click();
        else if(typeof submitNext === 'function') submitNext();
    """)
    
    time.sleep(10) # 検索条件画面の読み込みを待機

    # 3. エリア選択（世田谷区:113）を再帰JSで実行
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
        print("❌ 世田谷区のチェックボックスが見つかりませんでした。")
        return False
    print("✅ 世田谷区を選択し、検索を開始しました。")

    # 4. 検索結果ウィンドウの出現を監視
    print("⏳ 検索結果ウィンドウを待機中...")
    switched = False
    for i in range(20):
        handles = driver.window_handles
        if len(handles) > 1:
            new_handles = [h for h in handles if h != main_handle]
            if new_handles:
                driver.switch_to.window(new_handles[0])
                print(f"🪟 ウィンドウ切り替え完了: {driver.title}")
                switched = True
                break
        time.sleep(1)
    
    if not switched:
        print("🔍 別ウィンドウなし。現在のウィンドウでスキャンします。")

    # 5. 検索結果の描画完了を待機
    print("⌛ 検索結果の描画を待機中...")
    try:
        wait.until(lambda d: d.execute_script("""
            let t = document.body.innerText;
            return t.includes('詳細') || t.includes('物件') || t.includes('DK') || t.includes('データはありません');
        """))
    except: pass
    time.sleep(3)

    # 6. 全フレームを対象に空室スキャン
    print("🔎 全フレームを対象に最終スキャンを開始...")
    found_vacant = False
    all_target_frames = [None] + driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
    
    for target_f in all_target_frames:
        try:
            if target_f:
                driver.switch_to.frame(target_f)
            
            res = driver.execute_script("""
                function scan(w) {
                    try {
                        const keywords = ['DK', 'LDK', '1DK', '2DK', '1LDK', '2LDK', 'K', '１ＤＫ', '２ＤＫ', '１ＬＤＫ', '２ＬＤＫ', '詳細'];
                        let images = w.document.getElementsByTagName('img');
                        for (let img of images) {
                            let text = ((img.alt || "") + (img.src || "") + (img.parentElement ? img.parentElement.innerText : "")).toUpperCase();
                            if (keywords.some(k => text.includes(k))) return true;
                        }
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
                print("✅ 空室情報を検知しました！")
                found_vacant = True
                break
        except: pass
        finally:
            driver.switch_to.default_content()

    return found_vacant

def main():
    driver = setup_driver()
    wait = WebDriverWait(driver, 30)
    try:
        if login_and_check(driver, wait):
            print("🚨 空室を発見しました！通知を送ります。")
            # --- SyntaxErrorを修正したDiscord通知部分 ---
            requests.post(DISCORD_WEBHOOK_URL, json={
                "content": "🏠 **JKK世田谷区：空室あり！**\nすぐ確認してください！\nhttps://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"
            })
        else:
            print("👀 空室はありませんでした。")
    except Exception as e:
        print(f"❌ エラー発生: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
