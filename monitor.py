import os, time, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# --- 設定 ---
# ログイン画面の直リンクではなく、まずは「入口」から入る
START_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/"
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
    print(f"🏁 入口ページにアクセス中: {START_URL}")
    driver.get(START_URL)
    time.sleep(10)

    # 1. トップページから「ログイン画面」を呼び出す
    print("🖱️ ログイン画面へのボタンをクリックします...")
    driver.execute_script("""
        let loginBtn = Array.from(document.querySelectorAll('a, img')).find(el => 
            (el.innerText && el.innerText.includes('ログイン')) || 
            (el.src && el.src.includes('btn_mypage_login')) ||
            (el.href && el.href.includes('mypageLogin'))
        );
        if (loginBtn) { loginBtn.click(); } 
        else { window.location.href = 'https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin'; }
    """)
    
    time.sleep(10) # ログイン画面の読み込みを待つ

    # 2. ログイン情報を入力（再帰的に全フレームを探索）
    print("⌨️ ログイン情報を探索・入力中...")
    status = driver.execute_script("""
        const jkk_id = arguments[0];
        const jkk_pass = arguments[1];
        function findAndFill(w) {
            try {
                let uid = w.document.querySelector('input[name*="uid"], input[id*="uid"], input[name*="user"], input[id*="user"]');
                let upw = w.document.querySelector('input[type="password"]');
                let btn = w.document.querySelector('img[src*="btn_login"], input[src*="btn_login"], a[class*="login"], button[type="submit"]');
                
                if (uid && upw) {
                    uid.value = jkk_id;
                    upw.value = jkk_pass;
                    if (btn) { btn.click(); return "SUCCESS_CLICK"; }
                    uid.dispatchEvent(new KeyboardEvent('keydown', {'key': 'Enter'}));
                    return "SUCCESS_ENTER";
                }
                for (let i = 0; i < w.frames.length; i++) {
                    let res = findAndFill(w.frames[i]);
                    if (res && res.includes("SUCCESS")) return res;
                }
            } catch(e) { return "ERROR"; }
            return "NOT_FOUND";
        }
        return findAndFill(window);
    """, JKK_ID, JKK_PASS)

    print(f"📊 ログイン処理結果: {status}")
    
    if "SUCCESS" not in status:
        driver.save_screenshot("login_failed.png")
        return False

    # 3. ログイン成功後の遷移待ち
    print("⏳ マイページへの遷移を待機中...")
    time.sleep(10)
    
    # 4. 検索条件画面へ移動
    driver.execute_script("""
        let b = Array.from(document.querySelectorAll('a, img')).find(el => 
            el.src?.includes('btn_search_cond') || el.innerText?.includes('空室')
        );
        if(b) b.click();
    """)
    time.sleep(8)

    # 5. 世田谷区を選択して検索
    print("🎯 世田谷区を選択中...")
    area_ok = driver.execute_script("""
        function sel(w) {
            try {
                let cb = w.document.querySelector("input[value='113']");
                if (cb) {
                    cb.click();
                    let b = w.document.querySelector('img[src*="btn_search"], a[onclick*="doSearch"]');
                    if (b) b.click(); else if (w.doSearch) w.doSearch();
                    return true;
                }
                for (let i = 0; i < w.frames.length; i++) if (sel(w.frames[i])) return true;
            } catch(e) {}
            return false;
        }
        return sel(window);
    """)

    if not area_ok:
        print("❌ エリア選択に失敗しました。")
        driver.save_screenshot("area_error.png")
        return False

    # 6. 空室スキャン
    print("🔎 最終スキャン中...")
    time.sleep(8)
    # 別窓対応
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])

    vacant = driver.execute_script("""
        function scan(w) {
            const ks = ['DK', 'LDK', '1DK', '2DK', '1LDK', '2LDK', 'K', '詳細', '物件'];
            let txt = w.document.body.innerText.toUpperCase();
            if (ks.some(k => txt.includes(k))) return true;
            for (let i = 0; i < w.frames.length; i++) if (scan(w.frames[i])) return true;
            return false;
        }
        return scan(window);
    """)
    return vacant

def main():
    driver = setup_driver()
    wait = WebDriverWait(driver, 40)
    try:
        if login_and_check(driver, wait):
            print("🚨 空室を発見しました！")
            requests.post(DISCORD_WEBHOOK_URL, json={"content": "🏠 **JKK世田谷区：空室あり！**\\nhttps://jhomes.to-kousya.or.jp/search/jkknet/pc/"})
        else:
            print("👀 空室はありませんでした。")
    except Exception as e:
        print(f"❌ エラー発生: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
