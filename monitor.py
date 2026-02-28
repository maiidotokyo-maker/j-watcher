import os, time, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- 設定 ---
START_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
JKK_ID = os.environ.get("JKK_ID", "").strip()
JKK_PASS = os.environ.get("JKK_PASSWORD", "").strip()

def setup_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1280,1024')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def find_and_fill_recursive(driver, jkk_id, jkk_pass):
    """
    今いる階層および、すべてのサブフレームの中から入力欄を探して入力する（再帰関数）
    """
    try:
        # 1. 今の階層で探す
        uids = driver.find_elements(By.XPATH, "//input[contains(@name, 'uid') or contains(@id, 'uid') or contains(@name, 'user') or contains(@id, 'user')]")
        pws = driver.find_elements(By.XPATH, "//input[@type='password']")
        
        if uids and pws:
            uids[0].send_keys(jkk_id)
            pws[0].send_keys(jkk_pass)
            pws[0].submit()
            return True
        
        # 2. 子フレームを順番に潜って探す
        frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
        for i in range(len(frames)):
            # indexで指定しないと、切り替え後に要素が失効するため
            driver.switch_to.frame(i)
            if find_and_fill_recursive(driver, jkk_id, jkk_pass):
                return True
            driver.switch_to.parent_frame() # 一つ上の階層に戻る
            
    except Exception:
        pass
    return False

def login_and_check(driver):
    print(f"🏁 玄関ページへアクセス: {START_URL}")
    driver.get(START_URL)
    time.sleep(5)

    print("🖱️ ログインページへ移動中...")
    # セッション維持のため直接ジャンプ
    driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin")
    time.sleep(10)

    # 1. 全フレームをしらみつぶしに探して入力
    print("⌨️ 全フレームを再帰的に探索してID/PASSを入力中...")
    if find_and_fill_recursive(driver, JKK_ID, JKK_PASS):
        print("✅ ログイン情報の送信に成功しました！")
    else:
        print("❌ どのフレームにも入力欄が見つかりませんでした。")
        driver.save_screenshot("all_frames_failed.png")
        return False

    # 2. ログイン結果の確認
    print("⏳ 処理待ち...")
    time.sleep(15)
    
    # 全フレームのテキストを結合して「成功」の文字を探す
    def check_text_recursive(driver):
        txt = driver.find_element(By.TAG_NAME, "body").text
        if any(k in txt for k in ["ログアウト", "空室", "メニュー", "マイページ"]):
            return True
        frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
        for i in range(len(frames)):
            driver.switch_to.frame(i)
            if check_text_recursive(driver): return True
            driver.switch_to.parent_frame()
        return False

    if check_text_recursive(driver):
        print("🚨 ログイン突破成功！！！")
        driver.save_screenshot("login_success.png")
        return True
    
    print("❌ ログイン後の画面を確認できませんでした。")
    driver.save_screenshot("after_submit_failed.png")
    return False

def main():
    driver = setup_driver()
    try:
        if login_and_check(driver):
            print("🚀 次のステップ：エリア選択とスキャンの実装へ進めます")
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
