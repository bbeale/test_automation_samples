#!/usr/bin/env python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, WebDriverException
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
        ttime                   = str(time.strftime("%Y%m%d_%H%M%S", time.localtime()))
        self.name               = "{}_{}".format("Autotest Site", ttime)
        self.abbrev             = "{}{}".format("A", ttime)
        self.status             = "Active"
        self.billed             = True
        self.notes	            = "Test notes from {}".format(ttime)


class Paths:
    """ DOM element paths """
    def __init__(self):

        self.sites_billing      = (By.LINK_TEXT, "Sites/Billing")
        self.new_site           = (By.XPATH, "//a[contains(., \"Add New Site\")]")
        self.site_name          = (By.NAME, "site_name")
        self.site_abbrev        = (By.NAME, "site_abbrev")
        self.site_billed        = (By.XPATH, "//div[input[@name = \"site_billed\"]]")
        self.submit             = (By.CSS_SELECTOR, "input[value=\"Submit\"]")
        self.site_added         = (By.XPATH, "//span[contains(., \"Site added\")]")


class Locators:
    """ Field locators """
    def __init__(self):

        p = Paths()

        self.sites_billing      = EC.visibility_of_element_located(p.sites_billing)
        self.new_site           = EC.visibility_of_element_located(p.new_site)
        self.site_name          = EC.visibility_of_element_located(p.site_name)
        self.site_abbrev        = EC.visibility_of_element_located(p.site_abbrev)
        self.site_billed        = EC.visibility_of_element_located(p.site_billed)
        self.submit             = EC.element_to_be_clickable(p.submit)
        self.site_added         = EC.visibility_of_element_located(p.site_added)


class TestCreateSite(B):

    def __init__(self):

        self.driver             = None
        self.wait               = None
        self.connection         = None
        self.site_id            = None

    def setup_class(self):

        print("\nSetting up...")
        self.set_username(B.username, B.password)
        self.driver             = webdriver.Firefox()
        self.wait               = WebDriverWait(self.driver, 10)

        self.connection         = pymysql.connect(host=B.host, user=B.user, password=B.passwd, db=B.db, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)

    def test_create_site(self):

        wait                    = self.wait
        firefox                 = self.driver
        self.login(firefox)
        locators                = Locators()
        data                    = Data()

        try:
            wait.until(locators.sites_billing).click()
        except NoSuchElementException:
            m = "DOM is not interactable"
            firefox.save_screenshot(B.screenshot_dir + m + ".png")
            logging.warning(m), warnings.warn(m)
            firefox.get(B.base_url + "<<redacted>>")

        wait.until(locators.new_site).click()
        wait.until(locators.site_name).clear()
        wait.until(locators.site_abbrev).clear()
        wait.until(locators.site_name).send_keys(data.name)
        wait.until(locators.site_abbrev).send_keys(data.abbrev)
        if data.billed:
            wait.until(locators.site_billed).click()

        try:
            wait.until(locators.submit).click()
            wait.until(EC.visibility_of_element_located((By.LINK_TEXT, data.name)))

        except WebDriverException:
            message = "Unable to create a new site"
            firefox.save_screenshot(B.screenshot_dir + message + ".png")
            firefox.quit()
            logging.error(message)
            pytest.fail(message)

        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT `siteID` FROM `sites` WHERE `name`={} ORDER BY `siteID` DESC".format(data.name)
                cursor.execute(sql)
                result = cursor.fetchone()
                logging.info("Created new site with ID {}: ".format(result))
                self.site_id = result

        except DatabaseError as de:
            message = "database record for new site not found"
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
                logging.warning(message)
                warnings.warn(message)
                pytest.xfail(message)

        try:
            with self.connection.cursor() as cursor:
                sql = "DELETE FROM `sites` WHERE `siteID`={}".format(int(self.site_id))
                cursor.execute(sql)
                logging.info("Deleted site record for {}: ".format(self.site_id))

        finally:
            self.connection.close()
