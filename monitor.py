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

    # 1. ログイン入力 (Tabキーを利用)
    actions = ActionChains(driver)
    actions.send_keys(Keys.TAB).send_keys(Keys.TAB).send_keys(JKK_ID).send_keys(Keys.TAB).send_keys(JKK_PASS).perform()
    time.sleep(1)
    driver.execute_script("let btn = document.querySelector('img[src*=\"btn_login\"]'); if (btn) btn.click();")
    
    # 2. 待機画面（mypageMenu）でのボタンクリック
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
    
    time.sleep(8) # 画面遷移待ち

    # 3. 世田谷区(113)を全フレームから探索
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
                    let sBtn = document.querySelector('img[src*="btn_search"], a[onclick*="doSearch"]');
                    if(sBtn) sBtn.click(); else if(typeof doSearch === 'function') doSearch();
                """)
                break
        except: pass
        finally: driver.switch_to.default_content()

    if not found:
        return False

    # 4. 検索結果の待機と判定
    print("⏳ 検索結果を待機中（20秒間スキャン準備）...")
    time.sleep(20) # フレーム内の描画を確実に待つ

    # 判定ロジック：全フレームを再帰的にスキャンし、画像属性や周辺テキストに「DK」があるか確認
    found_vacant = driver.execute_script("""
        function scan(w) {
            try {
                // フレーム内の全画像タグを確認
                let images = w.document.getElementsByTagName('img');
                for (let img of images) {
                    let altText = (img.alt || "").toUpperCase();
                    let srcPath = (img.src || "").toUpperCase();
                    // 画像の親要素のテキストも一応確認（1DKなどの表記対策）
                    let parentText = (img.parentElement ? img.parentElement.innerText : "").toUpperCase();
                    
                    if (altText.includes('DK') || srcPath.includes('DK') || parentText.includes('DK')) {
                        return true;
                    }
                }
                
                // 子フレームを再帰探索
                for (let i = 0; i < w.frames.length; i++) {
                    if (scan(w.frames[i])) return true;
                }
            } catch (e) {
                return false; 
            }
            return false;
        }
        return scan(window);
    """)
    
    return found_vacant

def main():
    driver = setup_driver()
    wait = WebDriverWait(driver, 25)
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
