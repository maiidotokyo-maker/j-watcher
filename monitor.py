import sys
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

sys.stdout.reconfigure(encoding='utf-8')
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def main():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    # 完全に「人間」のフリをするためのUser-Agent
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        log("🚪 手順1: 玄関（TOP）に立ちます")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/")
        time.sleep(5) # ページが落ち着くまで待機
        
        # 玄関のタイトルを確認
        log(f"🏠 玄関のタイトル: {driver.title}")

        log("🖱️ 手順2: ログインボタンにマウスを載せて『物理クリック』")
        try:
            # onclick="mypageLogin()" を持つ要素を特定
            login_btn = driver.find_element(By.XPATH, "//*[@onclick[contains(.,'mypageLogin')]]")
            
            # 人間のように「マウスを動かしてクリック」
            actions = ActionChains(driver)
            actions.move_to_element(login_btn).click().perform()
            log("👉 クリック完了。窓が開くのを待ちます...")
        except Exception as e:
            log(f"🚨 ボタンが見つかりません。強引にJSを叩きます: {e}")
            driver.execute_script("mypageLogin();")

        # 手順3: 窓が2つになるまで、最大15秒間、人間が待つように小刻みにチェック
        for i in range(30):
            if len(driver.window_handles) > 1:
                log(f"✨ 手順3: 新しい窓が開きました（{i*0.5}秒後に検知）")
                break
            time.sleep(0.5)

        if len(driver.window_handles) > 1:
            # 手順4: ログイン専用の別窓へ乗り換える
            driver.switch_to.window(driver.window_handles[-1])
            log(f"📑 ログイン窓に移動成功。URL: {driver.current_url}")
            time.sleep(5) # フォームの読み込みを待つ

            log(f"📄 窓のタイトル: {driver.title}")
            
            if "おわび" in driver.title:
                log("💀 無念...手順を踏んでも『おわび』。リファラが欠落しているか、Cookieの初期化に失敗しています。")
            else:
                # 手順5: ログインフォームに入力
                u = driver.find_elements(By.NAME, "uid")
                if u:
                    log("🎯 ターゲット捕捉！ログイン情報を流し込みます")
                    u[0].send_keys(os.environ.get("JKK_ID"))
                    driver.find_element(By.NAME, "passwd").send_keys(os.environ.get("JKK_PASSWORD"))
                    
                    # ログイン実行（送信ボタンを物理クリック）
                    submit_btn = driver.find_element(By.XPATH, "//input[@type='image']|//img[contains(@src,'login')]")
                    submit_btn.click()
                    
                    time.sleep(10)
                    log(f"✅ 最終URL: {driver.current_url}")
                    log(f"📄 最終タイトル: {driver.title}")
                    
                    if "おわび" not in driver.title:
                        log("🎉🎉🎉 ついに『おわび』の迷宮を脱出しました！")
                else:
                    log("🚨 窓は開いたが、uid入力欄が見つかりません。")
        else:
            log("💀 窓が1つのままです。ポップアップがブロックされたか、クリックが効いていません。")

    except Exception as e:
        log(f"❌ 予期せぬエラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
