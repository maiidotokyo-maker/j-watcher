import sys
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
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
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,1024')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        log("🚪 玄関ページを開きます...")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/")
        time.sleep(3)
        
        log("🔧 直接ログインURLへ遷移します...")
        # 余計なJSフックをやめ、URL直接叩きに変更
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin")
        time.sleep(5)
        
        log(f"📄 現在のURL: {driver.current_url}")
        log(f"📄 タイトル: {driver.title}")
        
        u = driver.find_elements(By.NAME, "uid")
        
        if not u:
            # フレーム探索
            frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(frames)):
                driver.switch_to.frame(i)
                u = driver.find_elements(By.NAME, "uid")
                if u:
                    log(f"🎯 第{i}フレームでフォームを発見！")
                    break
                driver.switch_to.default_content()

        if u:
            log("🔑 ID/PWを注入します...")
            u[0].send_keys(os.environ.get("JKK_ID"))
            driver.find_element(By.NAME, "passwd").send_keys(os.environ.get("JKK_PASSWORD"))
            
            btn = driver.find_elements(By.XPATH, "//input[@type='image']|//img[contains(@src,'login')]")
            if btn: btn[0].click()
            else: driver.find_element(By.NAME, "passwd").submit()
            
            time.sleep(8)
            log(f"✅ ログイン完了後のURL: {driver.current_url}")
        else:
            log("🚨 フォームが見つかりません。サーバーが返した【生のHTML】をすべて表示します:")
            log("================= HTML START =================")
            log(driver.page_source)
            log("================= HTML END ===================")

    except Exception as e:
        log(f"❌ エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
