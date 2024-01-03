#!/usr/bin/env python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
import time
import pytest
import logging
import warnings
import pymysql.cursors
from pymysql.err import DatabaseError

from ..base import Base as B


class Data:
    """ Test data """
    def __init__(self):

        self.firstname      = "Test"
        self.lastname       = "Admin_{}".format(str(time.strftime("%Y%m%d_%H%M%S", time.localtime())))
        self.username       = "test" + self.lastname.lower()
        self.email          = self.username + "@<<redacted>>.com"


class Paths:
    """ DOM element paths """
    def __init__(self):

        self.p_admin        = (By.XPATH,        "//a[text() = \"Program Administrators\"]")
        self.add_admin      = (By.XPATH,        "//a[contains(., \" Add Administrator\")]")
        self.f_name         = (By.XPATH,        "//input[@name = \"firstname\"]")
        self.l_name         = (By.XPATH,        "//input[@name = \"lastname\"]")
        self.user_name      = (By.XPATH,        "//input[@name = \"username\"]")
        self.email          = (By.XPATH,        "//input[@name = \"email\"]")
        self.checkbox_1     = (By.XPATH,        "//div[@name = \"checkbox_1\"]")
        self.checkbox_2     = (By.XPATH,        "//div[@name = \"checkbox_2\"]")
        self.checkbox_3     = (By.XPATH,        "//div[@name = \"checkbox_3\"]")
        self.submit         = (By.CSS_SELECTOR, "input[value=\"Submit\"]")
        self.admin_added    = (By.XPATH,        "//span[contains(., \"Administrator added\")]")


class Locators:
    """ Field locators """
    def __init__(self):

        p = Paths()

        self.p_admin        = EC.visibility_of_element_located(p.p_admin)
        self.add_admin      = EC.visibility_of_element_located(p.add_admin)
        self.f_name         = EC.visibility_of_element_located(p.f_name)
        self.l_name         = EC.visibility_of_element_located(p.l_name)
        self.user_name      = EC.visibility_of_element_located(p.user_name)
        self.email          = EC.visibility_of_element_located(p.email)
        self.checkbox_1     = EC.visibility_of_element_located(p.admin_added)
        self.checkbox_2     = EC.visibility_of_element_located(p.admin_added)
        self.checkbox_3     = EC.visibility_of_element_located(p.admin_added)
        self.submit         = EC.element_to_be_clickable(p.submit)
        self.admin_added    = EC.visibility_of_element_located(p.admin_added)


class TestAddProgramAdmin(B):
    """ test case for adding a new admin usertype """

    @staticmethod
    def is_element_present(wd, element_path):
        try:
            wd.find_element_by_xpath(element_path)
        except NoSuchElementException:
            return False
        return True

    def __init__(self):

        self.driver             = None
        self.wait               = None
        self.connection         = None
        self.admin_user_id      = None

    def setup_class(self):

        print("\nSetting up...")
        self.set_username(B.username, B.password)
        self.driver             = webdriver.Firefox()
        self.wait               = WebDriverWait(self.driver, 10)

        # Connect to the database
        self.connection         = pymysql.connect(host=self.host, user=self.user, password=self.passwd, db=self.db, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)

    def test_add_admin(self):

        wait                    = self.wait
        firefox                 = self.driver
        self.login(firefox)
        locators                = Locators()
        data                    = Data()

        # Goto admin create page, add new
        try:
            wait.until(locators.p_admin).click()
        except NoSuchElementException:
            m = "DOM is not interactable"
            firefox.get(B.base_url + "<<redacted>>")
            logging.warning(m)
            warnings.warn(m)
            firefox.save_screenshot(B.screenshot_dir + "admin_fail.png")

        wait.until(locators.add_admin).send_keys(Keys.RETURN)
        wait.until(locators.f_name).clear()
        wait.until(locators.l_name).clear()
        wait.until(locators.user_name).clear()
        wait.until(locators.email).clear()
        wait.until(locators.f_name).send_keys(data.firstname)
        wait.until(locators.l_name).send_keys(data.lastname)
        wait.until(locators.user_name).send_keys(data.username)
        wait.until(locators.email).send_keys(data.email)

        if self.is_element_present(firefox, locators.checkbox_1):
            firefox.find_element_by_xpath(locators.checkbox_1).click()
        if self.is_element_present(firefox, locators.checkbox_2):
            firefox.find_element_by_xpath(locators.checkbox_2).click()
        if self.is_element_present(firefox, locators.checkbox_3):
            firefox.find_element_by_xpath(locators.checkbox_3).click()

        wait.until(locators.submit).click()

        try:
            wait.until(locators.admin_added)

        except NoSuchElementException:
            message = "Unable to create a new admin"
            firefox.save_screenshot(B.screenshot_dir + message + ".png")
            firefox.quit()
            logging.exception(message)
            pytest.fail(message)

        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT `userID` FROM `users` WHERE `lastname`={} AND `firstname`={} AND `email`={} ORDER BY `userID` DESC".format(data.lastname, data.firstname, data.email)
                cursor.execute(sql)
                result = cursor.fetchone()
                logging.info("Created administrator record with user ID {}: ".format(result))
                self.admin_user_id = result

        except DatabaseError as de:
            message = "database record for admin user not found"
            firefox.quit()
            logging.exception(de, message)
            pytest.fail(message)

    def teardown_class(self):
        print("\nCleaning up...")
        if self.driver:
            try:
                self.driver.quit()
            except WebDriverException:
                message = "driver.quit() is not working."
                warnings.warn(message), logging.warning(message)
                pytest.xfail(message)

        try:
            with self.connection.cursor() as cursor:
                sql = "DELETE FROM `users` WHERE `userID`={}".format(int(self.admin_user_id))
                cursor.execute(sql)
                logging.info("Deleted administrator record for user ID {}: ".format(self.admin_user_id))

        finally:
            self.connection.close()
