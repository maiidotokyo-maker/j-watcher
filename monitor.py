import os
import sys
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # 🕵️ 重要：より人間らしいUser-Agentと各種偽装
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    options.add_argument(f'--user-agent={ua}')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # 🛡️ webdriverプロパティを削除してボット検知を回避
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', {get: () => ['ja-JP', 'ja']});
        """
    })
    return driver

def main():
    driver = create_driver()
    wait = WebDriverWait(driver, 30)

    try:
        # 手順1: トップから正規Cookie取得
        log("🚪 手順1: トップページへアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        time.sleep(5)

        # 手順2: ログインページへ（JS遷移ではなく、クリックを模倣）
        log("🔗 手順2: ログインページへ遷移")
        # 直接URL指定が弾かれている可能性があるため、再度トップからの物理クリックを試行（JS使用）
        driver.execute_script("window.location.href = 'https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu';")
        
        # ロード時間をさらに長くし、画面内をスクロールして「人間」を装う
        log("⏳ ロード待機 + 擬似操作中...")
        for _ in range(3):
            time.sleep(10)
            driver.execute_script("window.scrollBy(0, 100);")
        
        driver.save_screenshot("debug_login_check.png")

        # 📄 デバッグ：現在のHTML構造を詳しくログ出力
        page_content = driver.page_source
        if "iframe" not in page_content.lower():
            log("⚠️ 警告: iframeタグ自体がページ内に存在しません。JSがブロックされた可能性があります。")
            print(f"DEBUG HTML SNIPPET: {page_content[1000:2000]}") # 中央付近を抽出

        # 手順3: iframe探索
        log("⌨️ 手順3: ログインフォームを探索")
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        log(f"発見されたiframe数: {len(frames)}")

        for i, frame in enumerate(frames):
            driver.switch_to.frame(frame)
            try:
                # presenceではなく、より強い判定「visibility」を使用
                u_field = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.NAME, "uid")))
                log(f"✅ iframe[{i}] 内でログインフォームを表示確認")
                
                driver.execute_script("arguments[0].value = arguments[1];", u_field, os.environ.get("JKK_ID"))
                p_field = driver.find_element(By.NAME, "passwd")
                driver.execute_script("arguments[0].value = arguments[1];", p_field, os.environ.get("JKK_PASSWORD"))
                
                driver.save_screenshot("debug_submitting.png")
                p_field.submit()
                
                # ログイン後の成功確認
                wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'マイページ')]")))
                log("🎉 ログイン成功！")
                return
            except:
                driver.switch_to.default_content()

        raise Exception("ログインフォームの描画に失敗しました。")

    except Exception as e:
        log(f"❌ エラー: {e}")
        driver.save_screenshot("final_error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
