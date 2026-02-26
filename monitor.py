import os, time, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

def login(driver, wait):
    print("🔑 ログイン開始...")
    driver.get(LOGIN_URL)
    time.sleep(3)

    try:
        driver.find_element(By.NAME, "userid").send_keys(JKK_ID)
        driver.find_element(By.NAME, "passwd").send_keys(JKK_PASS)
        time.sleep(1)
        driver.execute_script("let btn = document.querySelector('img[src*=\"btn_login\"]'); if (btn) btn.click();")
        time.sleep(7)

        if "おわび" in driver.title:
            print("❌ ログイン失敗：おわびページに遷移しました")
            return False
        print("✅ ログイン成功！")
        return True
    except Exception as e:
        print(f"❌ ログイン処理中にエラー: {e}")
        return False

def search_setagaya(driver, wait):
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
                driver.execute_script("""
                    let sBtn = document.querySelector('img[src*="btn_search"], a[onclick*="doSearch"]');
                    if(sBtn) sBtn.click(); else if(typeof doSearch === 'function') doSearch();
                """)
                break
        except: pass
        finally: driver.switch_to.default_content()

    if not found:
        print("❌ エリア選択に失敗しました。現在のタイトル:", driver.title)
        return False

    print("⏳ 検索結果を待機中...")
    time.sleep(10)

    content = driver.execute_script("""
        let t=''; 
        function c(w){
            try{t += w.document.body.innerText + '\\n'}catch(e){}
            for(let i=0; i<w.frames.length; i++) c(w.frames[i]);
        } 
        c(window); return t;
    """)

    return (
        "世田谷区" in content and
        "詳細" in content and
        "該当するデータはありません" not in content and
        "条件に一致する物件はありません" not in content
    )

def main():
    driver = setup_driver()
    wait = WebDriverWait(driver, 25)
    try:
        if login(driver, wait):
            if search_setagaya(driver, wait):
                print("🚨 空室を発見しました！")
                requests.post(DISCORD_WEBHOOK_URL, json={
                    "content": "🏠 **JKK世田谷区：空室あり！**\nすぐ確認してください！\nhttps://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"
                })
            else:
                print("👀 空室は見つかりませんでした。")
        else:
            print("🚫 ログインに失敗したため中断します。")
    except Exception as e:
        print(f"❌ エラー発生: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
