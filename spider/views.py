import json

import time
from django.http import HttpResponseRedirect, HttpResponse
import os
# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators import csrf
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from guoshui import guoshui
from django.views.decorators.csrf import csrf_exempt
from get_db import get_db, add_task, job_finish
from log_ging.log_01 import *

# 表单
def search_form(request):
    return render(request, 'index.html')


# 接收请求数据
def search(request):
    request.encoding = 'utf-8'
    if 'q' in request.GET:
        message = '你搜索的内容为: ' + request.GET['q']
    else:
        message = '你提交了空表单'
    return HttpResponse(message)


# 接收POST请求数据
@csrf_exempt
def search_post(request):
    # ctx = {}
    # ctx['rlt'] = "信息未输入"
    logger = create_logger()
    logger.info("开始接受请求")
    if request.POST:
        # ctx['rlt'] = request.POST['BatchID']
        post_data = dict(request.POST)
        logger.info("接受请求成功")
        # ctx['rlt'] = "请输入正确信息"
        if post_data['BatchID'] and post_data['BatchYear'] and post_data['BatchMonth'] and post_data['CompanyID'] and  post_data['CustomerID'] and post_data['TaxId'] and post_data['TaxPwd'] and post_data['jobname'] and post_data['jobparams']:
            account = post_data['TaxId'][0]
            pwd = post_data['TaxPwd'][0]
            batchid = post_data['BatchID'][0]
            batchyear = int(post_data['BatchYear'][0])
            batchmonth = int(post_data['BatchMonth'][0])
            companyid = int(post_data['CompanyID'][0])
            customerid = int(post_data['CustomerID'][0])
            jobname = post_data['jobname'][0]
            jobparams = post_data['jobparams'][0]
            #获取数据库
            host, port, db = get_db(companyid)
            #添加任务
            logger.info("添加任务到数据库")
            add_task(host, port, db, batchid, batchyear, batchmonth, companyid, customerid, jobname, jobparams)
            logger.info("任务添加成功,开始爬取")
            try:
                gs = guoshui(user=account, pwd=pwd, batchid=batchid, batchyear=batchyear, batchmonth=batchmonth,
                         companyid=companyid, customerid=customerid)
            # gs = guoshui(user=account, pwd=pwd,batchid=123,batchmonth=456,batchyear=789,companyid=12,customerid=13)
                cookies, session = gs.login()
                jsoncookies = json.dumps(cookies)
                with open('cookies.json', 'w') as f:  # 将login后的cookies提取出来
                    f.write(jsoncookies)
                    f.close()
                dcap = dict(DesiredCapabilities.PHANTOMJS)
                dcap["phantomjs.page.settings.userAgent"] = (
                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36')
                dcap["phantomjs.page.settings.loadImages"] = True
                # browser = webdriver.PhantomJS(
                # executable_path='D:/BaiduNetdiskDownload/phantomjs-2.1.1-windows/bin/phantomjs.exe',
                # desired_capabilities=dcap)
                browser = webdriver.PhantomJS(
                executable_path='/home/tool/phantomjs-2.1.1-linux-x86_64/bin/phantomjs',
                desired_capabilities=dcap)
                browser.implicitly_wait(10)
                browser.viewportSize = {'width': 2200, 'height': 2200}
                browser.set_window_size(1400, 1600)  # Chrome无法使用这功能
                index_url = "http://dzswj.szgs.gov.cn/BsfwtWeb/apps/views/myoffice/myoffice.html"
                browser.get(url=index_url)
                browser.delete_all_cookies()
                with open('cookies.json', 'r', encoding='utf8') as f:
                    cookielist = json.loads(f.read())
                for (k, v) in cookielist.items():
                    browser.add_cookie({
                    'domain': '.szgs.gov.cn',  # 此处xxx.com前，需要带点
                    'name': k,
                    'value': v,
                    'path': '/',
                    'expires': None})
                shenbao_url = 'http://dzswj.szgs.gov.cn/BsfwtWeb/apps/views/sb/cxdy/sbcx.html'
                browser.get(url="http://dzswj.szgs.gov.cn/BsfwtWeb/apps/views/myoffice/myoffice.html")
                browser.get(url=shenbao_url)
                time.sleep(3)
                gs.shuizhongchaxun(browser)
                # gs.parse_biaoge(browser)

                # # 国税缴款查询
                # jk_url = 'http://dzswj.szgs.gov.cn/BsfwtWeb/apps/views/sb/djsxx/jk_jsxxcx.html'
                # browser.get(url=jk_url)
                # gs.parse_jiaokuan(browser)
            #
                # # 地税查询
                # ds_url = 'http://dzswj.szgs.gov.cn/BsfwtWeb/apps/views/sb/djsxx/djsxx.html'
                # browser.get(url=ds_url)
                # gs.dishui(browser)
            except Exception as e:
                job_finish(host, port, db, batchid, companyid, customerid, '-1', 'e')
            job_finish(host, port, db, batchid,companyid,customerid, '1', '成功爬取')
            print("爬取完成")
            browser.quit()
            return HttpResponse("爬取完成")

    return HttpResponse("爬取失败")
