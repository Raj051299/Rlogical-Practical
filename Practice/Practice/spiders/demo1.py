import datetime
import json
import re
from urllib.parse import quote,unquote
import pandas as pd
import requests
import scrapy
from scrapy.http import HtmlResponse

main_data=[]

class Demo(scrapy.Spider):
    name='demo1'
    x=0

    headers = {
        'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        'accept-language': "en-US,en;q=0.9,fil;q=0.8",
        'cache-control': "no-cache",
        'connection': "keep-alive",
        'content-type': "application/x-www-form-urlencoded",
        'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
        'postman-token': "e3d517b0-c314-3bf4-7afb-fa8b8bf483fe"
    }

    def start_requests(self):
        df =pd.read_excel('Playhousesquare_Input.xlsx')

        links=df['Input']
        s = requests.Session()

        for l in links:
            print(l)
            res0=s.get(l, headers=self.headers)
            resp0=HtmlResponse(url='',body=res0.content)

            link=resp0.xpath('//span[contains(text(),"Availability")]/following-sibling::span/a/@href').get()
            print(link)

            res1=s.get(link,headers=self.headers)


            t1=re.findall(r'sToken: "(.*?)"',res1.text)[0]

            try:

                total_pages = re.findall(r' total_pages: "(.*?)"', res1.text)[0]
            except:
                total_pages=0

            if int(total_pages)>1:

                articalid=link.split('article_id=')[-1]
                for j in range(1, int(total_pages)+1):

                    if j==1:
                        nurl=link
                    else:

                        nurl=f'https://tickets.playhousesquare.org/online/default.asp?sToken={t1}&BOset::WScontent::SearchResultsInfo::current_page={str(j)}&doWork::WScontent::getPage=&BOparam::WScontent::getPage::article_id={articalid}'

                    res2=s.get(nurl,headers=self.headers)

                    ids = re.findall(r'searchResults : (.*?)searchFilters', res2.text, re.DOTALL)[0][:-4].replace('\n',
                                                                                                                      '').replace(
                        "\\'", "'")

                    data = json.loads(ids)

                    for d in data:
                        pid = d[0]

                        furl = 'https://tickets.playhousesquare.org/online/mapSelect.asp'

                        payload = f"sToken={t1}&BOparam%3A%3AWSmap%3A%3AloadMap%3A%3Aperformance_ids={pid}&createBO%3A%3AWSmap=1\n"

                        res3=s.post(furl,headers=self.headers,data=payload)

                        resp=HtmlResponse(url=furl,body=res3.content)

                        name=resp.xpath('//*[@class="item-short-description"]/text()').get()

                        if name:

                            date=resp.xpath('//span[@class="date"]/text()').get()

                            date1=date.split(',')[1].strip().split()
                            month_number = datetime.datetime.strptime(date1[0], '%b').month
                            date2=date.split(',')[2].strip().split(' ')[0]

                            eventdate=datetime.date(int(date2), month_number,int(date1[1]))
                            eventdatefinal=datetime.datetime.strftime(eventdate,"%Y/%m/%d")

                            vanue=resp.xpath('//p[@class="performance-venue"]/text()').get()

                            mixprice=resp.xpath('//div[@class="zone-label"]/text()').getall()
                            mixprice=[i.strip() for i in mixprice]
                            mixprice1=resp.xpath('//div[@class="item-box-detail-data price-zone-price"]/text()').getall()
                            mixprice1 = [i.strip() for i in mixprice1]
                            pricing1=[]
                            for i,j in zip(mixprice,mixprice1):
                                a1=f'{i}:{j}'
                                pricing1.append(a1)

                            pricing=' | '.join(pricing1)


                            ticket=resp.xpath('//g[@id="seatGroup"]//g//circle')


                            sections=resp.xpath('//g[@id="seatGroup"]//g//circle/@data-tsdesc').getall()
                            sections=set([i[:-7] for i in sections])


                            item={}

                            item['EventUrl']=l
                            item['EventName']=name
                            item['EventDate']=eventdatefinal
                            item['EventDate1']=date
                            item['EventVenue']=vanue
                            item['AllAvailableTickets']=len(ticket)
                            item['AllOrchestraPricing']=pricing
                            item['AllSectionName']='|'.join(sections)
                            self.x+=1

                            print(item,'....',self.x)

                            main_data.append(item)
                        else:
                            print('Not available')

    def close(spider, reason):
        df2=pd.DataFrame(main_data)

        print(df2)

        df2.to_excel('All_data.xlsx')

if __name__ == '__main__':
    from scrapy.cmdline import execute
    execute('scrapy crawl demo1'.split())