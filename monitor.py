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
    print("🔑 ログイン開始...")
    driver.get(LOGIN_URL)
    time.sleep(3)
    main_handle = driver.current_window_handle

    # 1. ログイン入力
    actions = ActionChains(driver)
    actions.send_keys(Keys.TAB).send_keys(Keys.TAB).send_keys(JKK_ID).send_keys(Keys.TAB).send_keys(JKK_PASS).perform()
    time.sleep(1)
    driver.execute_script("let btn = document.querySelector('img[src*=\"btn_login\"]'); if (btn) btn.click();")
    
    # 2. メニュー移動
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

    # 3. エリア選択（世田谷区）
    print("🎯 エリア選択（世田谷区）...")
    found_area = False
    all_frames = [None] + driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
    
    for f in all_frames:
        try:
            if f: driver.switch_to.frame(f)
            checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[value='113']")
            if checkboxes:
                driver.execute_script("arguments[0].click();", checkboxes[0])
                print("✅ 世田谷区を選択完了")
                found_area = True
                driver.execute_script("""
                    let sBtn = document.querySelector('img[src*=\"btn_search\"], a[onclick*=\"doSearch\"]');
                    if(sBtn) sBtn.click(); else if(typeof doSearch === 'function') doSearch();
                """)
                break
        except: pass
        finally: driver.switch_to.default_content()

    if not found_area: return False

    # 4. 新しいウィンドウの出現を監視
    print("⏳ 検索結果ウィンドウを待機中...")
    switched = False
    for i in range(20):
        handles = driver.window_handles
        if len(handles) > 1:
            new_handles = [h for h in handles if h != main_handle]
            if new_handles:
                driver.switch_to.window(new_handles[0])
                print(f"🪟 ウィンドウ切り替え完了!: {driver.title}")
                wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
                switched = True
                break
        time.sleep(1)
    
    if not switched:
        print("🔍 別ウィンドウなし。現在のウィンドウで続行します。")

    # 5. 【最強ロジック】全フレームをPythonで巡回しつつJSでスキャン
    print("🔎 全フレームを対象に空室スキャンを開始...")
    time.sleep(5)
    
    found_vacant = False
    all_target_frames = [None] + driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
    
    for target_f in all_target_frames:
        try:
            if target_f:
                frame_name = target_f.get_attribute("name") or target_f.get_attribute("id") or "(no name)"
                print(f"🔍 フレーム切り替え中: {frame_name}")
                driver.switch_to.frame(target_f)
            else:
                print("🔍 メインフレームをスキャン中...")

            # 各フレーム内で再帰スキャンJSを実行
            res = driver.execute_script("""
                function scan(w) {
                    try {
                        const keywords = ['DK', 'LDK', '1DK', '2DK', '1LDK', '2LDK', 'K', '１ＤＫ', '２ＤＫ', '１ＬＤＫ', '２ＬＤＫ'];
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
        except Exception as e:
            print(f"⚠️ スキャン中にスキップ: {e}")
        finally:
            driver.switch_to.default_content()

    if not found_vacant:
        print("❌ 全フレームを走査しましたが、キーワードは見つかりませんでした。")

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
