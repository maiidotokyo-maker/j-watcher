def wait_for_login_form_recursive(driver, timeout=30):
    print("⏳ ログインフォーム（全フレーム）を探索中...")
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        # 探索を始める前に必ず「一番外側の階層」にリセット
        driver.switch_to.default_content()
        
        # あなたの提案したロジックをベースに「存在確認」だけ行う
        if find_and_fill_recursive(driver, "", "", dry_run=True):
            print("✅ ログインフォームを検出しました！")
            return True
            
        time.sleep(3) # レトロサーバーを労わりつつ待機
        
    print("❌ ログインフォームが見つかりませんでした（全フレーム探索）。")
    driver.save_screenshot("login_form_not_found.png")
    return False

# --- find_and_fill_recursive の冒頭も少し強化 ---
def find_and_fill_recursive(driver, jkk_id, jkk_pass, dry_run=False):
    try:
        # パスワード欄を「ログイン画面」の絶対的な目印とする
        pws = driver.find_elements(By.XPATH, "//input[@type='password']")
        
        if pws:
            if dry_run:
                return True # 存在確認完了
            
            # 実際の入力処理（一度成功した時のロジック）
            uids = driver.find_elements(By.XPATH, "//input[contains(@name, 'uid') or contains(@id, 'uid') or contains(@name, 'user') or contains(@id, 'Id')]")
            if uids:
                uids[0].clear()
                uids[0].send_keys(jkk_id)
                pws[0].clear()
                pws[0].send_keys(jkk_pass)
                # 送信
                btns = driver.find_elements(By.XPATH, "//img[contains(@src, 'login')] | //input[@type='image'] | //input[@type='submit'] | //button")
                if btns: btns[0].click()
                else: pws[0].send_keys(Keys.RETURN)
                return True
        
        # 子フレーム探索
        frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
        for i in range(len(frames)):
            driver.switch_to.frame(i)
            if find_and_fill_recursive(driver, jkk_id, jkk_pass, dry_run):
                return True # 発見したらそのまま抜ける
            driver.switch_to.parent_frame()
    except:
        pass
    return False
