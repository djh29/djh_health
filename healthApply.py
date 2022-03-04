#!/usr/bin/env python
# coding: utf-8
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from time import sleep
import os
import re
import onnxruntime
from PIL import Image,ImageEnhance
import numpy as np
import requests
from retrying import retry

session=requests.Session()
c_service=Service(f"{os.environ['GITHUB_ACTION_PATH']}/geckodriver.exe")
c_service.command_line_args()
c_service.start()

class Apply():
    def __init__(self, NetID, pwd):
        self.NetID = NetID
        print(NetID)
        self.pwd = pwd
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless") #设置火狐为headless无界面模式
        options.add_argument("--disable-gpu")
        #options.binary_location = "./Mozilla Firefox/firefox.exe"
        self.driver = webdriver.Firefox(options=options)
        try:
            #self.driver.get(r'https://www.baidu.com/')
            #self.driver.close()
            self.main()
        except:
            self.__del__()
            pass

    def __del__(self):
        self.driver.quit()
        c_service.stop()

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
        session1=onnxruntime.InferenceSession(f"{os.environ['GITHUB_ACTION_PATH']}/cnn.onnx")
        input_name = session1.get_inputs()
        pred=session1.run([],{input_name[0].name:inputs.astype(np.float32).reshape(1,3,90,32)})
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
        self.driver.find_element(By.ID,'username').send_keys(self.NetID)
        #print(self.NetID)
        self.driver.find_element(By.ID,'password').send_keys(self.pwd)
        self.driver.find_element(By.ID,'captcha').send_keys(captcha)
        sleep(4)
        self.driver.find_element(By.NAME,'submit').click()

    def waituntil(self, by, value, time = 15):
        while time:
            elements = self.driver.find_elements(by, value)
            if len(elements):
                return True
            else:
                time -= 1
                sleep(1)
        return False
    
    # 失败后随机 3-5s 后重试，最多 6 次
    @retry(wait_random_min=3000, wait_random_max=5000, stop_max_attempt_number=6)
    def main(self):
        # 100% 缩放情况下使用
        self.driver.get(r'http://jksb.sysu.edu.cn/infoplus/form/XNYQSB/start')
        #self.driver.set_window_size(900, 900)
        self.waituntil('id', 'username')
        while True:
            headers = {'Connection': 'Keep-Alive',
        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)'}
            cookies=self.driver.get_cookies()
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'])
            captcha_url = 'https://cas.sysu.edu.cn/cas/captcha.jsp'
            response = session.get(captcha_url, headers=headers)
            sleep(5)
            with open(f"{os.environ['GITHUB_ACTION_PATH']}/captcha.jpg", "wb") as f:
                f.write(response.content)
            sleep(3)
            captcha = self.getCaptcha()
            print(        'captcha is %s' % captcha)
            #判断文件是否存在
            if(os.path.exists(f"{os.environ['GITHUB_ACTION_PATH']}/captcha.jpg")):
                os.remove(f"{os.environ['GITHUB_ACTION_PATH']}/captcha.jpg")
                print("移除目录下文件")
            else:
                print("要删除的文件不存在！")
            self.login(captcha) # 尝试登陆
            if not self.waituntil('xpath', "//*[text()='验证码不正确 ']"):
                break

        #self.driver.maximize_window()

        self.waituntil('xpath', '//nobr[text()="下一步"]')
        self.driver.find_element(By.XPATH,"//nobr[text()='下一步']").click() # 进入表单
        sleep(10)
        self.waituntil('xpath', '//*[@id="form_command_bar"]/li[1]')
        self.driver.find_element(By.XPATH,'//*[@id="form_command_bar"]/li[1]').click() # 提交
        self.waituntil('xpath', '//*[@class="dialog_footer"]/button')
        sleep(10)
        print("        提交。")
        #result = driver.find_element(By.XPATH,'//*[@class="dialog_content"]').text
        self.driver.find_element(By.XPATH,'//*[@class="dialog_footer"]/button').click()
        sleep(10)
        print("        Done.")
        self.driver.quit()
        c_service.stop()
        try:
            # 如果有未打钩的情况下需要再执行多一步
            self.driver.find_element(By.ID,'V1_CTRL82').click()
            self.waituntil('xpath', '//*[@class="dialog_footer"]/button')
            self.driver.find_element(By.XPATH,'//*[@class="dialog_footer"]/button').click()
            self.driver.quit()
            c_service.service.stop()
        except:
            pass

def spilt(id,pw):
    id_list=id.split(",")
    pw_list=pw.split(",")
    list_d=dict(zip(id_list,pw_list))
    #print(list_d)
    return list_d

if __name__ == '__main__':
    netid = os.environ['NETID']
    password = os.environ['PASSWORD']
    d=spilt(netid,password)
    for i in d.keys():
        apply = Apply(i, d[i])
    #with open(f"{os.environ['GITHUB_ACTION_PATH']}/text.txt", 'r') as f:
        #for f in f.readlines():
            #f=f.strip()
            #apply = Apply(f.split(',',1)[0], f.split(',',1)[1])
