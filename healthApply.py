#!/usr/bin/env python
# coding: utf-8
from selenium import webdriver
from time import sleep
import ddddocr
import os
import re
class Apply():
    def __init__(self, NetID, pwd):
        self.NetID = NetID
        self.pwd = pwd
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless") #设置火狐为headless无界面模式
        options.add_argument("--disable-gpu")
        #options.binary_location = "./Mozilla Firefox/firefox.exe"
        self.driver = webdriver.Firefox(executable_path=f"{os.environ['GITHUB_ACTION_PATH']}/geckodriver.exe",options=options)
        try:
            self.main()
        except:
            #self.__del__()
            pass

    def __del__(self):
        self.driver.quit()

    def getCaptcha(self, filePath = 'captcha.png'):
        # 识别
        ocr = ddddocr.DdddOcr()
        with open(f"{os.environ['GITHUB_ACTION_PATH']}/%s" %filePath, 'rb') as f:
            b = f.read()
        text=ocr.classification(b)
        text=''.join(re.findall(r'[a-zA-Z0-9]',text))
        return text[0:4]

    def login(self, captcha):
        self.driver.find_element_by_id('username').send_keys(self.NetID)
        print(self.NetID)
        self.driver.find_element_by_id('password').send_keys(self.pwd)
        self.driver.find_element_by_id('captcha').send_keys(captcha)
        self.driver.find_element_by_name('submit').click()

    def waituntil(self, by, value, time = 5):
        while time:
            elements = self.driver.find_elements(by, value)
            if len(elements):
                return True
            else:
                time -= 1
                sleep(1)
        return False

    def main(self):
        # 100% 缩放情况下使用
        self.driver.get(r'http://jksb.sysu.edu.cn/infoplus/form/XNYQSB/start')
        #self.driver.set_window_size(900, 900)
        sleep(3)
        self.waituntil('id', 'username')
        while True:
            img=self.driver.find_element_by_xpath('//*[@id="captchaImg"]')
            img.screenshot(f"{os.environ['GITHUB_ACTION_PATH']}/captcha.png")
            captcha = self.getCaptcha()
            print('captcha is %s' % captcha)
            self.login(captcha) # 尝试登陆
            if not self.waituntil('xpath', "//*[text()='验证码不正确 ']"):
                break

        #self.driver.maximize_window()

        self.waituntil('xpath', '//nobr[text()="下一步"]')
        self.driver.find_element_by_xpath("//nobr[text()='下一步']").click() # 进入表单
        sleep(3.5)
        self.waituntil('xpath', '//*[@id="form_command_bar"]/li[1]')
        self.driver.find_element_by_xpath('//*[@id="form_command_bar"]/li[1]').click() # 提交
        print("提交成功")
        self.waituntil('xpath', '//*[@class="dialog_footer"]/button')
        self.driver.find_element_by_xpath('//*[@class="dialog_footer"]/button').click()
        self.driver.quit()

        try:
            # 如果有未打钩的情况下需要再执行多一步
            self.driver.find_element_by_id('V1_CTRL82').click()
            self.waituntil('xpath', '//*[@class="dialog_footer"]/button')
            self.driver.find_element_by_xpath('//*[@class="dialog_footer"]/button').click()
            self.driver.quit()
        except:
            pass

if __name__ == '__main__':
    with open(f"{os.environ['GITHUB_ACTION_PATH']}/text.txt", 'r') as f:
        for f in f.readlines():
            apply = Apply(f.split(',',1)[0], f.split(',',1)[1])
