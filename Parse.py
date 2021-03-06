from bs4 import BeautifulSoup
import requests
import random
from random import choice
import time
import re
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from fake_useragent import UserAgent
from datetime import datetime
from time import gmtime, strftime
from my_package import db
from my_package.models import Shoe
from abc import ABC, abstractmethod 
from tqdm import tqdm
import queue
import threading

shoes_names_enumerate = {'Велотуфли', 'Туфли','Велообувь','Обувь','Велокроссовки','Кроссовки',
                                      'Велоботинки','Ботинки','велотуфли', 'туфли','велообувь','обувь','велокроссовки',
                                      'кроссовки','велоботинки','ботинки','Велотуфлі', 'Туфлі','Веловзуття','Взуття','Велокросівки','Кросівки',
                                      'Велоботінки','Ботінки','велотуфлі', 'туфлі','веловзуття','взуття','велокросовки',
                                      'кросівки','велоботінки','ботінки', 'Shoes', 'Shoe','shoe','shoes'}
USD_UAH_coef = 28.5

proxies_source_url = 'https://hidemy.name/ru/proxy-list/?country=MDPLRORUSKUA&type=hs#list'
proxies_list = []

def get_html(url, call_time=1):
    time.sleep(random.uniform(1,3)) 
    ua = UserAgent()
    header = {'User-Agent': str(ua.chrome)}
    proxy = {'http': 'http://'+choice(proxies_list)}
    while True:
        try:
            if call_time == 1:
                r = requests.get(url,headers=header, proxies = proxy)
            else:
                r = requests.get(url,headers=header, proxies = proxy, verify=False, timeout=10)
            break
        except:
            proxy = {'http': 'http://'+choice(proxies_list)}


    return r.text

def get_full_html(url, delay=10):
    # time.sleep(random.uniform(3,6))
    # return requests.get(url, headers={'User-Agent': UserAgent().chrome}).content
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(executable_path='./geckod/geckodriver', options = options)
    driver.implicitly_wait(delay)
    driver.get(url)
    html = driver.page_source
    driver.close()
    return html



def get_proxies():
    ua = UserAgent()
    header = {'User-Agent': str(ua.chrome)}
    r = requests.get(proxies_source_url,headers=header)
    html = r.text
    soup = BeautifulSoup(html, 'lxml')
    trs = soup.find('div', class_='table_block').find('tbody').findAll('tr')
    proxies = []
    for idx in range(len(trs)):
        tds = trs[idx].findAll('td')
        ip = tds[0].text
        port = tds[1].text
        proxies_list.append(ip+":"+port)
    


def get_numbers_from_text(text):
    new_str = ''.join((ch if ch in '0123456789.,' else ' ') for ch in text)
    words_list = []
    for w in new_str.split(' '):
        if '.' in w and ',' in w:
            w = w.replace(',', ' ')
            for word in w.split(' '):
                words_list.append(word)
            continue
        words_list.append(w.replace(',','.'))

    numbers=[]
    for word in words_list:
        while len(word)>0 and word[0] == '.':
            word = word[1:]
        while len(word)>0 and word[-1] == '.':
            word = word[:-1]
        if len(word) == 0:
            continue
        if word.replace('.','').isdigit():
            try:
                numbers.append(float(word))
            except:
                pass
    return numbers

def get_size_from_text(text):
    shoes_sizes_sm =  {(22.5, 23.0, 36),
                       (23.0, 24.0, 37),
                        (24.0, 25.0, 38),
                         (25.0, 25.5, 39),
                          (25.5, 26.5, 40),
                           (26.5, 27.0, 41),
                            (27.0, 27.5, 42),
                             (27.5, 28.5, 43),
                              (28.5, 29.0, 44),
                               (29.0, 29.5, 45),
                                (29.5, 30.0, 46),
                                 (30.0, 30.5, 47),
                                  (30.5, 31.0, 48),
                                   (31.0, 31.5, 49),
                                    (31.5, 32.0, 50),
                                     (32.0, 32.5, 51),
                                      (32.5, 33.1, 52)}
    Size = 0
    numbers = get_numbers_from_text(text)
    for number in numbers:
        if number < 22.5 or (number > 52 and number < 225) or number > 330 or (number > 33 and number < 36):
            continue
        if number >= 225:
            number /= 10
        if number < 36:
            for size in shoes_sizes_sm:
                if number >= size[0] and number < size[1]:
                    number = size[2]
        Size = number
        break
    return Size


