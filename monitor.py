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
SEARCH_PAGE = "https://jhomes.to-kousya.or.jp/search/jkknet/service/vacantConditionInit"
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
    # 1. ログイン画面へ直接アクセス
    print("🔑 ログイン開始...")
    driver.get(LOGIN_URL)
    time.sleep(3)

    # 2. ログイン情報の入力
    actions = ActionChains(driver)
    actions.send_keys(Keys.TAB).send_keys(Keys.TAB).send_keys(JKK_ID).send_keys(Keys.TAB).send_keys(JKK_PASS).perform()
    time.sleep(1)
    driver.execute_script("let btn = document.querySelector('img[src*=\"btn_login\"]'); if (btn) btn.click();")
    time.sleep(7)

    # 3. 待機画面を無視して「検索ページ」へ強制遷移（セッション維持）
    print("🚀 検索ページへ直接移動...")
    driver.get(SEARCH_PAGE)
    time.sleep(5)

    # 4. フレームの中から「世田谷区」を執念で探す
    print("🎯 世田谷区のチェックボックスを探します...")
    found = False
    frames = [None] + driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
    
    for f in frames:
        try:
            if f: driver.switch_to.frame(f)
            checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[value='113']")
            if checkboxes:
                driver.execute_script("arguments[0].click();", checkboxes[0])
                print("✅ 世田谷区を選択")
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
        print("❌ 世田谷区が見つかりません。ログインが外れたか、画面構成が違います。")
        return False

    print("⏳ 結果を待機中...")
    time.sleep(10)

    # 5. 空室判定（「世田谷区」と「案内可能」の文字があるかだけを見る）
    content = driver.execute_script("""
        let t=''; 
        function c(w){
            try{t += w.document.body.innerText + '\\n'}catch(e){}
            for(let i=0; i<w.frames.length; i++) c(w.frames[i]);
        } 
        c(window); return t;
    """)
    
    # 詳細はいらないので、キーワードの有無だけで判定
    if "世田谷区" in content and "案内可能" in content:
        if "該当するデータはありません" not in content and "条件に一致する物件はありません" not in content:
            return True # 空室あり！
    
    return False # 空室なし

def main():
    driver = setup_driver()
    wait = WebDriverWait(driver, 20)
    try:
        if login_and_check(driver, wait):
            print("🚨 空室発見！通知します。")
            requests.post(DISCORD_WEBHOOK_URL, json={"content": "🏠 **JKK世田谷区：空室あり！** 今すぐ確認してください！\nhttps://jhomes.to-kousya.or.jp/search/jkknet/service/vacantConditionInit"})
        else:
            print("👀 空室はありませんでした。")
    except Exception as e:
        print(f"❌ エラー発生: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
