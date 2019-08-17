#!/usr/bin/env python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, WebDriverException, NoAlertPresentException, TimeoutException
import os
import sys
import time
import logging
import platform


class Paths:

    def __init__(self):

        self.username        = (By.XPATH,       "//input[@id = \"username\"]")
        self.password        = (By.XPATH,       "//input[@id = \"password\"]")
        self.login           = (By.CSS_SELECTOR,"input[name=\"login\"]")
        self.user_serach     = (By.NAME,        "searchterms")
        self.setting_search  = (By.NAME,        "search")
        self.search          = (By.XPATH,       "//*[@id=\"content\"]/div[1]/div[3]/form[contains(., "
                                                "\"User Search\")]/div/input")
        self.login_user      = (By.XPATH,       "//*[@id=\"content\"]/table/tbody/tr[2]/td[contains(., \"Login\")]/a["
                                                "1]")
        self.logout          = (By.LINK_TEXT,   "Log Off")
        self.welcome         = (By.XPATH,       "//*[contains(., \"Welcome,\")]")


class Locators:

    def __init__(self):

        self.db = "customDb"
        p = Paths()

        self.username        = EC.visibility_of_element_located(p.username)
        self.password        = EC.visibility_of_element_located(p.password)
        self.login           = EC.visibility_of_element_located(p.login)
        self.user_serach     = EC.visibility_of_element_located(p.user_serach)
        self.setting_search  = EC.visibility_of_element_located(p.setting_search)
        self.search          = EC.visibility_of_element_located(p.search)
        self.login_user      = EC.visibility_of_element_located(p.login_user)
        self.logout          = EC.element_to_be_clickable(p.logout)
        self.welcome         = EC.visibility_of_element_located(p.welcome)


class Base:
    """ Global setup, teardown and helper methods along with base url,
    test data and test result directories """

    sys_name        = platform.platform()

    test_data       = os.environ["test_data"]
    ss_path_str     = "test_results/screenshots/{}"
    date_suffix     = str(time.strftime("%Y_%m_%d"))
    screenshot_dir  = os.path.relpath(os.path.join(ss_path_str.format(date_suffix)))
    results         = "results.log"

    # db connection
    host            = os.environ["host"]
    db_user         = os.environ["db_user"]
    user            = os.environ["user"]
    passwd          = os.environ["passwd"]

    # Environments
    base_url = "https://<<redacted>>.com/"

    if not os.path.exists(screenshot_dir):
        os.path.join(os.path.dirname(__file__), screenshot_dir)

    logging.basicConfig(filename='results.log', level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(lineno)d')

    # Login info
    username = os.environ["username"]
    password = os.environ["password"]

    @classmethod
    def access_boxes_checked(cls, box):
        unchecked = 0
        for b in box:
            try:
                WebDriverWait(webdriver, 10).until(EC.visibility_of_element_located((By.XPATH, b)))
            except WebDriverException:
                unchecked += 1
        print("Unchecked boxes: ", unchecked)
        return unchecked > 0

    @classmethod
    def set_username(cls, un, pw):
        cls.username = un
        cls.password = pw

    @classmethod
    def login(cls, driver):
        me = "\nStarting {} as {}".format(cls.__name__, cls.username)
        logging.info(me)
        driver.get(cls.base_url)
        timeout = 10
        wait = WebDriverWait(driver, timeout)
        locators = Locators()

        """ Login """
        wait.until(locators.username).clear()
        wait.until(locators.password).clear()
        wait.until(locators.username).send_keys(cls.username)
        wait.until(locators.password).send_keys(cls.password)
        wait.until(locators.login).click()

        try:
            wait.until(locators.welcome)

        except NoSuchElementException:
            message = "{} - Login as {} failed".format(str(time.strftime("%H%M%S")), cls.username)
            driver.save_screenshot(cls.screenshot_dir + message + ".png")
            driver.quit()
            logging.exception(message)
            sys.exit(-1)

    @staticmethod
    def logout(webd):
        timeout = 10
        wait = WebDriverWait(webd, timeout)
        locators = Locators()
        try:
            wait.until(locators.logout).click()
        except NoSuchElementException:
            message = "{} - Logging out as {} failed".format(str(time.strftime("%H%M%S")), Base.username)
            webd.save_screenshot(Base.screenshot_dir + message + ".png")
        finally:
            print("Logging out at ", Base.base_url + "login_logoff")
            webd.get(Base.base_url + "login_logoff")
            webd.quit()
