import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re, time

#获取标题和正文的内容
def get_page_data(url,key_word = ""):
    # 使用无头浏览器，这里以Chrome为例
    options = Options()
    options.add_argument('headless')  # 使用无头模式,不用打开浏览器，从底层进行通讯
    options.add_argument('--log-level=3')  # 不打印驱动的日志
    # driver:一个chrome的浏览器对象
    driver = webdriver.Chrome(options=options, executable_path="e:\\chromedriver.exe")
    #driver = webdriver.Chrome( executable_path="e:\\chromedriver.exe")
    driver.get(url)  # 浏览器对象访问某个网址
    html = driver.page_source  # 获取页面的源码
    soup = BeautifulSoup(html, 'html.parser')
    h1s = soup.find_all('h1')
    if not h1s:
        time.sleep(3)
        html = driver.page_source  # 获取页面的源码
        soup = BeautifulSoup(html, 'html.parser')

    page_publish_time = time.strftime("%Y-%m-%d %H:%M:%S")
    if re.search(r"\d{4}\s*-\d{2}\s*-\d{2}\s*\d{2}\s*:\d{2}", html):
        page_publish_time = re.search(r"\d{4}\s*-\d{2}\s*-\d{2}\s*\d{2}\s*:\d{2}", html).group()
    # 获取标题
    title = ''

    # 优先查找h1标签
    h1s = soup.find_all('h1')
    title = ""
    for h1 in h1s:
        if len(h1.get_text(strip=True)) >= len(title):
            title = h1.get_text(strip=True)

    if not title.strip():
        all_texts = soup.stripped_strings  # 获取页面的所有文本
        title = None
        for text in all_texts:
            if len(text) > 6 :  # 检查文本的字符长度
                title = text
                break  # 找到第一个符合条件的文本后停止循环

    # 获取正文内容
    content = ''
    # 策略：
    # 查找 tag 下的所有直接子孙标签的p，把p的正文存到列表中，然后取出p内容最多的作为正文即可。
    # 查找 tag 下的所有直接子标签
    all_content = []
    for tag in soup.find_all(True):
        content = ""
        for child in tag.find_all(True, recursive=False):  # True 表示查找所有标签，recursive=False 只找直接子标签
            if child.name == 'p':  # 如果子元素是 p 标签
                p_tag_text = child.get_text(strip=True)
                if p_tag_text:
                    content += p_tag_text + '\n'
            else:
                # 查找直接子标签中的 p 标签
                secondary_p_tags = child.find_all('p', recursive=False)  # 只查找一级 p 标签
                for p in secondary_p_tags:
                    p_tag_text = p.get_text(strip=True)
                    if p_tag_text:
                        content += p_tag_text + '\n'
        if "联系我们" in content or "广告服务" in content or "举报电话" in content or "服务邮箱" in content or "互联网新闻信息服务许可证" in content \
                or "增值电信业务经营许可证" in content or " 广播电视节目制作经营许可证" in content or "京ICP证" in content or "all rights reserved" in content:
            continue
        all_content.append(content)
    content = max(all_content, key=len)

    page_data = {}
    page_data["suburl"] = url
    pattern = r'https?://([^/]+)'
    match = re.search(pattern, url)
    if match.group(1):
        page_data["url"] = match.group(1)
    else:
        page_data["url"] = ""

    page_data["keyword"]=key_word
    if title is not None:
        page_data["news_title"] =title.strip()
    else:
        page_data["news_title"] = ""
    if content is not None:
        page_data["news_content"] = content.strip()
    else:
        page_data["news_content"] =""
    if page_publish_time is not None:
        page_data["news_release_time"] = page_publish_time.strip()
    else:
        page_data["news_release_time"] =time.strftime("%Y-%m-%d %H:%M:%S")

    page_data["crawler_date"] = time.strftime("%Y-%m-%d %H:%M:%S")

    return page_data

if __name__ == "__main__":
    url = "https://www.sohu.com/a/821021739_120578424?scm=10001.247_14-200000.0.10006.a3_504043-a2_3X2523&spm=smpc.channel_217.block3_93_gPMjDz_1_fd.4.1730164289905Lsz16yJ_397"
    #url = "https://163.com/news/article/JFLIQ4CG000189FH.html?clickfrom=w_yw"
    #url = "http://society.people.com.cn/n1/2024/1025/c1008-40346973.html"
    #url = "https://news.sina.com.cn/c/2024-10-29/doc-incuehui9015182.shtml"
    #url = "https://content-static.cctvnews.cctv.com/snow-book/index.html?item_id=16860892793570580930&toc_style_id=feeds_default&share_to=copy_url&track_id=dce2577e-01e0-40bb-b2f9-40c4033345a6"
    #url = "https://baijiahao.baidu.com/s?id=1813844243039980555&wfr=spider&for=pc"
    #url ="https://finance.china.com.cn/money/"
    data_dict = get_page_data(url)
    print(data_dict["news_title"])
    print(data_dict["news_content"])
    print(data_dict["news_release_time"])