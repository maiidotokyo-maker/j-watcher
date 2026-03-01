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
    options.add_argument("--disable-popup-blocking")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def find_and_fill_login(driver, jkk_id, jkk_pw):
    inputs = driver.find_elements(By.TAG_NAME, "input")
    text_fields = [i for i in inputs if i.is_displayed() and i.get_attribute("type") in ["text", "password", "tel"]]
    if len(text_fields) >= 2:
        log("✨ ログインフォームを発見。入力中...")
        driver.execute_script("arguments[0].value = arguments[1];", text_fields[0], jkk_id)
        driver.execute_script("arguments[0].value = arguments[1];", text_fields[1], jkk_pw)
        buttons = driver.find_elements(By.TAG_NAME, "a")
        for b in buttons:
            html = b.get_attribute("innerHTML") or ""
            if "btn_login" in html or "ログイン" in html:
                driver.execute_script("arguments[0].click();", b)
                return True
        text_fields[1].submit()
        return True
    child_frames = driver.find_elements(By.TAG_NAME, "iframe")
    for i in range(len(child_frames)):
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
    wait = WebDriverWait(driver, 20)
    
    try:
        log("🚪 手順1: ログインページへアクセス")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        wait.until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(10)
        
        log("⌨️ 手順2: ログイン試行")
        if find_and_fill_login(driver, JKK_ID, JKK_PASSWORD):
            time.sleep(12)
            log("🔍 手順3: 「条件から検索」ボタンを探索")
            
            # マイページ内のボタンを探す
            search_btn = None
            frames = driver.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(frames)):
                driver.switch_to.frame(i)
                btns = driver.find_elements(By.XPATH, "//img[contains(@src, 'btn_search_cond')]/parent::a")
                if btns:
                    search_btn = btns[0]
                    driver.execute_script("arguments[0].click();", search_btn)
                    log("🎯 検索ボタンをクリックしました")
                    break
                driver.switch_to.default_content()

            if not search_btn:
                raise Exception("検索ボタンが見つかりません")

            time.sleep(8)
            log("📍 手順4: 世田谷区を選択中...")
            
            # 世田谷区(113などのコードに関連)を選択
            # JKKの検索画面はiframe構造が続くため、再度フレーム内を探索
            driver.switch_to.default_content()
            frames = driver.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(frames)):
                driver.switch_to.frame(i)
                try:
                    # 「世田谷区」のラベルまたはチェックボックスを探す
                    target = driver.find_element(By.XPATH, "//*[contains(text(), '世田谷区')]")
                    driver.execute_script("arguments[0].click();", target)
                    log("✅ 世田谷区を選択しました")
                    break
                except:
                    driver.switch_to.default_content()

            log("🖱️ 手順5: 検索実行")
            submit_img = driver.find_element(By.XPATH, "//img[contains(@src, 'btn_search') and not(contains(@src, 'cond'))]")
            driver.execute_script("arguments[0].click();", submit_img.find_element(By.XPATH, "./parent::a"))
            
            time.sleep(10)
            driver.save_screenshot("final_result.png")
            log(f"🏁 完了。最終URL: {driver.current_url}")
            
            # 結果に「該当する物件はありません」が含まれているかチェック
            if "該当する物件はありません" in driver.page_source:
                log("ℹ️ 現在、世田谷区に空室はありません。")
            else:
                log("📢 空室がある可能性があります！スクリーンショットを確認してください。")

    except Exception as e:
        log(f"❌ エラー: {e}")
        driver.save_screenshot("error_search.png")
    finally:
        driver.quit()
        log("🏁 プロセス終了")

if __name__ == "__main__":
    main()