class Item:
    def __init__(self):
        self.Url = ''
        self.ImageUrl=''
        self.Title=''
        self.Price = 0
        self.Description = ''
        self.set_date()

    def set_date(self):
        curr_time = gmtime()
        year = int(strftime("%Y", curr_time))
        month = int(strftime("%m", curr_time))
        day = int(strftime("%d", curr_time))
        HH = int(strftime("%H", curr_time))
        MM = int(strftime("%M", curr_time))
        self.Date = datetime(year,month,day,HH,MM)

class Shoes:
    def __init__(self, item):
        self.Date = item.Date
        self.Title = item.Title
        self.Description = item.Description
        self.ImageUrl = item.ImageUrl
        self.Url = item.Url
        self.Price = item.Price
        self.Size = get_size_from_text(self.Description + ' '+ self.Title)

    def show(self):
        print(self.Description)
    # def show(self):
    #     print(self.Url +'\n'+self.ImageUrl + '\n'+ 'Title:' +self.Title  +'\n'+'Price: '+str(self.Price)+'\n'+'Size: '+ str(self.Size)+'\n'+str(self.Date) )


class ShoppingWebsite(ABC):
    @abstractmethod
    def get_item_info(self, html):
        pass
    @abstractmethod
    def parse_batch(self, url):
        pass
    @abstractmethod
    def parse_all(self, url):
        pass
    @abstractmethod
    def parse_total_pages(self, url):
        pass


class Xt(ShoppingWebsite):
    def __init__(self):
        pass

    def parse_total_pages(self, url):
        html = get_full_html(url)
        soup = BeautifulSoup(html, 'lxml')
        parent = soup.find("a", string="След.").parent
        pages = int(parent.findAll("a")[-3].text)
        print('XT Pages'+str(pages))
        return int(pages)
    
    def get_item_info(self, html):
        item = Item()
        soup = BeautifulSoup(html, 'lxml')
        item.Url = soup.find('link', rel='canonical').get('href')
        item.Title = soup.find('meta', {'name' : 'title'}).get('content')[:-23]
        item.Description = soup.find('div', {'style':"float:right; width:300px; height:250px; margin:5px;"}).parent.text
        row_date = soup.find("b", string="Добавлено:").parent.text
        year = int(row_date.split(sep=' ')[1].split('.')[2])
        month = int(row_date.split(sep=' ')[1].split('.')[1])
        day = int(row_date.split(sep=' ')[1].split('.')[0])
        HH = int(row_date.split(sep=' ')[2].split(':')[0])
        MM = int(row_date.split(sep=' ')[2].split(':')[1])
        item.Date = datetime(year,month,day,HH,MM)
        for tag in soup.find_all('div', style='float: left;'):
            words = tag.text.split(' ')
            for i in range(len(words)):
                if 'грн.' in words[i]:
                    item.Price = get_numbers_from_text(words[i - 1])[0]
        img_tag = soup.find('img', {'class' : 'postlink img-link'})
        if img_tag is not None:
            item.ImageUrl = img_tag.get('src')
        else:
            img_tag = soup.find('a', {'class': 'highslide'})
            if img_tag is not None:
                item.ImageUrl = 'http://xt.ht/phpbb/'+img_tag.get('href')[1:]

        return item

    def parse_batch(self, url):
        all_a = BeautifulSoup(get_html(url), 'lxml').find_all('a', class_='topictitle')
        for a in all_a:
            print(a)
            if a.get('href') is None:
                print(a)
                print('111NONE')
                continue
            link = a.get('href')
            if link[2:11]!='viewtopic' or ('p=' in link) or ('#unread' in link) or ('start' in link) or ('page' in link):
                print(a)
                print('222NONE')
                continue
            link = 'http://xt.ht/phpbb/'+link[1:]
            item = Item()

            count = 1
            while True:
                try:
                    item = self.get_item_info(get_html(link,count))
                    break
                except:
                    count+=1
                
            
            shoes = Shoes(item)
            shoe = Shoe(Date=shoes.Date, Title = shoes.Title, Description = shoes.Description, Url = shoes.Url, ImageUrl = shoes.ImageUrl, Price = shoes.Price, Size = shoes.Size)
            shoes.show()
            yield shoe

    def parse_all(self, url):
        pages = self.parse_total_pages(url)
        count = 0
        for page in tqdm(range(pages)):
            page_url = url+'&start=' + str(page*40)
            shoes = self.parse_batch(page_url)
            if shoes:
                for shoe in shoes:
                    db.session.add(shoe)
                    db.session.commit()
                    print(str(count)+" :"+shoe.Title)
                    count+=1


        
