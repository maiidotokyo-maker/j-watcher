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
    
    # 修正：文法エラーを解消
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def find_and_fill_login(driver, jkk_id, jkk_pw):
    """現在の階層、およびその配下の全iframeを再帰的に探索してログイン試行"""
    # 1. 現在の階層でinputを探す
    inputs = driver.find_elements(By.TAG_NAME, "input")
    text_fields = [i for i in inputs if i.is_displayed() and i.get_attribute("type") in ["text", "password", "tel"]]
    
    if len(text_fields) >= 2:
        log(f"✨ 入力フィールドを発見。ID={jkk_id[:3]}*** を入力します。")
        driver.execute_script("arguments[0].value = arguments[1];", text_fields[0], jkk_id)
        driver.execute_script("arguments[0].value = arguments[1];", text_fields[1], jkk_pw)
        
        # ログインボタンを探してクリック
        buttons = driver.find_elements(By.TAG_NAME, "a")
        for b in buttons:
            onclick = b.get_attribute("onclick") or ""
            href = b.get_attribute("href") or ""
            html = b.get_attribute("innerHTML") or ""
            if "login" in onclick.lower() or "login" in href.lower() or "btn_login" in html:
                log("🖱️ ログインボタンをクリックします")
                driver.execute_script("arguments[0].click();", b)
                return True
        
        log("⌨️ ボタンが見つからないため、Enterキー送信を試みます")
        text_fields[1].submit()
        return True

    # 2. 子iframeを探索
    child_frames = driver.find_elements(By.TAG_NAME, "iframe")
    for i in range(len(child_frames)):
        try:
            driver.switch_to.frame(i)
            if find_and_fill_login(driver, jkk_id, jkk_pw):
                return True
            driver.switch_to.parent_frame()
        except:
            continue
    
    return False

def main():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    
    driver = create_driver()
    wait = WebDriverWait(driver, 20)
    
    try:
        log("🚪 手順1: ログイン開始ページへアクセス")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        
        # ウィンドウ切り替え
        wait.until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        log("🔄 新しいウィンドウに切り替え完了")
        
        time.sleep(10)
        
        log("⌨️ 手順3: ログインフォームを再帰的に探索開始")
        
        if find_and_fill_login(driver, JKK_ID, JKK_PASSWORD):
            log("🚀 ログイン情報を送信しました。")
            time.sleep(10)
            driver.save_screenshot("debug_after_submit.png")
            log(f"最終URL: {driver.current_url}")
            
            if "mypage" in driver.current_url.lower():
                log("🎉 ログイン成功！")
            else:
                log("⚠️ ログイン後のURLがマイページではありません。")
        else:
            driver.save_screenshot("debug_not_found.png")
            raise Exception("再帰探索の結果、入力フィールドが見つかりませんでした。")

    except Exception as e:
        log(f"❌ エラー発生: {e}")
    finally:
        driver.quit()
        log("🏁 プロセス終了")

if __name__ == "__main__":
    main()
