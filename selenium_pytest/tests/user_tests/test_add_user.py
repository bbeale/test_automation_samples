#!/usr/bin/env python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
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

        self.first_name         = "Test"
        self.last_name          = "User_{}".format(str(time.strftime("%Y%m%d_%H%M%S", time.localtime())))
        self.username           = "testuser{}".format(str(time.strftime("%H%M%S", time.localtime())))
        self.email              = self.username + "@<<redacted>>.com"
        self.startdate          = str(time.strftime("%Y-%m-%d", time.localtime()))
        self.enddate            = str(time.strftime("%Y-12-31", time.localtime()))
        self.level              = "2"


class Paths:
    """ DOM element paths """
    def __init__(self):

        self.home               = (By.XPATH,        "//a[contains(., \"Home\")]")
        self.select_all         = (By.XPATH,        "//div[contains(@class, \"unchecked\") and input[@name = \"select_all\"]]")
        self.submit_button      = (By.NAME,         "submitbutton")
        self.users              = (By.LINK_TEXT,    "Users")
        self.add_new            = (By.XPATH,        "//*[text() = \"Add New User\"]")
        self.f_name             = (By.NAME,         "firstname")
        self.l_name             = (By.NAME,         "lastname")
        self.user_name          = (By.NAME,         "username")
        self.email              = (By.NAME,         "email")
        self.start_date         = (By.NAME,         "start_date")
        self.end_date           = (By.NAME,         "end_date")
        self.level              = (By.NAME,         "level")
        self.add_new_user       = (By.CSS_SELECTOR, "input[value = \"Add New User\"]")
        self.saved              = (By.XPATH,        "//span[contains(., \"User information saved\")]")


class Locators:
    """ Field locators """
    def __init__(self):

        p = Paths()

        self.home               = EC.visibility_of_element_located(p.home)
        self.select_all         = EC.visibility_of_element_located(p.select_all)
        self.submit_button      = EC.visibility_of_element_located(p.submit_button)
        self.users              = EC.visibility_of_element_located(p.users)
        self.add_new            = EC.visibility_of_element_located(p.add_new)
        self.f_name             = EC.visibility_of_element_located(p.f_name)
        self.l_name             = EC.visibility_of_element_located(p.l_name)
        self.user_name          = EC.visibility_of_element_located(p.user_name)
        self.email              = EC.visibility_of_element_located(p.email)
        self.start_date         = EC.visibility_of_element_located(p.start_date)
        self.end_date           = EC.visibility_of_element_located(p.end_date)
        self.level              = EC.visibility_of_element_located(p.level)
        self.add_new_user       = EC.visibility_of_element_located(p.add_new_user)
        self.saved              = EC.visibility_of_element_located(p.saved)


class TestAddNewUser(B):

    def __init__(self):
        self.driver             = None
        self.wait               = None
        self.connection         = None
        self.user_id            = None

    def setup_class(self):
        print("\nSetting up...")
        self.set_username(B.username, B.password)
        self.driver             = webdriver.Firefox()
        self.wait               = WebDriverWait(self.driver, 10)
        self.user_id            = 0
        
        # Connect to the database
        self.connection = pymysql.connect(host=self.host, user=self.user, password=self.passwd, db=self.db, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)

    def test_add_user(self):

        wait                    = self.wait
        firefox                 = self.driver
        self.login(firefox)
        locators                = Locators()
        data                    = Data()

        try:
            wait.until(locators.users).send_keys(Keys.ENTER)
        except NoSuchElementException:
            m = "DOM is not interactable"
            firefox.save_screenshot(B.screenshot_dir + "user_fail.png")
            logging.warning(m), warnings.warn(m)
            firefox.get(B.base_url + "<<redacted>>")

        wait.until(locators.f_name).clear()
        wait.until(locators.l_name).clear()
        wait.until(locators.user_name).clear()
        wait.until(locators.email).clear()
        wait.until(locators.start_date).clear()
        wait.until(locators.end_date).clear()
        wait.until(locators.f_name).send_keys(data.first_name)
        wait.until(locators.l_name).send_keys(data.last_name)
        wait.until(locators.user_name).send_keys(data.username)
        wait.until(locators.email).send_keys(data.email)
        wait.until(locators.start_date).send_keys(data.startdate)
        wait.until(locators.end_date).send_keys(data.enddate)
        Select(wait.until(locators.level)).select_by_index(data.level)
        wait.until(locators.add_new_user).click()

        # Confirm we're on the right page/tab by looking at the h1 elements
        hs = firefox.find_elements_by_tag_name("h1")

        if not hs[1].text == "New User Created":
            message = "Failed to add new user"
            firefox.save_screenshot(B.screenshot_dir + message + ".png")
            firefox.quit()
            logging.exception(message)
            pytest.fail(message)
            
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT `userID` FROM `users` WHERE `lastname`={} AND `firstname`={} AND `email`={} ORDER BY `userID` DESC".format(data.last_name, data.first_name, data.email)
                cursor.execute(sql)
                result = cursor.fetchone()
                logging.info("Created user with user ID {}: ".format(result))
                self.user_id = result
                
        except DatabaseError as de:
            message = "database record for new user not found"
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
                logging.exception(message)
                warnings.warn(message)
                pytest.xfail(message)

        try:
            with self.connection.cursor() as cursor:
                sql = "DELETE FROM `users` WHERE `userID` = {}".format(int(self.user_id))
                cursor.execute(sql)

        finally:
            self.connection.close()
