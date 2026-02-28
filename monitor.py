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
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        log("🚪 玄関ページにアクセス")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/")
        time.sleep(5)

        # フレーム（窓枠）が複数ある可能性があるので、全部順番にチェックする
        frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
        btn = None

        if not frames:
            # フレームがなければ直接探す
            btn = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_login')]|//a[contains(@onclick, 'mypageLogin')]")
        else:
            # フレームを1つずつ覗いてボタンを探す
            for i in range(len(frames)):
                driver.switch_to.frame(i)
                btn = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_login')]|//a[contains(@onclick, 'mypageLogin')]")
                if btn:
                    log(f"🎯 第{i}フレームでボタンを発見")
                    break
                driver.switch_to.default_content()

        if btn:
            btn[0].click()
            time.sleep(10)
            
            # 別窓が開いたらそっちに移動
            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[-1])
            
            log(f"📄 現在のページ: {driver.title}")
            
            # ログイン入力（ここもシンプルに）
            u = driver.find_elements(By.NAME, "uid")
            if u:
                log("🎯 入力開始")
                u[0].send_keys(os.environ.get("JKK_ID"))
                driver.find_element(By.NAME, "passwd").send_keys(os.environ.get("JKK_PASSWORD"))
                driver.find_element(By.XPATH, "//input[@type='image']|//img[contains(@src,'login')]").click()
                time.sleep(5)
                log(f"✅ 到達URL: {driver.current_url}")
        else:
            log("🚨 ログインボタンがどこにも見つかりません")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
