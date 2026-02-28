import os, time, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# --- 設定 ---
# ログイン画面のURL
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
    print(f"🔑 ログインページへ直接アクセス: {LOGIN_URL}")
    driver.get(LOGIN_URL)
    
    # ページ構造が複雑なので長めに待機
    time.sleep(15)

    # 1. ログインフォーム入力（セレクタを極限まで強化）
    print("⌨️ ID/PASS入力欄を探索中...")
    status = driver.execute_script("""
        const jkk_id = arguments[0];
        const jkk_pass = arguments[1];
        
        function findAndFill(w) {
            try {
                // ターゲットとなる全入力要素を取得
                let inputs = Array.from(w.document.querySelectorAll('input'));
                let uid = inputs.find(el => el.name?.includes('uid') || el.id?.includes('uid') || el.id?.includes('user'));
                let upw = inputs.find(el => el.type === 'password');
                let btn = w.document.querySelector('img[src*="login"], input[type="image"], input[type="submit"], .btn_login');

                if (uid && upw) {
                    uid.value = jkk_id;
                    upw.value = jkk_pass;
                    if (btn) { btn.click(); return "SUCCESS_CLICK"; }
                    // ボタンがない場合はフォーム送信を試みる
                    if (uid.form) { uid.form.submit(); return "SUCCESS_SUBMIT"; }
                    return "SUCCESS_FILL_ONLY";
                }

                // フレームの中を再帰的に探す
                for (let i = 0; i < w.frames.length; i++) {
                    let res = findAndFill(w.frames[i]);
                    if (res && res.includes("SUCCESS")) return res;
                }
            } catch(e) { return "ERROR: " + e.message; }
            return "NOT_FOUND";
        }
        return findAndFill(window);
    """, JKK_ID, JKK_PASS)

    print(f"📊 ログイン処理結果: {status}")
    
    if "SUCCESS" not in status:
        driver.save_screenshot("login_failed.png")
        print("❌ ログインフォームが見つかりませんでした。")
        return False

    # 2. ログイン後の遷移を待つ
    print("⏳ マイページ読み込み待ち...")
    time.sleep(12)

    # 3. 検索画面へ移動（「空室検索」ボタンを狙う）
    print("📍 検索画面へ遷移中...")
    nav_status = driver.execute_script("""
        function goSearch(w) {
            let b = Array.from(w.document.querySelectorAll('a, img, input')).find(el => 
                el.src?.includes('btn_search_cond') || el.innerText?.includes('空室') || el.alt?.includes('空室')
            );
            if (b) { b.click(); return true; }
            for (let i = 0; i < w.frames.length; i++) if (goSearch(w.frames[i])) return true;
            return false;
        }
        return goSearch(window);
    """)
    
    if not nav_status:
        print("❌ 検索ボタンが見つかりません。")
        driver.save_screenshot("nav_failed.png")
        return False

    time.sleep(8)

    # 4. エリア選択（世田谷区）
    print("🎯 世田谷区を選択中...")
    area_ok = driver.execute_script("""
        function sel(w) {
            let cb = w.document.querySelector("input[value='113']");
            if (cb) {
                cb.click();
                let b = w.document.querySelector('img[src*="search"], .btn_search, a[onclick*="doSearch"]');
                if (b) b.click(); else if (w.doSearch) w.doSearch();
                return true;
            }
            for (let i = 0; i < w.frames.length; i++) if (sel(w.frames[i])) return true;
            return false;
        }
        return sel(window);
    """)

    if not area_ok:
        print("❌ エリア選択失敗")
        return False

    # 5. 空室スキャン
    print("🔎 最終確認中...")
    time.sleep(10)
    # 別窓対応
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])

    vacant = driver.execute_script("""
        function scan(w) {
            const ks = ['DK', 'LDK', '1DK', '2DK', '詳細'];
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
    try:
        if login_and_check(driver, None):
            print("🚨 空室あり！")
            requests.post(DISCORD_WEBHOOK_URL, json={"content": "🏠 **JKK世田谷区：空室あり！**"})
        else:
            print("👀 現在、世田谷区に空室はありません。")
    except Exception as e:
        print(f"❌ エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
