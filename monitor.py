def find_and_fill_recursive(driver, jkk_id, jkk_pass, dry_run=False):
    try:
        pws = driver.find_elements(By.XPATH, "//input[@type='password']")
        if pws:
            if dry_run:
                inputs = driver.find_elements(By.TAG_NAME, "input")
                print(f"🔍 検出された input 要素一覧（{len(inputs)} 件）:", flush=True)
                for i, el in enumerate(inputs):
                    try:
                        print(f"  [{i}] type={el.get_attribute('type')} id='{el.get_attribute('id')}' name='{el.get_attribute('name')}'", flush=True)
                    except:
                        pass
                return True
            uids = driver.find_elements(By.XPATH, "//input[contains(@name, 'uid') or contains(@id, 'uid') or contains(@name, 'user') or contains(@id, 'Id')]")
            if uids:
                uids[0].clear()
                uids[0].send_keys(jkk_id)
                pws[0].clear()
                pws[0].send_keys(jkk_pass)
                btns = driver.find_elements(By.XPATH, "//img[contains(@src, 'login')] | //input[@type='image'] | //input[@type='submit'] | //button")
                if btns:
                    btns[0].click()
                else:
                    pws[0].send_keys(Keys.RETURN)
                return True
        frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
        for i in range(len(frames)):
            driver.switch_to.frame(i)
            if find_and_fill_recursive(driver, jkk_id, jkk_pass, dry_run):
                return True
            driver.switch_to.parent_frame()
    except Exception as e:
        print(f"⚠️ フォーム探索中の例外: {e}", flush=True)
    return False
