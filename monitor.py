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
        
        log("🔧 別窓で開く処理を強制的に『同じ画面で開く』ように書き換えます")
        # サイトの window.open を上書きして、現在のタブで強引に遷移させる
        driver.execute_script("""
            window.open = function(url, name, features) {
                window.location.href = url || '/search/jkknet/pc/mypageLogin';
                return null;
            };
        """)
        
        log("🖱️ ログイン処理を発動")
        # ここで関数を呼ぶと、別窓ではなく今の画面のままログインページへ飛ぶ
        driver.execute_script("if(typeof mypageLogin === 'function') { mypageLogin(); } else { window.location.href = '/search/jkknet/pc/mypageLogin'; }")
        
        time.sleep(5)
        log(f"📄 現在のURL: {driver.current_url}")
        
        # フォームを探す（フレームの中に隠れている場合も想定）
        u = driver.find_elements(By.NAME, "uid")
        
        if not u:
            # フレームがあれば全部順番に覗き込む
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
            if btn:
                btn[0].click()
            else:
                driver.find_element(By.NAME, "passwd").submit()
            
            time.sleep(8)
            log(f"✅ ログイン完了後のURL: {driver.current_url}")
            log(f"📄 最終タイトル: {driver.title}")
        else:
            log("🚨 フォームが見つかりませんでした。画面に表示されている文字を抽出します:")
            # なぜ失敗したか（おわびなのか、別エラーなのか）をログに出す
            log(driver.find_element(By.TAG_NAME, "body").text[:200])

    except Exception as e:
        log(f"❌ エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
