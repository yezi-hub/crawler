from django.db import models  

class CrawlerData(models.Model):  
    url = models.CharField(max_length=1000, null=True, blank=True)  
    suburl = models.CharField(max_length=1000, null=True, blank=True)  
    keyword = models.CharField(max_length=800, null=True, blank=True)  
    news_title = models.CharField(max_length=800, null=True, blank=True)  
    news_content = models.TextField(null=True, blank=True)  
    news_release_time = models.CharField(max_length=100, null=True, blank=True)  
    crawler_date = models.DateTimeField(auto_now_add=True)  

class Meta:  
    db_table = 'crawler_data'  
    managed = False  # 让 Django 不主动管理这个表
