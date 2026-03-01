import os
import sys
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def find_and_fill_login(driver, jkk_id, jkk_pw):
    """ログインフォームを探索して入力"""
    inputs = driver.find_elements(By.TAG_NAME, "input")
    text_fields = [i for i in inputs if i.is_displayed() and i.get_attribute("type") in ["text", "password", "tel"]]
    if len(text_fields) >= 2:
        driver.execute_script("arguments[0].value = arguments[1];", text_fields[0], jkk_id)
        driver.execute_script("arguments[0].value = arguments[1];", text_fields[1], jkk_pw)
        buttons = driver.find_elements(By.TAG_NAME, "a")
        for b in buttons:
            if "btn_login" in (b.get_attribute("innerHTML") or ""):
                driver.execute_script("arguments[0].click();", b)
                return True
        text_fields[1].submit()
        return True
    
    frames = driver.find_elements(By.TAG_NAME, "iframe")
    for i in range(len(frames)):
        try:
            driver.switch_to.frame(i)
            if find_and_fill_login(driver, jkk_id, jkk_pw): return True
            driver.switch_to.parent_frame()
        except: continue
    return False

def main():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    driver = create_driver()
    
    try:
        log("🚪 手順1: ログインページへアクセス")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        
        # ウィンドウ切り替え
        WebDriverWait(driver, 20).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(10)
        
        log("⌨️ 手順2: ログイン試行")
        find_and_fill_login(driver, JKK_ID, JKK_PASSWORD)
        time.sleep(12)
        
        # --- 手順3: 条件から検索をクリック ---
        log("🔍 手順3: 「条件から検索」ボタンをクリックします")
        driver.switch_to.default_content() # 一旦親に戻る
        
        # 再帰的にボタンを探してクリック
        found_search = False
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        for i in range(len(frames)):
            try:
                driver.switch_to.frame(i)
                btns = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_search_cond')]/parent::a")
                if btns:
                    driver.execute_script("arguments[0].click();", btns[0])
                    found_search = True
                    break
                driver.switch_to.parent_frame()
            except: continue
        
        if not found_search:
            driver.save_screenshot("error_no_btn.png")
            raise Exception("条件から検索ボタンが見つかりませんでした")

        time.sleep(8)
        log("📍 手順4: 世田谷区を選択して検索実行")
        
        # 世田谷区のチェックボックスを探してクリック
        driver.switch_to.default_content()
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        for i in range(len(frames)):
            try:
                driver.switch_to.frame(i)
                # 世田谷区というテキストを持つ要素、またはその隣のチェックボックス
                targets = driver.find_elements(By.XPATH, "//*[contains(text(), '世田谷区')]")
                if targets:
                    driver.execute_script("arguments[0].click();", targets[0])
                    log("✅ 世田谷区を選択しました")
                    
                    # 検索実行（Enter相当）
                    submit_img = driver.find_element(By.XPATH, "//img[contains(@src, 'btn_search') and not(contains(@src, 'cond'))]")
                    driver.execute_script("arguments[0].click();", submit_img.find_element(By.XPATH, "./parent::a"))
                    log("🚀 検索を実行しました")
                    break
                driver.switch_to.default_content()
            except: continue

        time.sleep(10)
        driver.save_screenshot("final_result.png")
        log("🏁 プロセス完了。結果を保存しました。")

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        driver.save_screenshot("fatal_error_final.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
