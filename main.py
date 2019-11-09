from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from openpyxl import Workbook
import requests
import codecs
import time
import datetime
import sys
import os
import asyncio
import json
import mysql.connector
import numpy as np
import glob
import pyautogui
import base64

base_url = "https://e.fbr.gov.pk/esbn/Service.aspx?PID=Ku9Bf5IjoLpY++SZytsSMw=="
screenshot_file = "capture.png"

def get_captcha_text():
    global screenshot_file
	captcha_api = "12345678901234567890123456789012"
    action_url = "https://2captcha.com/in.php"
    req_url = "https://2captcha.com/res.php?key={}&action=get&id={}"
    encoded_string = ""
    captcha_result = ""

    with open(screenshot_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())

    data = {'key': captcha_api,
            'method': 'base64',
            'body': encoded_string}

    res = ""
    while True:
        try:
            r = requests.post(url=action_url, data=data)
            res = r.text
            print(res)
            break
        except requests.exceptions.ConnectionError:
            time.sleep(3)

    try:
        res_arr = res.split("|")

        if len(res_arr) > 1:
            sleep_time = 6
            while True:
                ret = ""
                time.sleep(sleep_time)
                while True:
                    try:
                        r = requests.get(req_url.format(captcha_api, res_arr[1]))
                        ret = r.text
                        print(ret)
                        break
                    except requests.exceptions.ConnectionError:
                        time.sleep(3)

                if ret == "CAPCHA_NOT_READY":
                    sleep_time = 2
                    continue

                ret_arr = ret.split("|")
                if len(ret_arr) > 1:
                    captcha_result = ret_arr[1]
                break
    except:
        return ""

    print(captcha_result)
    return captcha_result

mydb = mysql.connector.connect(
  host="localhost",
  user="xxx",
  passwd="xxx",
  database="fbrgov"
)
mycursor = mydb.cursor()

mycursor.execute("select id, ntn from datalist order by id desc")
myresult = mycursor.fetchall()

options = Options()
options.add_argument('--log-level=3')
options.add_argument("--disable-extensions")
options.add_argument("--incognito")
driver = webdriver.Chrome('chromedriver2', options=options)

while True:
    try:
        driver.get(base_url)
        driver.implicitly_wait(3)
        break
    except requests.exceptions.ConnectionError:
        time.sleep(5)

driver.set_window_size(1336, 572)
driver.set_window_position(-551, 572)
time.sleep(1)

driver.execute_script("window.scrollTo(0, document.body.scrollWidth);")

driver.find_element_by_xpath("//select[@id='ctl00_ContentPlaceHolder1_DDLS0004001']/option[text()='CNIC']").click()
time.sleep(1)

