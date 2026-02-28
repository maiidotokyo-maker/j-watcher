import sys
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
    options.add_argument('--window-size=1280,1024')
    # ユーザーエージェントをより一般的に
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # 手順1: ここが重要。サブドメインではなく、大本の www.to-kousya.or.jp から入る。
        log("🚪 手順1: 公社公式サイトのトップ(www)へアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        time.sleep(5)

        # 手順2: 「JKKねっと」へのリンクを物理的に探してクリック
        # これによりブラウザに正規のセッションが紐付きます
        log("🔍 手順2: ページ内の『JKKねっと』ボタンを探します")
        entrance = None
        selectors = [
            "//a[contains(@href, 'jkknet')]",
            "//img[contains(@alt, 'JKKねっと')]/..",
            "//a[contains(text(), '空き家検索')]"
        ]
        
        for sel in selectors:
            els = driver.find_elements(By.XPATH, sel)
            if els:
                entrance = els[0]
                break

        if entrance:
            log(f"🎯 入り口発見（{entrance.get_attribute('href')}）。クリックします。")
            driver.execute_script("arguments[0].click();", entrance)
            time.sleep(5)
            
            # ページ遷移後、ログインボタンを探索
            log("🔍 手順3: ログインボタンの探索")
            login_btn = None
            xpath_list = [
                "//a[contains(@onclick, 'mypageLogin')]",
                "//img[contains(@src, 'login')]/..",
                "//a[contains(text(), 'ログイン')]"
            ]
            
            for xpath in xpath_list:
                btns = driver.find_elements(By.XPATH, xpath)
                if btns:
                    login_btn = btns[0]
                    break
            
            if login_btn:
                log("🚀 ログインボタンをクリック（正規ルート遷移）")
                driver.execute_script("arguments[0].click();", login_btn)
                time.sleep(5)
                
                # ポップアップ対応
                if len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[-1])
                
                log("⌨️ 手順4: ID/PWの投入")
                # ここで見つからなければ、やはり『くじら』が邪魔をしています
                u = driver.find_element(By.NAME, "uid")
                p = driver.find_element(By.NAME, "passwd")
                
                u.send_keys(os.environ.get("JKK_ID"))
                p.send_keys(os.environ.get("JKK_PASSWORD"), Keys.ENTER)
                
                time.sleep(10)
                log(f"📄 最終結果タイトル: {driver.title}")
                if "マイページ" in driver.title or "ログイン" not in driver.title:
                    log("🎉 成功！ついに突破しました！")
                else:
                    log("💀 ログイン失敗（入力内容または手順の不備）")
            else:
                log("🚨 ログインボタンに到達できません。")
                driver.save_screenshot("step_3_fail.png")
        else:
            log("🚨 そもそも公式サイトからJKKねっとへの入り口が見つかりません。")
            driver.save_screenshot("step_2_fail.png")

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        driver.save_screenshot("crash_report.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
