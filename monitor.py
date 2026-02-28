import os, time, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- 設定 ---
# 枠組みを無視して、ログインフォーム本体があるURLを直接指定
LOGIN_CORE_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"
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
    # 完全に人間になりすますためのUA設定
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def login_and_check(driver):
    print(f"🎯 ログインフォーム本体へ直撃: {LOGIN_CORE_URL}")
    driver.get(LOGIN_CORE_URL)
    time.sleep(10)

    # 現在のページにある全テキストを確認（デバッグ用）
    body_text = driver.find_element(By.TAG_NAME, "body").text
    print(f"📊 ページ内テキスト(先頭100文字): {body_text[:100].replace('\\n', ' ')}")

    # 1. ID/PASS入力
    print("⌨️ ID/PASSを入力中...")
    status = driver.execute_script("""
        const jkk_id = arguments[0];
        const jkk_pass = arguments[1];
        
        // 1. 直接 document から探す
        let uid = document.querySelector('input[name*="uid"], input[id*="uid"], input[name*="user"]');
        let upw = document.querySelector('input[type="password"]');
        let btn = document.querySelector('img[src*="login"], input[type="submit"], .btn_login');

        if (uid && upw) {
            uid.value = jkk_id;
            upw.value = jkk_pass;
            if (btn) { btn.click(); return "SUCCESS_CLICK"; }
            if (uid.form) { uid.form.submit(); return "SUCCESS_SUBMIT"; }
        }
        
        // 2. フレームの中も念のため探す
        for (let i = 0; i < window.frames.length; i++) {
            try {
                let fuid = window.frames[i].document.querySelector('input[name*="uid"]');
                let fupw = window.frames[i].document.querySelector('input[type="password"]');
                if (fuid && fupw) {
                    fuid.value = jkk_id;
                    fupw.value = jkk_pass;
                    window.frames[i].document.forms[0].submit();
                    return "SUCCESS_FRAME_SUBMIT";
                }
            } catch(e) {}
        }
        return "NOT_FOUND";
    """, JKK_ID, JKK_PASS)

    print(f"📊 ログイン処理結果: {status}")
    
    if "SUCCESS" not in status:
        driver.save_screenshot("login_core_failed.png")
        return False

    time.sleep(10)

    # 2. 検索条件画面への遷移を試行
    print("📍 空室検索ボタンをクリック中...")
    # documentから直接「btn_search_cond」などを探す
    found_search = driver.execute_script("""
        let b = Array.from(document.querySelectorAll('a, img')).find(el => 
            el.src?.includes('btn_search_cond') || el.innerText?.includes('空室')
        );
        if (b) { b.click(); return true; }
        return false;
    """)
    
    if not found_search:
        print("⚠️ 検索ボタンが見つかりません。リダイレクトを試みます。")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/vacancy/area")
    
    time.sleep(8)

    # 3. 世田谷区選択
    print("🎯 エリア(世田谷区)を選択中...")
    area_ok = driver.execute_script("""
        let cb = document.querySelector("input[value='113']");
        if (cb) {
            cb.click();
            let b = document.querySelector('img[src*="search"], a[onclick*="doSearch"]');
            if (b) b.click(); else if (window.doSearch) window.doSearch();
            return true;
        }
        return false;
    """)

    if not area_ok:
        driver.save_screenshot("area_failed.png")
        return False

    # 4. 最終スキャン
    time.sleep(10)
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])

    vacant = driver.execute_script("return document.body.innerText.includes('DK') || document.body.innerText.includes('LDK') || document.body.innerText.includes('詳細');")
    return vacant

def main():
    driver = setup_driver()
    try:
        if login_and_check(driver):
            print("🚨 空室を発見しました！")
            requests.post(DISCORD_WEBHOOK_URL, json={"content": "🏠 **JKK世田谷区：空室あり！**"})
        else:
            print("👀 空室はありません。")
    except Exception as e:
        print(f"❌ エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
