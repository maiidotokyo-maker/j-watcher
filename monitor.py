import sys
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

sys.stdout.reconfigure(encoding='utf-8')
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def main():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1280,1024')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # 手順1: ここが生命線。必ず「玄関」から入る。
        log("🚪 手順1: JKKねっとの玄関ページへアクセス")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/")
        time.sleep(5)

        # 手順2: URL移動せず、ページ内のログインボタンを「クリック」する
        log("🔍 手順2: ページ内のログインボタンを物理的に探します")
        # 複数の可能性（aタグ、画像ボタン、onclick属性）を考慮
        login_btn = None
        selectors = [
            "//a[contains(@onclick, 'mypageLogin')]",
            "//area[contains(@onclick, 'mypageLogin')]",
            "//img[contains(@src, 'login')]/..",
            "//a[contains(text(), 'ログイン')]"
        ]
        
        for sel in selectors:
            elements = driver.find_elements(By.XPATH, sel)
            if elements:
                login_btn = elements[0]
                break

        if login_btn:
            log("🎯 ボタン発見。物理クリックを実行します（これで『くじら』を回避）")
            driver.execute_script("arguments[0].click();", login_btn)
            time.sleep(5)
            
            # 別窓が開くタイプの場合、新しい窓に切り替え
            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[-1])
                log(f"📑 ログイン窓に切り替え完了: {driver.current_url}")
            
            # 手順3: ようやく入力（ここまできたら、くじらはいないはず）
            log("⌨️ 手順3: IDとPWを投入します")
            u_field = driver.find_element(By.NAME, "uid")
            p_field = driver.find_element(By.NAME, "passwd")
            
            u_field.clear()
            u_field.send_keys(os.environ.get("JKK_ID"))
            p_field.clear()
            p_field.send_keys(os.environ.get("JKK_PASSWORD"), Keys.ENTER)
            
            log("⏳ ログイン処理の完了を待ちます（10秒）...")
            time.sleep(10)
            
            log(f"✅ 最終URL: {driver.current_url}")
            log(f"📄 最終タイトル: {driver.title}")
            
            if "マイページ" in driver.title or "ログアウト" in driver.page_source:
                log("🎉 ログイン成功！突破しました！")
            else:
                log("💀 ログイン失敗。まだ何かが足りません。")
                driver.save_screenshot("login_result.png")
        else:
            log("🚨 玄関ページにログインボタンが見つかりません。")
            driver.save_screenshot("no_button_at_entrance.png")

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        driver.save_screenshot("crash.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
