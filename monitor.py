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
LOGIN_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu"
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

def login(driver, wait):
    print("🔑 ログイン開始...")
    driver.get(LOGIN_URL)
    main_handle = driver.current_window_handle

    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        driver.execute_script("""
            let links = Array.from(document.querySelectorAll('a'));
            let target = links.find(a => a.textContent.includes('こちら'));
            if (target) { target.click(); }
            else { window.open('https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin', '_blank'); }
        """)
    except Exception:
        driver.execute_script("window.open('https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin', '_blank');")

    time.sleep(5)
    if len(driver.window_handles) < 2:
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin")
    else:
        login_handle = [h for h in driver.window_handles if h != main_handle][0]
        driver.switch_to.window(login_handle)

    print("📝 ログイン情報を入力中...")
    time.sleep(3)
    actions = ActionChains(driver)
    actions.send_keys(Keys.TAB).send_keys(Keys.TAB).send_keys(JKK_ID).send_keys(Keys.TAB).send_keys(JKK_PASS).perform()
    time.sleep(1)
    driver.execute_script("let btn = document.querySelector('img[src*=\"btn_login\"]'); if (btn) btn.click();")
    
    time.sleep(7)
    # ログイン窓を閉じてメインへ戻る
    if len(driver.window_handles) > 1:
        driver.close() 
    driver.switch_to.window(main_handle)
    
    print("✅ ログイン完了後の状況確認")
    print(f"🌐 URL: {driver.current_url}")
    print(f"📄 Title: {driver.title}")

def search_setagaya(driver, wait):
    print("📍 検索条件画面へ移動開始...")
    driver.execute_script("""
        let btn = Array.from(document.querySelectorAll('a, img, input')).find(el => 
            (el.innerText && (el.innerText.includes('条件') || el.innerText.includes('空室'))) || 
            (el.src && el.src.includes('btn_search_cond')) ||
            (el.href && el.href.includes('vacantCondition'))
        );
        if(btn) btn.click();
    """)
    
    time.sleep(10)
    print("🎯 世田谷区のチェックボックスを全フレームから再帰的に探します...")

    def find_checkbox_recursive():
        checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[value='113']")
        if checkboxes:
            cb = checkboxes[0]
            driver.execute_script("arguments[0].scrollIntoView(true);", cb)
            driver.execute_script("arguments[0].click();", cb)
            print("✅ 世田谷区を発見・選択しました！")
            
            print("🔍 検索ボタンをクリック...")
            driver.execute_script("""
                let sBtn = document.querySelector('img[src*="btn_search"], a[onclick*="doSearch"]');
                if(sBtn) { sBtn.click(); }
                else if(typeof doSearch === 'function') { doSearch(); }
            """)
            return True

        frames = driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
        for i in range(len(frames)):
            try:
                driver.switch_to.frame(i)
                if find_checkbox_recursive():
                    return True
            except:
                pass
            finally:
                driver.switch_to.parent_frame()
        return False

    driver.switch_to.default_content()
    if not find_checkbox_recursive():
        print("❌ 探索失敗: 世田谷区が見つかりませんでした")
        print("🌐 現在のURL:", driver.current_url)
        print("📄 現在のタイトル:", driver.title)
        print("🧾 ページ冒頭HTML:")
        print(driver.page_source[:1000])
        raise Exception("世田谷区(113)が見つかりません")

    print("⏳ 検索結果を待機中（12秒）...")
    time.sleep(12)

    content = driver.execute_script("""
        let t=''; 
        function c(w){
            try{t += w.document.body.innerText + '\\n'}catch(e){}
            for(let i=0; i<w.frames.length; i++) c(w.frames[i]);
        } 
        c(window); return t;
    """)
    
    results = []
    if "世田谷区" in content:
        if not any(kw in content for kw in ["該当するデータはありません", "条件に一致する物件はありません"]):
            lines = [l.strip() for l in content.split('\n') if "世田谷区" in l and "案内可能" in l]
            results = list(set(lines))
    return results

def notify_discord(message):
    if not DISCORD_WEBHOOK_URL: return
    requests.post(DISCORD_WEBHOOK_URL, json={"content": message})

def main():
    driver = setup_driver()
    wait = WebDriverWait(driver, 25)
    try:
        login(driver, wait)
        current = search_setagaya(driver, wait)
        if current:
            msg = "🏠 **世田谷区に空室アリ！**\n" + "\n".join([f"- {i}" for i in current])
            notify_discord(msg)
            print(f"✅ 通知送信: {len(current)}件")
        else:
            print("👀 現在、空室はありません。")
    except Exception as e:
        print(f"❌ エラー詳細: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
