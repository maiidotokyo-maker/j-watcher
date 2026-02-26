import os, time, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
    # --- 1. ログイン（ここは成功しているので変更なし） ---
    print("🔑 ログイン開始...")
    driver.get(LOGIN_URL)
    time.sleep(3)
    main_handle = driver.current_window_handle

    actions = ActionChains(driver)
    actions.send_keys(Keys.TAB).send_keys(Keys.TAB).send_keys(JKK_ID).send_keys(Keys.TAB).send_keys(JKK_PASS).perform()
    time.sleep(1)
    driver.execute_script("let btn = document.querySelector('img[src*=\"btn_login\"]'); if (btn) btn.click();")
    
    # --- 2. メニュー移動（ここも成功中） ---
    print("📍 メニューから検索画面へ移動中...")
    time.sleep(7)
    driver.execute_script("""
        let btn = Array.from(document.querySelectorAll('a, img, input')).find(el => 
            (el.innerText && el.innerText.includes('空室')) || 
            (el.src && el.src.includes('btn_search_cond')) ||
            (el.onclick && el.onclick.toString().includes('submitNext'))
        );
        if(btn) btn.click();
        else if(typeof submitNext === 'function') submitNext();
    """)
    
    time.sleep(8)

    # --- 3. 世田谷区選択（ここも成功中） ---
    print("🎯 エリア選択（世田谷区）...")
    found = False
    all_frames = [None] + driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
    
    for f in all_frames:
        try:
            if f: driver.switch_to.frame(f)
            checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[value='113']")
            if checkboxes:
                driver.execute_script("arguments[0].click();", checkboxes[0])
                print("✅ 世田谷区を選択完了")
                found = True
                # 検索実行
                driver.execute_script("""
                    let sBtn = document.querySelector('img[src*=\"btn_search\"], a[onclick*=\"doSearch\"]');
                    if(sBtn) sBtn.click(); else if(typeof doSearch === 'function') doSearch();
                """)
                break
        except: pass
        finally: driver.switch_to.default_content()

    if not found: return False

    # --- 4. 【新機能】別ウィンドウへの切り替えと待機 ---
    print("⏳ 新しいウィンドウの待機中...")
    try:
        # 新しい窓が開くまで最大20秒待つ
        wait.until(lambda d: len(d.window_handles) > 1)
        for handle in driver.window_handles:
            if handle != main_handle:
                driver.switch_to.window(handle)
                print(f"🪟 検索結果ウィンドウに切り替え完了: {driver.title}")
                # ページが完全に読み込まれるまで待つ
                wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
                break
    except:
        print("ℹ️ 新しい窓は開きませんでした。同一窓での遷移として続行します。")

    # --- 5. 【強化版】間取りキーワードスキャン ---
    print("🔎 空室判定スキャン開始...")
    time.sleep(5) # 念押しの描画待ち
    
    found_vacant = driver.execute_script("""
        function scan(w) {
            try {
                // キーワードリスト（LDK等も網羅）
                const keywords = ['DK', 'LDK', '1DK', '2DK', '1LDK', '2LDK', 'K'];
                let images = w.document.getElementsByTagName('img');
                for (let img of images) {
                    // 画像のalt, src, 周辺テキストを大文字で統一してチェック
                    let text = ((img.alt || "") + (img.src || "") + (img.parentElement ? img.parentElement.innerText : "")).toUpperCase();
                    if (keywords.some(k => text.includes(k))) return true;
                }
                // 全てのフレームを再帰的にチェック
                for (let i = 0; i < w.frames.length; i++) {
                    if (scan(w.frames[i])) return true;
                }
            } catch (e) { return false; }
            return false;
        }
        return scan(window);
    """)
    
    return found_vacant

def main():
    driver = setup_driver()
    wait = WebDriverWait(driver, 30)
    try:
        if login_and_check(driver, wait):
            print("🚨 空室を発見しました！")
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
