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
    options.add_argument('--disable-dev-shm-usage')
    # 履歴を残さない「シークレットモード」をエミュレート
    options.add_argument('--incognito') 
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # 過去のCookieが邪魔をしている可能性を排除するため、全削除
        driver.delete_all_cookies()
        
        log("🧹 全ての過去を消去しました。真っさらな状態で玄関へ向かいます...")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/")
        time.sleep(7)
        
        log(f"🏠 玄関のタイトル: {driver.title}")

        if "おわび" in driver.title:
            log("🚨 まだおわびが出ます。これはIPアドレス自体が一時的にブラックリスト入りしています。")
            log("💡 対策: 1時間ほど放置してIPが変わるのを待つか、別のURLを試します。")
            
            # 最後の悪あがき：URLの末尾にランダムな文字を入れてキャッシュを回避
            log("🔄 最終手段：キャッシュ回避URLで再トライ...")
            driver.get(f"https://jhomes.to-kousya.or.jp/search/jkknet/pc/?dummy={int(time.time())}")
            time.sleep(5)
            log(f"🏠 再トライ後のタイトル: {driver.title}")

        # もし玄関が開いたら、ボタンを探す
        btns = driver.find_elements(By.TAG_NAME, "a")
        log(f"🔍 ページ内のリンク数: {len(btns)}")
        
        for btn in btns:
            if "mypageLogin" in btn.get_attribute("onclick") or "ログイン" in btn.text:
                log("🎯 ボタン発見！")
                driver.execute_script("arguments[0].click();", btn)
                break

    except Exception as e:
        log(f"❌ エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
