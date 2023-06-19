import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# ISBNの出版者検索ページ
URL_TARGET = "https://isbn.jpo.or.jp/index.php/fix__ref_pub/"


# 本当にないらしいときの例外
class MyNotFound(Exception):
    pass


def get_one_publisher(pub_code):
    print(f"pub_code: {pub_code}")
    ret_ary = []

    # Chrome のオプションを設定する
    options = webdriver.ChromeOptions()
    #options.add_argument('--headless')
    options.add_experimental_option('prefs', {
        'safebrowsing.enabled': True,
    })

    driver = None
    found_publisher = None
    try:
        # Seleniumに接続
        driver = webdriver.Remote(
            command_executor = os.environ['SELENIUM_URL'],
            desired_capabilities=options.to_capabilities(),
            options=options,
        )

        driver.get(URL_TARGET)
        
        # 出版者記号
        driver.find_element(
            By.XPATH,
            "/html/body/section[2]/div/div/div/div/form[1]/p/input[4]"
        ).send_keys(pub_code)
        # 検索ボタン
        driver.find_element(
            By.XPATH,
            "/html/body/section[2]/div/div/div/div/form[1]/p/input[5]"
        ).click()
        try:
            WebDriverWait(
                driver, 20
            ).until(
                EC.presence_of_element_located(
                    (By.ID, "tblp1")
                )
            )
        except TimeoutException:
            # tblp1が現れないときは、本当にない
            raise MyNotFound

        # 結果テーブルから"pub_code"を探す
        found = False
        page_no = 0
        while not found:
            page_no += 1

            td = None
            try:
                td = driver.find_element(
                    By.CSS_SELECTOR,
                    f'#tblp1 tr.sheet[id="{pub_code}"] td:first-child'
                )
            except NoSuchElementException:
                # カンマ区切りで２つ以上設定してるとき、idに設定されていないことがある
                print("NoSuchElementException !!")
                pass
                
            # まだ見つかっていない場合、trを１つずつ見ていく
            if td is None:
                trs = driver.find_elements(
                    By.CSS_SELECTOR,
                    "#tblp1 tr.sheet"
                )
                for tr in trs:
                    # publisher_name
                    td_name = tr.find_element(
                        By.CSS_SELECTOR,
                        "td:nth-child(1)"   # 1から始まる
                    )
                    publisher_name = td_name.text

                    # publisher_code
                    td_code = tr.find_element(
                        By.CSS_SELECTOR,
                        "td:nth-child(2)"   # 1から始まる
                    )
                    codes = td_code.text
                    codes_ary = codes.split(",")
                    for c in codes_ary:
                        c_chomped = c.replace(" ","")

                        if (c_chomped == pub_code):
                            # 見つけた！
                            found = True
                            found_publisher = publisher_name
                        else:
                            # 違ってても、せっかく検索したので戻り値に返してDBに入れる
                            ret_ary.append((c_chomped, publisher_name))

                if found:
                    continue    # while

            if td:
                found = True
                found_publisher = td.text
                continue
            
            # 見つからなかったので、次へボタンを押す

            # 次へボタンを探す
            try:
                next_button = driver.find_element(
                    By.XPATH,
                    '//*[@id="pubListform"]/table[1]/tbody/tr/td/input[2]'
                )
            except NoSuchElementException:
                # Nextが見つからない場合は本当にない
                # 何度も"ない"ということを探してしまうので、Nullで登録しておく
                print("NoSuchElementException !!(2)")
                found = True    # Trueじゃないけど抜けるために入れる
                found_publisher = None
                continue
                
            if (next_button.get_attribute("class") == "next_disabled"):
                # 使用不可になっていたら次はない
                # 番号から出版社名がヒットするが、記号にはない、というケースがある
                found = True    # Trueじゃないけど抜けるために入れる
                found_publisher = None
                continue
            
            # 押して、次のページになるまで待つ
            next_button.click()
            WebDriverWait(
                driver, 30
            ).until(
                EC.text_to_be_present_in_element(
                    (
                        By.XPATH,
                        '//*[@id="pubListform"]/table[1]/tbody/tr/td'
                    ),
                    f"{page_no + 1}／"
                )
            )

            # 無限ループ回避（念のため）
            if page_no > 10:
                found = True
                found_publisher = "ERROR: Loop 10 count"
            
            print(f"ループ page:{page_no}")

    except MyNotFound:
        pass

    finally:
        # ブラウザを終了
        if (driver):
            driver.quit()

    print(f"pub_code: {pub_code} -> {found_publisher}")
    ret_ary.append((pub_code, found_publisher))
    return ret_ary

