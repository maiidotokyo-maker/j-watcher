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
    time.sleep(5)

    # 【デバッグ】要素検出チェック（ユーザー提案のコードを強化）
    print("🧪 ログイン要素の検出テスト...")
    status = driver.execute_script(f"""
        function findAndFill(w) {{
            try {{
                let uid = w.document.querySelector('input[id*="user"], input[name*="user"]');
                let upw = w.document.querySelector('input[type="password"]');
                let btn = w.document.querySelector('img[src*="btn_login"], input[src*="btn_login"], a[onclick*="login"]');
                
                if (uid && upw) {{
                    uid.value = "{JKK_ID}";
                    upw.value = "{JKK_PASS}";
                    if (btn) btn.click();
                    return "SUCCESS";
                }}
                for (let i = 0; i < w.frames.length; i++) {{
                    let res = findAndFill(w.frames[i]);
                    if (res === "SUCCESS") return "SUCCESS";
                }}
            } catch(e) {{}}
            return "NOT_FOUND";
        }}
        return findAndFill(window);
    """)
    print(f"📊 ログイン試行結果: {status}")

    # 2. ログイン成否の判定
    try:
        wait.until(lambda d: d.execute_script("return document.body.innerText.includes('ログアウト') || document.body.innerText.includes('メニュー')"))
        print("✅ ログイン成功を確認しました。")
    except:
        driver.save_screenshot("login_error.png")
        print("❌ ログイン失敗。画面を確認してください。")
        return False

    # 3. 検索画面へ移動（メニューボタンをクリック）
    print("📍 メニューから検索画面へ移動中...")
    driver.execute_script("""
        let btn = Array.from(document.querySelectorAll('a, img, input')).find(el => 
            (el.innerText && el.innerText.includes('空室')) || (el.src && el.src.includes('btn_search_cond'))
        );
        if(btn) btn.click(); else if(typeof submitNext === 'function') submitNext();
    """)
    
    # 4. エリア選択（世田谷区）- 粘り強くリトライ
    print("🎯 エリア選択（世田谷区）を実行中...")
    area_found = False
    for i in range(6): # 最大30秒待機
        time.sleep(5)
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
        print(f"   ...読み込み待ちリトライ中 ({i+1}/6)")

    if not area_found:
        driver.save_screenshot("area_error.png")
        return False

    # 5. ウィンドウ切り替え
    main_handle = driver.current_window_handle
    for _ in range(15):
        if len(driver.window_handles) > 1:
            driver.switch_to.window([h for h in driver.window_handles if h != main_handle][0])
            break
        time.sleep(1)

    # 6. 空室スキャン
    print("🔎 スキャン中...")
    time.sleep(5)
    res = driver.execute_script("""
        function scan(w) {
            try {
                const keywords = ['DK', 'LDK', '1DK', '2DK', '1LDK', '2LDK', 'K', '詳細', '物件'];
                if (keywords.some(k => w.document.body.innerText.toUpperCase().includes(k))) return true;
                for (let i = 0; i < w.frames.length; i++) {
                    if (scan(w.frames[i])) return true;
                }
            } catch (e) {}
            return false;
        }
        return scan(window);
    """)
    return res

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
            print("👀 空室なし。")
    except Exception as e:
        print(f"❌ エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
