#!/usr/bin/env python
# coding: utf-8
from selenium import webdriver
from time import sleep
import os
import re
import onnxruntime
from PIL import Image,ImageEnhance
import numpy as np
import requests
session=requests.Session()
class Apply():
    def __init__(self, NetID, pwd):
        self.NetID = NetID
        print(NetID)
        self.pwd = pwd
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless") #设置火狐为headless无界面模式
        options.add_argument("--disable-gpu")
        #options.binary_location = "./Mozilla Firefox/firefox.exe"
        self.driver = webdriver.Firefox(executable_path=f"{os.environ['GITHUB_ACTION_PATH']}/geckodriver.exe",options=options)
        try:
            self.main()
        except:
            self.__del__()
            pass

    def __del__(self):
        self.driver.quit()

    def convert2array(self,imgdata,width, height):
        imgarray=[0 for a in range(3)]
        for channel in range(3):
            imgarray[channel] = [0 for a in range(width) ]
            for i in range(width):
                imgarray[channel][i]=[0 for a in range(height)]
                for j in range(height):
                    index=(i + j * width) * 4
                    imgarray[channel][i][j]=imgdata[index+channel]
        return imgarray


    def getCaptcha(self, filePath = 'captcha.jpg'):
        # 识别
        key_map={48: '0', 49: '1', 50: '2', 51: '3', 52: '4', 53: '5', 54: '6', 55: '7', 56: '8', 57: '9',
         97: 'a', 98: 'b', 99: 'c', 100: 'd', 101: 'e', 102: 'f', 103: 'g', 104: 'h', 105: 'i', 106: 'j', 107: 'k', 108: 'l', 109: 'm', 110: 'n', 111: 'o', 112: 'p', 113: 'q', 114: 'r', 115: 's', 116: 't', 117: 'u', 118: 'v', 119: 'w', 120: 'x', 121: 'y', 122: 'z'}
        img_file=Image.open(f"{os.environ['GITHUB_ACTION_PATH']}/%s" %filePath)
        img_file=img_file.convert("RGBA")
        inputs=np.array(img_file)
        inputs=inputs.ravel()
        inputs=self.convert2array(inputs,90,32)
        inputs=np.array(inputs)
        session=onnxruntime.InferenceSession(f"{os.environ['GITHUB_ACTION_PATH']}/cnn.onnx")
        input_name = session.get_inputs()
        pred=session.run([],{input_name[0].name:inputs.astype(np.float32).reshape(1,3,90,32)})
        pred=pred[0].flatten()
        strs=""
        for t in range(4):
            a=pred[t*36:(t+1)*36]
            ans=np.argmax(a)
            if ans>=0 and ans <26:
                strs +=key_map[ans+97]
            else:
                strs +=key_map[ans+22]
        strs=''.join(re.findall(r'[a-zA-Z0-9]',strs))
        return strs[0:4]

    def login(self, captcha):
        self.driver.find_element_by_id('username').send_keys(self.NetID)
        #print(self.NetID)
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
        self.waituntil('id', 'username')
        while True:
            headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"}
            cookies=self.driver.get_cookies()
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'])
            captcha_url = 'https://cas.sysu.edu.cn/cas/captcha.jsp'
            response = session.get(captcha_url, headers=headers)
            with open(f"{os.environ['GITHUB_ACTION_PATH']}/captcha.jpg", "wb") as f:
                f.write(response.content)
            captcha = self.getCaptcha()
            print('captcha is %s' % captcha)
            self.login(captcha) # 尝试登陆
            if not self.waituntil('xpath', "//*[text()='验证码不正确 ']"):
                break

        #self.driver.maximize_window()

        self.waituntil('xpath', '//nobr[text()="下一步"]')
        self.driver.find_element_by_xpath("//nobr[text()='下一步']").click() # 进入表单
        sleep(4)
        self.waituntil('xpath', '//*[@id="form_command_bar"]/li[1]')
        self.driver.find_element_by_xpath('//*[@id="form_command_bar"]/li[1]').click() # 提交
        self.waituntil('xpath', '//*[@class="dialog_footer"]/button')
        sleep(4)
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
