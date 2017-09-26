# -*- coding: utf-8 -*-  

import datetime
import os
import re
import requests
import string
import thread
import time
import urllib2
import base64
import hashlib
import chardet
from BeautifulSoup import BeautifulSoup
from requests.exceptions import MissingSchema

from UserDefineHash import UserDefineHash
from INIFILE import INIFILE
import emojiutil
from pip._vendor.requests import ReadTimeout, ConnectionError


# ----------- 加载处理糗事百科 -----------


class Spider_Model:
    def __init__(self):
        self.page = 1
        self.pages = []
        self.enable = False
        self.canLoad = True #sub thread can run?
	self.allDone = False
        self.store_dir = None
        self.init_work_dir()

        self.isFirst = True #run only once
        self.unload_page_num = 0 #page to be loaded
        # self.save_path = 'F:\\qiushimm\\'


    # init the storage dir = 'tmp /'
    def init_work_dir(self):
        retval = os.getcwd()
        print '#current dir is : ' + retval
        # 图片存放路径
        store_dir = retval + os.sep + 'tmp'
        print '#all imgs are going to be stored in dir :' + store_dir

        if not os.path.exists(store_dir):
            print '#tmp dir does not exist, attemp to mkdir'
            os.mkdir(store_dir)
            print '#mkdir sucessfully'
        else:
            print '#tmp dir is already exist'

        self.store_dir = store_dir

        # print '#now change current dir to tmp'
        # os.chdir(store_dir) #no neccessary
        # print os.getcwd()

    def print_commet(self):
        print '==================================='

    # 获取当前时间
    def now_date(self):
        # 获得当前时间
        now = datetime.datetime.now()  # ->这是时间数组格式
        # 转换为指定的格式:
        formateDate = now.strftime("%Y%m%d%H%M%S")
        return formateDate

    # 显示图片后缀名
    def file_extension(self, url):
        # get filename
        filename = os.path.basename(url)
        ext = os.path.splitext(filename)[1]
        return ext

    # 保存图片
    def saveFile(self, url, page, idx):
        user_define_name = self.now_date() + '_p_' + str(page) + '_' + string.zfill(idx, 2)  # 补齐2位
        file_ext = self.file_extension(url)  # 后缀名
        save_file_name = user_define_name + "_" + file_ext

        # 不能保存，改用open方法
        # urllib.urlretrieve(item[0], self.save_path + save_file_name)
        # 保存图片
        url = self.CheckUrlValidate(url)
        try:
            pic = requests.get(url, timeout=10)
            f = open(self.store_dir + os.sep + save_file_name, 'wb')
            f.write(pic.content)
            f.close()
            print '\ndone save file ' + save_file_name
        except ReadTimeout:
              print 'save file %s failed. cause by timeout(10)' %(save_file_name)
        except MissingSchema:
            print 'invalid url %s' %(url)
        except Exception, e:
            print e


    #检查url是否包括http:协议
    def CheckUrlValidate(self, url):
        print url
        if not url.startswith('http') and url.startswith("//"):
            url = "http:" + url
        return url
    # 将所有的段子都扣出来，添加到列表中并且返回列表  
    def GetPage(self, page):
        hashMethod = UserDefineHash(15)
        site_url = hashMethod.decrypt('HGLHLHPHFDACACIHIHIHBCOHGGKHNGOGGGMGHGKGBGIGNHKGBGBCMGAGCGAC')
        myUrl = site_url + page + ".html"
        user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        headers = {'User-Agent': user_agent}
        req = urllib2.Request(myUrl, headers=headers)

        print u'\n----background----now loading: page/' + page

        myResponse = urllib2.urlopen(req, data=None, timeout=10)

        #检测网页编码
        # print chardet.detect(myResponse.read())

        #将获取的字符串strTxt做decode时，指明ignore，会忽略非gb2312编码的字符
        myPage = myResponse.read().decode('gb2312','ignore').encode('utf-8')
        # encode的作用是将unicode编码转换成其他编码的字符串
        # decode的作用是将其他编码的字符串转换成unicode编码
        unicodePage = myPage.decode("utf-8")

        #remove emoji[when this page get emoji inside, it'll run error:unichr() arg not in range(0x10000) (narrow Python build)]
        # unicodePage= emojiutil.remove_define_emoji(unicodePage)

        #only do it once
        if self.isFirst:
            self.isFirst = False
            print '====================get the max page number===================='
            self.GetTotalPage(unicodePage)


        # if self.unload_page_num > int(page):
        #     print 'already done load all new page, stop thread now.'
        #     self.enable = False
        #     os._exit(0)

        link_soups = BeautifulSoup(unicodePage)
        parent_divs = link_soups.findAll('div',attrs={'class':'mala-text'})
        myItems = [] #list: store the tup(src, alt)
        for parent_div in parent_divs:
            try:
                link = parent_div.find('img')
                tup1 = (link['src'], link['alt'])
                myItems.append(tup1)
            except KeyError,e: #if u can't get key attr
                print 'KeyError', e
	    except Exception,e: 
	        print 'Other Error', e

        return myItems

    # get the max page number
    def GetTotalPage(self, html):
        # create the BeautifulSoup
        some_soup = BeautifulSoup(html)
        #get the page div
        ele_a = some_soup.find('div', attrs={'class': 'page'})
        #get the last div>a text='末页'
        last_a = ele_a.findAll('a')[-1]
        #substr 0:.html
        pagenum = last_a.get('href')[:-5]
        print 'pagenum :', pagenum
        # print type(last_a)

        self.SaveTotalPageToFile(pagenum)

    # store the max page number to totalpage.ini
    #new_page_num: new max page num
    def SaveTotalPageToFile(self, new_page_num):

        print '====================save the totalpage to totalpage.ini===================='

        file = INIFILE('qiubaiadult_page.ini')

        # must write something if you set is_write to true. otherwise your file become empty.
        is_ok = file.Init(True, True)
        if not is_ok:
            print 'class initializing failed. check the [%s] file first.' % ('totalpage.ini')
            os._exit(0)

        old_page_num = file.GetValue('Main', 'totalpage')
        print '====================the old_page_num is [%s], the new_page_num is [%s]====================' % (old_page_num, new_page_num)
        file.SetValue('Main', 'totalpage', new_page_num)
        #close all
        file.UnInit()

        if int(new_page_num) >= int(old_page_num): #if there is new page
            # self.unload_page_num = int(new_page_num) - int(old_page_num)
            self.unload_page_num = int(new_page_num) - int(old_page_num)
            if self.unload_page_num == 0:   #页码未增加，但是图片新增了
               self.unload_page_num = 1
            elif self.unload_page_num > 0: #增加新页面了，但是旧页上图片存在未下载的情况***会导致下载不会结束
               self.unload_page_num += 1
            print 'since we start at page %s, we still got (%s-%s) pages to load.' %(self.page, self.unload_page_num, self.page)
        else: #nothing new, stop main thread
            print 'Oops! Nothing new. exit main thread now.'
            os._exit(0) #terminal sub thread
            self.enable = False #terminal main thread

    # 用于加载新的段子  
    def LoadPage(self):
        # 如果用户未输入:q则一直运行  
        while self.canLoad:
            # 如果pages数组中的内容小于2个
            # print '\n----background----self.pages length: ' + str(len(self.pages))
            # 预加载2页数据
            if len(self.pages) < 2:
                try:
                    # 获取新的页面
                    myPage = self.GetPage(str(self.page))
                    self.page += 1
                    self.pages.append(myPage)
                    # print 'self.pages ' + str(len(self.pages))
                    print '====================%s============%s' %(self.unload_page_num, self.page)
                    if self.unload_page_num <= self.page:
                        print 'already load all new page, stop sub thread now.'
                        self.canLoad = False #let this thread do nothing
			self.allDone = True

                except Exception, e:
                    print e
            else:
                time.sleep(1)
                #print '\n----background----pause and wait.'
            #print '\n----background----sleep 2s, do not request too fast.'
            time.sleep(2)  # sleep 2s for test

    # show one page after press enter button.
    def ShowOnePage(self, now_page_items, page):
        for idx, item in enumerate(now_page_items):
            print "\ndownload " + item[1]
            self.saveFile(item[0], page, idx)
        #print '========one page done.================='
        print '========Please hit the Enter.================='
        #if self.unload_page_num == page:
        if self.allDone:
            print '========all pages done. clean the repeated files.=========='
            self.CleanRepeatImage() #at last, deal with the repeated images.
            print 'Nothing left. Now close this application.'
            # self.enable = False  #let the main thread know it's time to quit
            os._exit(0) #can teminal main thread.

        # 输出一页后暂停
        time.sleep(1)
        print 'take a snap for 1s.'
        # myInput = raw_input()
        # if myInput == ":q":
        #     self.CleanRepeatImage() #if break manually, must clean work dir.
        #     self.enable = False

    # deal with the repeated image
    def CleanRepeatImage(self):
        if not os.path.exists('repeat'): #store the repeated file
            os.mkdir('repeat')

        hash_imgs = {}  # store the img_hash as key, the filepath as value..
        img_files = os.listdir('tmp')
        img_files.sort()
        for file in img_files:
            #print file
            # print type(file) the type of 'file' is str.
            f = open(os.path.join('tmp', file), 'rb')
            hash_img = hashlib.md5(f.read()).hexdigest()  # md5 this file.
            f.close()
            # print type(hash_img)
            # print hash_img
            if not hash_imgs.has_key(hash_img):
                hash_imgs[hash_img] = file
            else:
                print '--------------'
                print '%s already exsits.' % (file)  # the current file to be record.
                print hash_imgs.get(hash_img)  # the file already record.
                print '--------------'
                # remove it
                f1 = os.path.join('tmp', file)
                os.remove(f1)

        print 'done delete repeat files.'


    def Start(self):
        self.enable = True
        page = self.page
        print u'正在加载中请稍候......'
        # 新建一个线程在后台加载段子并存储
        thread.start_new_thread(self.LoadPage, ())
        time.sleep(2) #wait the sub thread to be done.
        # ----------- 加载处理糗事百科 -----------
        while self.enable:
            # 如果self的page数组中存有元素
            if len(self.pages) > 0:
                now_page_items = self.pages[0]

                # del now page items
                del self.pages[0]
		print '---main thred --', page
                self.ShowOnePage(now_page_items, page)
                page += 1

        print self.enable


# ----------- 程序的入口处 -----------
print u""" 
--------------------------------------- 
   程序：qiubaiAdult--爬虫
   版本：3.0
   作者：guzi
   日期：2017年9月21日
   语言：Python 2.7 
   操作：输入:q退出
   功能：按下回车依次浏览
--------------------------------------- 
"""
myModel = Spider_Model()
print u'请按下回车浏览今日的糗百内容：'
raw_input(' ')
#myModel.page=913 #start from which page, default 1
myModel.Start()
# myModel.CleanRepeatImage()