for node in myresult:
    r = ""
    _id = node[0]
    _ntn = node[1]
    _reference_no = ""
    _strn = ""
    _name2 = ""
    _category = ""
    _pp_reg_inc_no = ""
    _email = ""
    _cellphone = ""
    _address = ""
    _registered_on = ""
    _tax_office = ""
    _registration_status = ""
    _branch_arr = []

    print("--", _id, _ntn)
    if _ntn.find("-") > 0:
        driver.find_element_by_xpath("//select[@id='ctl00_ContentPlaceHolder1_DDLS0004001']/option[text()='NTN']").click()
    else:
        driver.find_element_by_xpath("//select[@id='ctl00_ContentPlaceHolder1_DDLS0004001']/option[text()='CNIC']").click()

    driver.find_element_by_id('ctl00_ContentPlaceHolder1_TXTS1003002').clear()
    time.sleep(1)

    driver.find_element_by_xpath("//input[@id='ctl00_ContentPlaceHolder1_TXTS1003002']").send_keys(_ntn)
    time.sleep(1)

    kk = 0
    captcha_error = False
    while True:
        pyautogui.screenshot(screenshot_file, region=(33, 945, 247, 51))
        time.sleep(1)

        captcha_result = get_captcha_text()
        if captcha_result == "":
            kk = kk + 1
            if kk > 3:
                captcha_error = True
                break
            driver.find_element_by_xpath("//input[@id='ctl00_ContentPlaceHolder1_imgReload']").click()
            time.sleep(1)
            continue
        else:
            captcha_result = captcha_result.upper().replace(" ", "", 10)
            driver.find_element_by_id('ctl00_ContentPlaceHolder1_txtCapcha').clear()
            time.sleep(1)
            driver.find_element_by_xpath("//input[@id='ctl00_ContentPlaceHolder1_txtCapcha']").send_keys(captcha_result)
            time.sleep(1)
            break

    if captcha_error == True:
        print("Captcha is error.")
        driver.get(base_url)
        driver.implicitly_wait(3)
        time.sleep(1)

        driver.execute_script("window.scrollTo(0, document.body.scrollWidth);")
        driver.find_element_by_xpath("//select[@id='ctl00_ContentPlaceHolder1_DDLS0004001']/option[text()='CNIC']").click()
        time.sleep(1)
        continue

    driver.find_element_by_xpath("//input[@id='ctl00_ContentPlaceHolder1_btnVerify']").click()
    time.sleep(1)

    s = BeautifulSoup(driver.page_source, 'html.parser')

    status_arr = s.select("span#ctl00_ContentPlaceHolder1_lblStatus")
    status_msg = status_arr[0].text
    if status_msg.find("Invalid Captcha value.") >= 0:
        sql = "UPDATE datalist SET flag=1 WHERE id=\"{}\""
        sql = sql.format(_id)
        print(sql)
        mycursor.execute(sql)
        mydb.commit()
        continue

    table_arr = s.select('span#ctl00_ContentPlaceHolder1_lblResults > table')
    mm = 0
    for table_node in table_arr:
        mm = mm + 1
        if mm == 1:
            tr_arr = table_node.select('tbody > tr')
            for tr_node in tr_arr:
                th_arr = tr_node.select('th')
                td_arr = tr_node.select('td')
                th_tag = th_arr[0].text
                td_tag = td_arr[0].text
                if th_tag == "Reference No":
                    _reference_no = td_tag
                elif th_tag == "STRN":
                    _strn = td_tag
                elif th_tag == "Name":
                    _name2 = td_tag
                elif th_tag == "Category":
                    _category = td_tag
                elif th_tag == "PP/REG/INC No.":
                    _pp_reg_inc_no = td_tag
                elif th_tag == "Email":
                    _email = td_tag
                elif th_tag == "Cell":
                    _cellphone = td_tag
                elif th_tag == "Address":
                    _address = td_tag
                    _address = _address.replace("\"", "'", 10)
                elif th_tag == "Registered On":
                    _registered_on = td_tag
                elif th_tag == "Tax Office":
                    _tax_office = td_tag
                elif th_tag == "Registration Status":
                    _registration_status = td_tag
        elif mm == 2:
            tr_arr = table_node.select('tbody > tr')
            cc = 0
            for tr_node in tr_arr:
                if cc == 0:
                    cc = cc + 1
                    continue
                td_arr = tr_node.select('td')
                _branch_name = td_arr[1].text
                _branch_address = td_arr[2].text
                _branch_activity = td_arr[3].text
                branch_data = {'name': _branch_name,
                               'address': _branch_address,
                               'activity': _branch_activity}
                _branch_arr.append(branch_data)

    print(_reference_no, _strn, _name2, _category, _pp_reg_inc_no, _email, _cellphone, _address, _registered_on, _tax_office, _registration_status)


    sql = "UPDATE datalist SET reference_no=\"{}\", strn=\"{}\", name2=\"{}\", "
    sql = sql + "category=\"{}\", pp_reg_inc_no=\"{}\", email=\"{}\", cellphone=\"{}\", "
    sql = sql + "address=\"{}\", registered_on=\"{}\", tax_office=\"{}\", registration_status=\"{}\" WHERE id=\"{}\""
    sql = sql.format(_reference_no, _strn, _name2, _category, _pp_reg_inc_no, _email, _cellphone, _address, _registered_on, _tax_office, _registration_status, _id)
    print(sql)
    mycursor.execute(sql)
    mydb.commit()

    for branch_node in _branch_arr:
        sql = "INSERT INTO branchlist(data_id, branch_name, branch_address, principal_activity) "
        sql = sql + "VALUES (%s, %s, %s, %s)"
        val = (_id, branch_node['name'], branch_node['address'], branch_node['activity'])
        mycursor.execute(sql, val)
        mydb.commit()

driver.close()
print("THE END")

exit(0)
