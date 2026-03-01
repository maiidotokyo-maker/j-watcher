import os
import time
# ... (インポート類は共通) ...

def main():
    driver = create_driver()
    wait = WebDriverWait(driver, 30)

    try:
        # ① まずは公式サイトの「トップ」へ
        log("🚪 手順1: JKK東京トップページへアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        time.sleep(5)
        
        # ② 「住宅をお探しの方」メニューから「JKKねっと」を探してクリック
        log("🔎 手順2: サイト内の『JKKねっと』ボタンを探索・クリック")
        # テキストに依存せず、URLのパターンでボタンを特定
        jkk_btn_xpath = "//a[contains(@href, 'jhomes.to-kousya.or.jp')]"
        jkk_btn = wait.until(EC.element_to_be_clickable((By.XPATH, jkk_btn_xpath)))
        jkk_btn.click()
        
        # 新しいタブが開く場合を考慮し、最新のウィンドウに切り替え
        time.sleep(5)
        driver.switch_to.window(driver.window_handles[-1])
        
        # ③ 遷移後のページで「ログイン」ボタンをURLから特定してクリック
        log("🔗 手順3: ログイン画面へのリンクをクリック")
        # /mypageMenu へのリンクを直接クリックすることでリファラを維持
        login_link_xpath = "//a[contains(@href, 'mypageMenu')]"
        login_link = wait.until(EC.element_to_be_clickable((By.XPATH, login_link_xpath)))
        login_link.click()
        
        time.sleep(8)
        driver.save_screenshot("after_click_transition.png")

        # ④ ログインフォーム入力（iframe対応）
        log("⌨️ 手順4: フォーム入力開始")
        # iframeを全てチェック
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        if frames:
            driver.switch_to.frame(frames[0])
            log("📦 iframeに切り替えました")

        u_field = wait.until(EC.presence_of_element_located((By.NAME, "uid")))
        p_field = driver.find_element(By.NAME, "passwd")

        driver.execute_script("arguments[0].value = arguments[1];", u_field, JKK_ID)
        driver.execute_script("arguments[0].value = arguments[1];", p_field, JKK_PASSWORD)
        
        p_field.submit()
        
        # ⑤ 成功判定
        wait.until(EC.any_of(EC.url_contains("mypage"), EC.title_contains("マイページ")))
        log("🎉 ログイン成功！")

    except Exception as e:
        log(f"❌ 失敗: {e}")
        driver.save_screenshot("final_attempt_error.png")