class Olx(ShoppingWebsite):
    def __init__(self):
        pass
    def get_item_info(self, item_tag):
        item = Item()
        item.Url = item_tag.get('href')
        item.Title = item_tag.text
        price_tag_text = ""
        count = 1
        while True:
            try:
                soup = BeautifulSoup(get_html(item.Url,count), 'lxml')
                price_tag_text = soup.find('div', class_ = 'pricelabel').text
                break
            except:
                count+=1

        string_price = ""
        in_usd = False
        for c in price_tag_text:
            if c in "0123456789":
                string_price+=c
            if c == '$':
                in_usd=True
        price = float(string_price)
        if in_usd:
            price *= USD_UAH_coef
        item.Price = price
        item.Description = soup.find('div', id = 'textContent').text
        item.ImageUrl = soup.find('img', class_ = 'bigImage {nr:1}').get('src').split(';')[0]
        return item

    def parse_total_pages(self, url):
        html = get_html(url)
        pages = BeautifulSoup(html, 'lxml').find('div', class_='pager rel clr').find_all('a', class_='block br3 brc8 large tdnone lheight24')[-1].get('href').split('page=')[1]
        print('OLX pages '+str(pages))
        return int(pages)

    def parse_batch(self, url):
        batch=[]
        page_html = None 
        items_parents_tags = None
        while True:
            page_html = get_html(url)
            items_parents_tags = BeautifulSoup(page_html, 'lxml').find('table',class_='fixed offers breakword redesigned').find_all('h3',class_='lheight22 margintop5')
            if items_parents_tags[0] is not None:
                break
        items_tags = []
        for t in items_parents_tags:
            items_tags.append(t.find('a', class_='marginright5 link linkWithHash detailsLink'))  

        for item_tag in items_tags:
            title = item_tag.text
            for word in shoes_names_enumerate:
                if word in title:
                    item = self.get_item_info(item_tag)
                    shoes = Shoes(item)
                    shoe = Shoe(Date=shoes.Date, Title = shoes.Title, Description = shoes.Description, Url = shoes.Url, ImageUrl = shoes.ImageUrl, Price = float(shoes.Price), Size = float(shoes.Size))
                    yield shoe
                    break
     
    def parse_all(self, url):
        count = 0
        pages = self.parse_total_pages(url)
        for page in tqdm(range(pages)):
            page_url = url+'?page=' + str(page)
            for shoe in self.parse_batch(page_url):
                print(str(count)+" :"+shoe.Title)
                db.session.add(shoe)
                db.session.commit()
                count+=1
                
            

def olx_parse():
    o = Olx()
    olx_items = o.parse_all('https://www.olx.ua/hobbi-otdyh-i-sport/sport-otdyh/velo/veloaksessuary/')


def xt_parse():
    x = Xt()
    x.parse_all('http://xt.ht/phpbb/viewforum.php?f=2725&price_type_sel=0&sk=t&sd=d')

# olx_thread = threading.Thread(target=olx_parse, name='olx')
# xt_thread = threading.Thread(target=xt_parse, name='xt')

# olx_thread.daemon = True
# xt_thread.daemon = True
# olx_thread.start()
# xt_thread.start()

# input()
 

get_proxies()
olx_parse()
xt_parse()
 











