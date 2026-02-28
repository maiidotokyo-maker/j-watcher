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

def find_button_recursive(driver):
    # 今いる階層でボタンを探す
    btns = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_login')]|//a[contains(@onclick, 'mypageLogin')]")
    if btns:
        return btns[0]
    
    # 子フレームを順番に潜って探す
    frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
    for i in range(len(frames)):
        try:
            driver.switch_to.frame(i)
            found = find_button_recursive(driver)
            if found: return found
            driver.switch_to.parent_frame()
        except:
            continue
    return None

def main():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        log("🚪 玄関ページにアクセス")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/")
        time.sleep(5)

        # フレームを潜り倒してボタンを探す
        btn = find_button_recursive(driver)

        if btn:
            log("🎯 ボタン発見、クリックします")
            btn.click()
            time.sleep(10)
            
            # 別窓へ移動
            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[-1])
            
            log(f"📄 到着: {driver.title}")

            # ログイン入力
            u = driver.find_elements(By.NAME, "uid")
            if u:
                u[0].send_keys(os.environ.get("JKK_ID"))
                driver.find_element(By.NAME, "passwd").send_keys(os.environ.get("JKK_PASSWORD"))
                driver.find_element(By.XPATH, "//input[@type='image']|//img[contains(@src,'login')]").click()
                time.sleep(5)
                log(f"✅ ログイン後のURL: {driver.current_url}")
        else:
            log("🚨 迷宮の奥底にもボタンがありませんでした")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
