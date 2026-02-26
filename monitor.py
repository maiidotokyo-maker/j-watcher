import os, time, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- 設定 ---
# 玄関口となるトップページ
TOP_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/index.html"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
JKK_ID = os.environ.get("JKK_ID", "").strip()
JKK_PASS = os.environ.get("JKK_PASSWORD", "").strip()

def setup_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = setup_driver()
    wait = WebDriverWait(driver, 30)
    
    try:
        # 1. 玄関（トップページ）から入る
        print("🌐 トップページにアクセスして「おわび」を回避中...")
        driver.get(TOP_URL)
        time.sleep(3)
        
        # 2. ログインボタンを探してクリック（これで正規セッションが開始される）
        print("🔑 ログインボタンをクリック...")
        login_nav = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "img[src*='btn_login'], a[href*='mypageLogin']")))
        driver.execute_script("arguments[0].click();", login_nav)
        
        # 3. ログインフォームの入力
        print("⏳ フォーム待機中...")
        user_input = wait.until(EC.presence_of_element_located((By.NAME, "userid")))
        # inputのtype="password"を指定することでpasswd/password表記ブレを回避
        pass_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        
        user_input.send_keys(JKK_ID)
        pass_input.send_keys(JKK_PASS)
        print("📝 ログイン情報を送信...")
        driver.execute_script("document.querySelector('img[src*=\"btn_login\"]').click();")
        
        # 4. メニュー画面（同じタブで遷移）
        time.sleep(10)
        print("📍 メニュー画面。条件入力へ...")
        driver.execute_script("""
            let btn = Array.from(document.querySelectorAll('a, img, input')).find(el => 
                (el.innerText && el.innerText.includes('空室')) || 
                (el.src && el.src.includes('btn_search_cond'))
            );
            if(btn) {
                if(btn.tagName === 'A') btn.target = "_self";
                btn.click();
            }
        """)
        
        # 5. 世田谷区(113)を選択
        time.sleep(10)
        print("🎯 世田谷区を選択中...")
        found_checkbox = False
        all_frames = [None] + driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
        
        for f in all_frames:
            try:
                if f: driver.switch_to.frame(f)
                cb = driver.find_elements(By.CSS_SELECTOR, "input[value='113']")
                if cb:
                    driver.execute_script("arguments[0].click();", cb[0])
                    search_btn = driver.find_elements(By.CSS_SELECTOR, "img[src*='btn_search']")
                    if search_btn:
                        driver.execute_script("arguments[0].click();", search_btn[0])
                        found_checkbox = True
                        print("✅ 世田谷区を選択して検索開始")
                        break
            except: pass
            finally: driver.switch_to.default_content()

        if not found_checkbox:
            print(f"❌ エリア選択に失敗。現在のタイトル: {driver.title}")
            return

        # 6. 結果判定
        print("⏳ 検索結果を読み込み中（15秒）...")
        time.sleep(15)
        
        full_text = driver.execute_script("""
            let t = '';
            function scan(w) {
                try { t += w.document.body.innerText + '\\n'; } catch(e) {}
                for (let i = 0; i < w.frames.length; i++) scan(w.frames[i]);
            }
            scan(window);
            return t;
        """)

        # 画像の「詳細」または「案内可能」ボタンを検知
        if "世田谷区" in full_text and ("詳細" in full_text or "案内可能" in full_text):
            if "該当するデータはありません" not in full_text:
                print("🚨 空室を確認！通知します。")
                requests.post(DISCORD_WEBHOOK_URL, json={
                    "content": "🏠 **【JKK世田谷区】空室あり！**\\n画像で確認された物件が出ています。至急確認してください！\\nhttps://jhomes.to-kousya.or.jp/search/jkknet/pc/index.html"
                })
                return

        print("👀 空室はありませんでした。")

    except Exception as e:
        print(f"❌ エラー詳細: {e}")
        # デバッグ用にその時のURLとタイトルを表示
        try:
            print(f"📄 最終URL: {driver.current_url}")
            print(f"📄 最終タイトル: {driver.title}")
        except: pass
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
