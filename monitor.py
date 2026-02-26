import os, time, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- 設定 ---
LOGIN_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"
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
        # 1. ログインページへアクセス
        print("🔑 ログイン開始...")
        driver.get(LOGIN_URL)
        
        # 2. ログイン情報の入力
        user_input = wait.until(EC.presence_of_element_located((By.NAME, "userid")))
        pass_input = driver.find_element(By.NAME, "passwd")
        
        user_input.send_keys(JKK_ID)
        pass_input.send_keys(JKK_PASS)
        
        print("📝 ログイン実行...")
        driver.execute_script("document.querySelector('img[src*=\"btn_login\"]').click();")
        
        # 3. メニュー画面での待機と検索画面への遷移
        time.sleep(10)
        print("📍 メニューから検索画面へ移動中...")
        
        driver.execute_script("""
            let btn = Array.from(document.querySelectorAll('a, img, input')).find(el => 
                (el.innerText && el.innerText.includes('空室')) || 
                (el.src && el.src.includes('btn_search_cond')) ||
                (el.onclick && el.onclick.toString().includes('submitNext'))
            );
            if(btn) btn.click();
            else if(typeof submitNext === 'function') submitNext();
        """)
        
        # 4. 検索条件画面で世田谷区(113)を選択
        time.sleep(10)
        print("🎯 エリア選択（世田谷区）...")
        found_checkbox = False
        
        # フレーム内を全探索
        all_frames = [None] + driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
        for f in all_frames:
            try:
                if f: driver.switch_to.frame(f)
                cb = driver.find_elements(By.CSS_SELECTOR, "input[value='113']")
                if cb:
                    driver.execute_script("arguments[0].click();", cb[0])
                    print("✅ 世田谷区を選択完了")
                    
                    # 検索ボタンクリック
                    search_btn = driver.find_elements(By.CSS_SELECTOR, "img[src*='btn_search']")
                    if search_btn:
                        driver.execute_script("arguments[0].click();", search_btn[0])
                        found_checkbox = True
                        break
            except: pass
            finally: driver.switch_to.default_content()

        if not found_checkbox:
            print(f"❌ エリア選択に失敗しました。現在のタイトル: {driver.title}")
            return

        # 5. 結果表示と判定
        print("⏳ 検索結果を待機中...")
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

        # 画像で確認された条件で判定
        if "世田谷区" in full_text and ("詳細" in full_text or "案内可能" in full_text):
            if "該当するデータはありません" not in full_text:
                print("🚨 空室を発見しました！")
                requests.post(DISCORD_WEBHOOK_URL, json={
                    "content": "🏠 **【JKK世田谷区】空室あり！**\n今すぐ確認してください！\nhttps://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"
                })
                return

        print("👀 空室は見つかりませんでした。")

    except Exception as e:
        print(f"❌ エラー詳細: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
