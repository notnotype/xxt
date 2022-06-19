import random
import os
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

login_url = 'http://i.chaoxing.com/'


def login() -> str:
    options = webdriver.ChromeOptions()
    options.add_argument('--mute-audio')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    driver_path = os.path.join(os.path.split(os.path.realpath(__file__))[0], 'chromedriver.exe')
    driver = webdriver.Chrome(driver_path, options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined
        })
      """
    })

    driver.maximize_window()
    driver.get(login_url)

    slide = driver.find_element_by_id('nc_1_n1z')

    action = ActionChains(driver)
    action.click_and_hold(slide).perform()
    action.move_by_offset(200 + random.randint(-50, 50), random.randint(-20, 20)).perform()
    sleep(random.randint(10, 50) * 0.001)

    try:
        action.move_by_offset(20, random.randint(-30, 30)).perform()
        action.release()
    except StaleElementReferenceException:
        pass

    wait = WebDriverWait(driver, 10)
    wait.until(EC.url_contains('&u_atype'))
    url: str = driver.current_url
    driver.quit()

    token = url[url.find('&u_atype'):]
    return token


if __name__ == '__main__':
    print(auth())
