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
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def main():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    
    driver = create_driver()
    wait = WebDriverWait(driver, 20)
    
    try:
        log("🚪 手順1: ログイン開始ページへアクセス")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        
        # 🔄 ウィンドウ切り替え
        log("⏳ 新しいウィンドウの生成を待機中...")
        wait.until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        log("🔄 新しいウィンドウに切り替え完了")
        
        # フォーム描画待ち
        time.sleep(5)
        
        # ⌨️ iframeの探索とスイッチ
        log("⌨️ 手順3: ログインフォームを探索")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        log(f"発見されたiframe数: {len(frames)}")

        found = False
        for i, frame in enumerate(frames):
            driver.switch_to.frame(frame)
            try:
                # uidが見えるまで最大15秒待機
                u_field = WebDriverWait(driver, 15).until(
                    EC.visibility_of_element_located((By.NAME, "uid"))
                )
                p_field = driver.find_element(By.NAME, "passwd")
                
                log(f"✅ iframe[{i}] 内でログインフォームを特定しました。")
                
                # 入力と送信
                driver.execute_script("arguments[0].value = arguments[1];", u_field, JKK_ID)
                driver.execute_script("arguments[0].value = arguments[1];", p_field, JKK_PASSWORD)
                
                driver.save_screenshot("debug_before_submit.png")
                
                # ログインボタンをクリック（またはformをsubmit）
                try:
                    login_btn = driver.find_element(By.XPATH, "//img[contains(@src, 'btn_login') or @alt='ログイン']/parent::a")
                    login_btn.click()
                except:
                    p_field.submit()
                
                found = True
                break
            except Exception as e:
                driver.switch_to.default_content()

        if not found:
            raise Exception("ログインフィールドが見つかりませんでした。")

        # 🎉 最終確認
        log("🚀 ログイン処理中...")
        time.sleep(10)
        driver.save_screenshot("debug_after_login.png")
        log(f"最終URL: {driver.current_url}")

        if "mypage" in driver.current_url.lower():
            log("🎉 ログイン成功！")
        else:
            log("⚠️ ログイン後のURLがマイページではありません。")

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        driver.save_screenshot("fatal_error.png")
    finally:
        driver.quit()
        log("🏁 プロセス終了")

if __name__ == "__main__":
    main()
