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
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def login_and_check(driver, wait):
    print("🔑 ログイン開始...")
    driver.get(LOGIN_URL)
    time.sleep(3)

    # 1. ログイン入力
    actions = ActionChains(driver)
    actions.send_keys(Keys.TAB).send_keys(Keys.TAB).send_keys(JKK_ID).send_keys(Keys.TAB).send_keys(JKK_PASS).perform()
    time.sleep(1)
    driver.execute_script("let btn = document.querySelector('img[src*=\"btn_login\"]'); if (btn) btn.click();")
    
    # 2. メニューから検索画面へ移動
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

    # 3. 世田谷区(113)を選択
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
                # 検索実行
                driver.execute_script("""
                    let sBtn = document.querySelector('img[src*=\"btn_search\"], a[onclick*=\"doSearch\"]');
                    if(sBtn) sBtn.click(); else if(typeof doSearch === 'function') doSearch();
                """)
                break
        except: pass
        finally: driver.switch_to.default_content()

    if not found_area:
        print("❌ エリア選択に失敗しました")
        return False

    # 4. 【重要】結果表示待ちと空室判定
    print("⏳ 検索結果の読み込みを待機（15秒）...")
    time.sleep(15) 

    # 画像にある「詳細」ボタンや「世田谷区」のリスト行があるかを全フレームからスキャン
    is_vacant = driver.execute_script("""
        let found = false;
        function scan(w) {
            try {
                let html = w.document.body.innerHTML;
                let text = w.document.body.innerText;
                // 「世田谷区」という文字があり、かつ「詳細」ボタンが存在するか
                if (text.includes('世田谷区') && (html.includes('詳細') || html.includes('btn_detail'))) {
                    // 「該当するデータはありません」という文言がないことを確認
                    if (!text.includes('該当するデータはありません') && !text.includes('一致する物件はありません')) {
                        found = true;
                    }
                }
                for (let i = 0; i < w.frames.length; i++) scan(w.frames[i]);
            } catch (e) {}
        }
        scan(window);
        return found;
    """)
    
    return is_vacant

def main():
    driver = setup_driver()
    wait = WebDriverWait(driver, 25)
    try:
        if login_and_check(driver, wait):
            print("🚨 空室を発見しました！通知を飛ばします。")
            requests.post(DISCORD_WEBHOOK_URL, json={
                "content": "🏠 **【JKK世田谷区】空室あり！**\n画像で確認された物件が掲載されています。至急確認してください！\nhttps://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"
            })
        else:
            print("👀 空室は見つかりませんでした（判定ロジックが画像を検知できませんでした）。")
    except Exception as e:
        print(f"❌ エラー発生: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
