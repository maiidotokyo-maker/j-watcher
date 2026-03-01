import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def main():
    driver = create_driver()
    wait = WebDriverWait(driver, 30)

    try:
        # 手順1: まずトップページにアクセスして「正規のCookie」を焼く
        log("🚪 手順1: トップページでCookieを取得")
        driver.get("https://www.to-kousya.or.jp/")
        time.sleep(5)

        # 手順2: ログインページへ直接遷移（リファラをトップページに偽装）
        log("🔗 手順2: リファラを伴ってログインページへ直接アクセス")
        # 直接URLを指定。遷移ボタンが見つからない問題を物理的に回避
        driver.execute_script("window.location.href = 'https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu';")
        
        # JSロードを十分に待つ
        log("⏳ ロード待機（20秒）...")
        time.sleep(20)
        driver.save_screenshot("debug_direct_access.png")

        # 手順3: iframe探索（ここからは従来の最強ロジック）
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        found = False
        for i, frame in enumerate(frames):
            driver.switch_to.frame(frame)
            try:
                u_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "uid")))
                p_field = driver.find_element(By.NAME, "passwd")
                log(f"✅ iframe[{i}] 内にログインフォームを捕捉！")
                
                driver.execute_script("arguments[0].value = arguments[1];", u_field, JKK_ID)
                driver.execute_script("arguments[0].value = arguments[1];", p_field, JKK_PASSWORD)
                p_field.submit()
                found = True
                break
            except:
                driver.switch_to.default_content()

        if not found:
            raise Exception("どのiframe内にもログインフォームが見つかりませんでした。")

        # 成功判定
        wait.until(EC.any_of(EC.url_contains("mypage"), EC.title_contains("マイページ")))
        log("🎉 ログイン成功！")

    except Exception as e:
        log(f"❌ 失敗: {e}")
        driver.save_screenshot("final_error_report.png")
    finally:
        driver.quit()
