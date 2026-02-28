import os, time, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# --- 設定 ---
# ログインURL（入口ページ）
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
    print(f"🔑 ログイン開始... URL: {LOGIN_URL}")
    driver.get(LOGIN_URL)
    time.sleep(12) # 読み込みを十分に待つ

    # --- 🧪 デバッグ：ページ内の全入力を調査 ---
    print("🧪 ログインフォームの要素を調査中...")
    inputs = driver.execute_script("""
        function getAllInputs(w) {
            let res = Array.from(w.document.querySelectorAll('input')).map(el => ({
                id: el.id,
                name: el.name,
                type: el.type,
                value: el.value
            }));
            for (let i = 0; i < w.frames.length; i++) {
                try { res = res.concat(getAllInputs(w.frames[i])); } catch(e) {}
            }
            return res;
        }
        return getAllInputs(window);
    """)
    if not inputs:
        print("⚠️ 警告: ページ内に input 要素が一つも見つかりません。")
    for i, el in enumerate(inputs):
        print(f"   [{i}] id='{el['id']}' name='{el['name']}' type='{el['type']}'")

    # --- ⌨️ ログイン試行 ---
    print("🚀 ログインフォームを探索・入力試行...")
    status = "NOT_FOUND"
    for attempt in range(4):
        status = driver.execute_script("""
            const jkk_id = arguments[0];
            const jkk_pass = arguments[1];
            function findAndFill(w) {
                try {
                    // 柔軟なセレクタでID/PW欄を特定
                    let uid = w.document.querySelector('input[id*="user"], input[name*="user"], input[id*="uid"], input[id*="Id"]');
                    let upw = w.document.querySelector('input[type="password"]');
                    let btn = w.document.querySelector('img[src*="btn_login"], input[src*="btn_login"], a[onclick*="login"], button[type="submit"]');
                    
                    if (uid && upw) {
                        uid.value = jkk_id;
                        upw.value = jkk_pass;
                        if (btn) {
                            btn.click();
                            return "SUCCESS";
                        }
                        // ボタンが見つからない場合はEnterキー
                        uid.dispatchEvent(new KeyboardEvent('keydown', {'key': 'Enter'}));
                        return "SUCCESS_BY_ENTER";
                    }
                    for (let i = 0; i < w.frames.length; i++) {
                        let res = findAndFill(w.frames[i]);
                        if (res && res.includes("SUCCESS")) return res;
                    }
                } catch(e) { return "JS_ERROR: " + e.message; }
                return "NOT_FOUND";
            }
            return findAndFill(window);
        """, JKK_ID, JKK_PASS)

        if "SUCCESS" in status:
            print(f"✅ ログイン情報を入力しました！ステータス: {status} (試行 {attempt+1}回目)")
            break
        print(f"   ...要素がまだ見つかりません (試行 {attempt+1}/4)。待機中...")
        time.sleep(7)

    if "SUCCESS" not in status:
        driver.save_screenshot("login_error.png")
        print(f"❌ ログイン失敗。最終ステータス: {status}")
        return False

    # --- ⏳ 遷移待ち ---
    print("⏳ ログイン後の遷移を待機中...")
    time.sleep(12)
    try:
        wait.until(lambda d: d.execute_script("""
            let t = document.body.innerText;
            return t.includes('ログアウト') || t.includes('空室') || t.includes('メニュー') || t.includes('マイページ');
        """))
        print("✅ マイページへのログインを確認しました。")
    except:
        driver.save_screenshot("after_login_error.png")
        print("❌ ログイン後の画面遷移が確認できません。")
        return False

    # --- 📍 検索条件入力画面へ移動 ---
    print("📍 検索条件入力画面へ移動中...")
    driver.execute_script("""
        let btn = Array.from(document.querySelectorAll('a, img, input')).find(el => 
            (el.innerText && el.innerText.includes('空室')) || 
            (el.src && el.src.includes('btn_search_cond')) ||
            (el.onclick && el.onclick.toString().includes('submitNext'))
        );
        if(btn) btn.click(); else if(typeof submitNext === 'function') submitNext();
    """)
    
    # --- 🎯 エリア選択（世田谷区：113） ---
    print("🎯 エリア選択（世田谷区）を実行中...")
    area_found = False
    for i in range(5):
        time.sleep(7)
        area_found = driver.execute_script("""
            function selectArea(w) {
                try {
                    let cb = w.document.querySelector("input[value='113']");
                    if (cb) {
                        cb.click();
                        let sBtn = w.document.querySelector('img[src*="btn_search"], a[onclick*="doSearch"]');
                        if (sBtn) sBtn.click(); else if (typeof w.doSearch === 'function') w.doSearch();
                        return true;
                    }
                    for (let j = 0; j < w.frames.length; j++) {
                        if (selectArea(w.frames[j])) return true;
                    }
                } catch (e) { return false; }
                return false;
            }
            return selectArea(window);
        """)
        if area_found:
            print(f"✅ 世田谷区を選択完了 (試行 {i+1}回目)")
            break
        print(f"   ...検索画面の読み込み待ち ({i+1}/5)")

    if not area_found:
        driver.save_screenshot("area_selection_error.png")
        print("❌ エリア選択に失敗しました。")
        return False

    # --- 🪟 ウィンドウ切り替え ---
    main_handle = driver.current_window_handle
    for _ in range(15):
        if len(driver.window_handles) > 1:
            driver.switch_to.window([h for h in driver.window_handles if h != main_handle][0])
            print(f"🪟 検索結果ウィンドウに切り替えました: {driver.title}")
            break
        time.sleep(1)

    # --- 🔎 空室スキャン ---
    print("🔎 空室情報を最終スキャン中...")
    time.sleep(7)
    found_vacant = driver.execute_script("""
        function scan(w) {
            try {
                const keywords = ['DK', 'LDK', '1DK', '2DK', '1LDK', '2LDK', 'K', '詳細', '物件'];
                let bodyText = w.document.body.innerText.toUpperCase();
                if (keywords.some(k => bodyText.includes(k))) return true;
                for (let i = 0; i < w.frames.length; i++) {
                    if (scan(w.frames[i])) return true;
                }
            } catch (e) {}
            return false;
        }
        return scan(window);
    """)
    return found_vacant

def main():
    driver = setup_driver()
    wait = WebDriverWait(driver, 45)
    try:
        if login_and_check(driver, wait):
            print("🚨 ターゲット条件の空室を発見しました！")
            requests.post(DISCORD_WEBHOOK_URL, json={
                "content": "🏠 **JKK世田谷区：空室あり！**\\n今すぐ確認してください！\\nhttps://jhomes.to-kousya.or.jp/search/jkknet/pc/mypage"
            })
        else:
            print("👀 現在、世田谷区に空室はありません。")
    except Exception as e:
        print(f"❌ 予期せぬエラーが発生しました: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
