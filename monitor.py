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
        # 1. 玄関へ
        log("🚪 アクセス開始")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/")
        time.sleep(5)

        # 2. ログインボタンを普通にクリック
        log("🖱️ ログインボタンをクリック")
        btn = driver.find_element(By.XPATH, "//img[contains(@src, 'btn_login')]|//a[contains(@onclick, 'mypageLogin')]")
        btn.click()
        time.sleep(10)

        # 3. 窓が分かれたら切り替える（これだけ！）
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
        
        log(f"📄 現在のページ: {driver.title}")

        # 4. フォーム入力（あれば入力、なければ終了）
        u = driver.find_elements(By.NAME, "uid")
        if u:
            log("🎯 フォーム発見")
            u[0].send_keys(os.environ.get("JKK_ID"))
            driver.find_element(By.XPATH, "//input[@type='password']").send_keys(os.environ.get("JKK_PASSWORD"))
            driver.find_element(By.XPATH, "//input[@type='image']|//img[contains(@src,'login')]").click()
            time.sleep(5)
            log(f"✅ 完了URL: {driver.current_url}")
        else:
            log("🚨 フォームなし（おわび等）")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
