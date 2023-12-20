import streamlit as st
import random, requests
from lxml import etree


# 定义一个生成随机user-agent的类
class FakeUA:
    num1 = random.randint(55, 62)
    num2 = random.randint(0, 3200)
    num3 = random.randint(0, 140)
    version_ = 'Chrome/{}.0.{}.{}'.format(num1, num2, num3)
    os_type = ['(Windows NT 6.1; WOW64)', '(Windows NT 10.0; WOW64)', '(X11; Linux x86_64)',
               '(Macintosh; Intel Mac OS X 10_12_6)']

    @classmethod
    def get_ua(cls):
        return ''.join(
            ['Mozilla/5.0', random.choice(cls.os_type), 'AppleWebKit/537.36', '(KHTML, like Gecko)', cls.version_,
             'Safari/537.36'])

# 定义爬虫类Spiders，继承FakeUA类
class Spiders(FakeUA):
    def __init__(self, url, headers=None):
        self.url = url
        self.headers = headers
        if not self.headers:
            self.headers = {}
            self.headers['user-agent'] = self.get_ua()

    def spider(self, url):
        try:
            res = requests.get(url, headers=self.headers)
            if res.status_code == 200:
                res.encoding = 'utf-8'
                return res.text
        except requests.ConnectionError:
            st.error('无法获取数据，请检查网络连接或站点是否可用')
            return None

    def get_cityinfo(self):
        res = self.spider(self.url)
        if res:
            html = etree.HTML(res)
            cityenums = html.xpath('//div[@class="city-enum fl"]')
            self.city_dict = {}
            for i in cityenums:
                city_names = i.xpath('./a/text()')
                city_urls = i.xpath('./a/@href')
                for k, v in zip(city_names, city_urls):
                    self.city_dict[k.strip()] = 'https:' + v

    def get_maxpagenum(self):
        loupan_url = self.city_url + '/loupan'
        res = self.spider(loupan_url)
        if not res:
            return 'error'
        html = etree.HTML(res)
        total_num = int(html.xpath('//span[@class="value "]/text()')[0])  # 注意value后面有空格
        maxpage = total_num // 10 if total_num % 10 == 0 else total_num // 10 + 1
        return maxpage

    @st.cache(allow_output_mutation=True)
    @st.cache(suppress_st_warning=True)
    def get_citydata(self, pages_choice):
        maxpage_num = self.get_maxpagenum()
        if maxpage_num == 'error':
            st.error('获取最大页数失败，无法继续。')
            return 'error'
        st.write(f'您选择获取数据的城市为{self.city_name}，共有{maxpage_num}页数据')
        self.data_list = []

        # 显示进度条
        progress_bar = st.progress(0)

        for i in range(1, pages_choice + 1):
            # 更新进度条
            progress_bar.progress(i / pages_choice)
            st.write(f'正在获取第{i}页数据...')

            city_page_url = f"{self.city_url}/loupan/pg{str(i)}"
            res = self.spider(city_page_url)
            if res:
                html = etree.HTML(res)
                map = lambda x: x[0] if x else '未知'
                items = html.xpath('//div[@class="resblock-desc-wrapper"]')
                self.fieldnames = ['名称', '地址', '户型', '面积', '均价', '总价']
                for item in items:
                    title = map(item.xpath('div[@class="resblock-name"]/a/text()'))
                    address = item.xpath('string(div[@class="resblock-location"])').replace(' ', '').replace('\n', '')
                    rooms = map(item.xpath('a[@class="resblock-room"]/span/text()'))
                    area = map(item.xpath('div[@class="resblock-area"]/span/text()'))
                    average_price = ''.join(item.xpath('div[@class="resblock-price"]//span//text()')).replace('\xa0', '')
                    sum_price = map(item.xpath('div[@class="resblock-price"]/div[@class="second"]/text()'))
                    if sum_price == []: sum_price = '价格待定'
                    data_list = [title, address, rooms, area, average_price, sum_price]
                    data_dict = {k: v for k, v in zip(self.fieldnames, data_list)}
                    self.data_list.append(data_dict)
                    st.write(f'名称：{title}    地址：{address}    户型：{rooms}    面积：{area}    均价：{average_price}    总价：{sum_price}')
        st.write(f'\n本次共获取数据 {len(self.data_list)} 条')
