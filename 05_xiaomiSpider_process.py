import  requests
import json
from multiprocessing import Process,Lock,Queue
import random
import time
from fake_useragent import FakeUserAgent
from lxml import etree
import csv

class XiaomiSpider():
    def __init__(self):
        self.url='http://app.mi.com/categotyAllListApi?page={}&categoryId={}&pageSize=30'
        self.q=Queue()
        self.i=0
        self.lock=Lock()
        self.f=open('小米.csv','a',newline='')
        self.writer=csv.writer(self.f)

    def get_html(self,url):
        headers={'User-Agent':FakeUserAgent().random}
        html=requests.get(url=url,headers=headers).text
        return html

    #获取所有类别的ID
    def get_id(self):
        url='http://app.mi.com/'
        html=self.get_html(url)
        p=etree.HTML(html)
        r_list=p.xpath('//div[@class="sidebar"]/div[2]/ul[1]/li')
        for i in r_list:
            id=i.xpath('./a/@href')[0].split('/')[-1]
            # print(id)
            name=i.xpath('./a/text()')[0]
            self.url_in(id)
    #url入队列
    def url_in(self,id):
        total=self.get_total(id)
        for page in range(0,total):
            url=self.url.format(page,id)
            self.q.put(url)

    def get_total(self,id):
        url=self.url.format(0,id)
        html=json.loads(self.get_html(url))
        count=int(html['count'])
        if count%30==0:
            total=count//30
        else:
            total=count//30+1

        return total

    #线程事件函数
    def parse_html(self):
        while True:
            if not self.q.empty():
                url=self.q.get()
                html=json.loads(self.get_html(url))
                print(html)
                item={}
                app_list=[]
                for app in html['data']:
                    item['name']=app['displayName']
                    item['type']=app['level1CategoryName']
                    item['link']=app['packageName']
                    print(item)
                    app_list.append((item['name'],item['type'],item['link']))
                    self.lock.acquire()
                    self.writer.writerows(app_list)
                    self.lock.release()
                    time.sleep(random.randint(0,1))

                    #加锁
                    self.lock.acquire()
                    self.i+=1
                    self.lock.release()
            else:
                break

    def run(self):
        id=self.get_id()
        self.url_in(id)
        t_list=[]
        for i in range(2):
            t=Process(target=self.parse_html)
            t_list.append(t)
            t.start()

        for i in t_list:
            i.join()

        #关闭文件
        self.f.close()

        print('数量:',self.i)






if __name__ == '__main__':
    begin=time.time()
    spider=XiaomiSpider()
    spider.run()
    end=time.time()
    print('执行时间{}'.format(end-begin))
