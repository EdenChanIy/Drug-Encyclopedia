# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.exceptions import DropItem
import json
from quotesbot.items import QuotesbotItemTCM
from quotesbot.items import QuotesbotItemWM
from scrapy.pipelines.images import ImagesPipeline
import scrapy
import pymysql

#输出为json文件
class QuotesbotPipeline(object):
    def __init__(self):
        pass

    def open_spider(self, spider):
        if(spider.name=='toscrape-tcm'):
            self.file0 = open('data_tcm.json', 'w', encoding='utf-8')
        elif(spider.name=='toscrape-wm'):
            self.file1 = open('data_wm.json', 'w', encoding='utf-8')

    def close_spider(self, spider):
        if(spider.name=='toscrape-tcm'):
            self.file0.close()
        elif(spider.name=='toscrape-wm'):
            self.file1.close()

    def process_item(self, item, spider):
        #根据抓取数据类型输出到不同文件中
        if isinstance(item, QuotesbotItemTCM):
            lines = json.dumps(dict(item), ensure_ascii=False) + '\n'
            self.file0.write(lines)
            return item
        if isinstance(item, QuotesbotItemWM):
            if item['name']:
                lines = json.dumps(dict(item), ensure_ascii=False) + '\n'
                self.file1.write(lines)
                return item
            else:
                #丢弃掉名称为空值的数据
                raise DropItem("Missing name in %s" % item)      

#爬取图片
class ImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        for image_url in item['image_urls']:
            yield scrapy.Request(image_url)

#存入mysql
class MySQLPipeline(object):
    tcmInsert = '''insert into drug_encyclopedia(
                    category,name,type,alias,medicinal_part,component,functional_manage,
                    usage_dosage,prescription,clinical_application,compat_incompat)
                    values(0,'{name}','{type}','{alias}','{medicinal_part}','{component}','{functional_manage}',
                    '{usage_dosage}','{prescription}','{clinical_application}','{compat_incompat}')'''
    wmInsert = '''insert into drug_encyclopedia(category,name,type,component,functional_manage,usage_dosage,
                    pharmacological,compat_incompat,adverse_reactions,matters) 
                    values(1,'{name}','{type}','{component}','{functional_manage}','{usage_dosage}',
                    '{pharmacological}','{compat_incompat}','{adverse_reactions}','{matters}')'''
    def __init__(self, settings):
        self.settings = settings
    
    def process_item(self, item, spider):
        if isinstance(item, QuotesbotItemTCM):
            if item['alias'] is None:
                item['alias'] = 'null'
            if item['medicinal_part'] is None:
                item['medicinal_part'] = 'null'
            if item['component'] is None:
                item['component'] = 'null'
            if item['functional_management'] is None:
                item['functional_management'] = 'null'
            if item['usage_dosage'] is None:
                item['usage_dosage'] = 'null'
            if item['prescription'] is None:
                item['prescription'] = 'null'
            if item['clinical_application'] is None:
                item['clinical_application'] = 'null'
            if item['compatibility_incompatibility'] is None:
                item['compatibility_incompatibility'] = 'null'
            sqltext = self.tcmInsert.format(
                name=pymysql.escape_string(item['name']),
                type=pymysql.escape_string(item['type']),
                alias=pymysql.escape_string(item['alias']),
                medicinal_part=pymysql.escape_string(item['medicinal_part']),
                component=pymysql.escape_string(item['component']),
                functional_manage=pymysql.escape_string(item['functional_management']),
                usage_dosage=pymysql.escape_string(item['usage_dosage']),
                prescription=pymysql.escape_string(item['prescription']),
                clinical_application=pymysql.escape_string(item['clinical_application']),
                compat_incompat=pymysql.escape_string(item['compatibility_incompatibility'])
            )
            self.cursor.execute(sqltext)
            return item
        elif isinstance(item, QuotesbotItemWM):
            sqltext = self.wmInsert.format(
                name=pymysql.escape_string(item['name']),
                type=pymysql.escape_string(item['type']),
                component=pymysql.escape_string(item['component']),
                functional_manage=pymysql.escape_string(item['functional_management']),
                usage_dosage=pymysql.escape_string(item['usage_dosage']),
                pharmacological=pymysql.escape_string(item['pharmacological']),
                compat_incompat=pymysql.escape_string(item['compatibility_incompatibility']),
                adverse_reactions=pymysql.escape_string(item['adverse_reactions']),
                matters=pymysql.escape_string(item['matters'])
            )
            self.cursor.execute(sqltext)
            return item


    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)
    
    def open_spider(self, spider):
        self.connect = pymysql.connect(
             host=self.settings.get('MYSQL_HOST'),
            port=self.settings.get('MYSQL_PORT'),
            db=self.settings.get('MYSQL_DBNAME'),
            user=self.settings.get('MYSQL_USER'),
            passwd=self.settings.get('MYSQL_PASSWD'),
            charset='utf8',
            use_unicode=True
        )
        self.cursor = self.connect.cursor()
        self.connect.autocommit(True)

    def close_spider(self, spider):
        self.cursor.close()
        self.connect.close()