import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from util.get_links import extract_valid_links
import re,time,os
import queue
from util.page_parser import get_page_data
from util.write_data import write_data_to_db
import random
from util.pickle_util import pickle_dump_dicts,pickle_load_dicts
import traceback
import threading
import tldextract,sys
import multiprocessing
from multiprocessing import current_process
from config.proj_vars import key_words
from playwright.sync_api import sync_playwright


def extract_domain(url):
    # 使用 tldextract 解析 URL
    extracted = tldextract.extract(url)
    # 构建完整域名
    domain = f"{extracted.domain}.{extracted.suffix}"
    return domain
#

#获取网页的原码
# def get_html(url):
#     options = Options()
#     options.add_argument('headless')  # 使用无头模式,不用打开浏览器，从底层进行通讯
#     options.add_argument('--log-level=3')  # 不打印驱动的日志
#     # driver:一个chrome的浏览器对象
#     driver = webdriver.Chrome(options=options, executable_path="e:\\chromedriver.exe")
#     # driver = webdriver.Chrome( executable_path="e:\\chromedriver.exe")
#     driver.get(url)  # 浏览器对象访问某个网址
#     html = driver.page_source  # 获取页面的源码
#     return html#

def get_html(url):
    with sync_playwright() as playwright:
        # 启动 Chromium 浏览器
        browser = playwright.chromium.launch(headless=True)  # headless=True 表示无头模式
        page = browser.new_page()

        page.goto(url)

        # 等待页面加载
        page.wait_for_load_state("domcontentloaded")

        # 获取网页源码
        html = page.content()

        # 关闭浏览器
        browser.close()

        return html

def get_url_scope(seed_urls):
    url_scope = []
    for seed_url in seed_urls:
        base_url = extract_domain(seed_url)
        if base_url:
            url_scope.append(base_url)
    return url_scope

def get_base_url(url):
    pattern = r'https?://[^/]+'
    match = re.search(pattern, url)
    base_url = ""
    if match.group():
        base_url = match.group()
    else:
        print("网址中 %s 的base url没有匹配到" % url)
        base_url =""
    return base_url

#把种子url页面中的所有链接提取出来
def get_seed_url(crawl_urls,q):
    to_be_crawl_urls = []
    for url in crawl_urls:
        base_url = get_base_url(url)
        if not base_url:
            print("链接 %s 中的base url 没有取到" %url)
            continue
        html = get_html(url)
        valid_urls = extract_valid_links(html,base_url)
        to_be_crawl_urls.extend(valid_urls)
    random.shuffle(to_be_crawl_urls)
    for url in to_be_crawl_urls:
        q.put(url)

    return

def extract_link_to_queue(url,q,url_scope):
    html = get_html(url)
    base_url = get_base_url(url)
    links = extract_valid_links(html, base_url)
    for link in links:
        for base_url in url_scope:#判断当前链接是否在允许的url范围内
            if base_url in link:
                #print("入队列的url:" ,link)
                q.put(link)
                break



def judge_keyword_in_page(key_words,title,content):
    contain_keywords = []
    for key_word in key_words:
        if key_word in title+content:
            contain_keywords.append(key_word)
    return "&&".join(contain_keywords)

def judge_page_content_if_write_to_db(data,key_words,exclude_content_list,exclude_url_list):
    if "302" in data["news_title"] or "404" in data["news_title"] or "301" in data["news_title"]:
        return
    if len(data["news_title"]) >= 5 and len(data["news_content"]) >= 300:
        if key_words:
            for key_word in key_words:
                if key_word and key_word in data["news_title"] + data["news_content"]:
                    contain_keywords = judge_keyword_in_page(key_words, data["news_title"], data["news_content"])
                    data["keyword"] = contain_keywords
                    print("开始入库",data)
                    write_data_to_db(data,exclude_content_list,exclude_url_list)
                    print("成功入库：",key_word, time, data)
                    return True
        else:
            write_data_to_db(data,exclude_content_list,exclude_url_list)
            return True
    return False

# 定义任务函数，让每个进程将共享计数器加1
def increment_crawl_url_counter(shared_counter,lock):
    # 加锁并累加1
    with lock:  # 使用锁避免竞争条件
        shared_counter.value += 1
        print(f"Process {multiprocessing.current_process().name}:目前抓取的url总数是 {shared_counter.value}")

# 定义任务函数，让每个进程将共享计数器加1
def increment_get_content_url_counter(shared_counter,lock):
    # 加锁并累加1
    with lock:  # 使用锁避免竞争条件
        shared_counter.value += 1
        print(f"Process {multiprocessing.current_process().name} ：目前成功获取内容的url总数是 {shared_counter.value}")

#参数lock:进程锁
#参数key_words：页面中需要包含的关键词列表
#参数url_scope_list：共享列表，存储url的爬取范围
#参数：content_page_dict：共享字典，存储被爬取过页面内容的url字典，value是时间戳
#参数：index_page_dict：共享字典，存储被爬取过列表页面的url字典，value是时间戳
#参数：crawl_url_counter：共享整数变量，存储爬取过了多少url的数量
#参数：get_content_url_counter：共享整数变量，存储成功爬取过正文的url数量
#参数：q，存放待爬取url的进程队列
#参数：crawl_page_num：每个进程最多可以爬取最大的正文页面数量
def task(message_queue,lock,key_words,url_scope_list,content_page_dict,index_page_dict,crawl_url_counter,get_content_url_counter,q,crawl_page_num=1):
    times = 0
    process_name = current_process().name
    while times < crawl_page_num:
        print("&&&&&&&&&&&&&&", process_name, times)
        try:
            if q.qsize() > 0:
                url = q.get(timeout=10).strip()  # 设置超时，防止永久阻塞
                print("当前爬取的Url:", url)
                # 情况1：url没有出现在2个字典中，说明从来没有被爬取过
                if url not in content_page_dict and url not in index_page_dict:
                    data = get_page_data(url)
                    extract_link_to_queue(url, q, url_scope_list)
                    increment_crawl_url_counter(crawl_url_counter, lock)  # 爬取过的url总数+1
                    content_page_dict[url] = round(time.time(), 0)  # 爬取过的url加入到字典中，设定好时间戳作为value
                    # 如果爬取的正文或者标题包含了关键字，则写入到数据库
                    if judge_page_content_if_write_to_db(data, key_words):
                        times += 1  # 爬取的数量加1
                        increment_get_content_url_counter(get_content_url_counter, lock)  # 成功爬取到内容的url总数+1

                # 情况2：url在conent_page_dict被当做正文页面爬取过
                elif url in content_page_dict:
                    if time.time() - content_page_dict[url] < 3600 * 24:  # 小于1天就不爬了
                        continue
                    else:
                        data = get_page_data(url)
                        extract_link_to_queue(url, q, url_scope_list)
                        increment_crawl_url_counter(crawl_url_counter, lock)  # 爬取数量+1
                        if judge_page_content_if_write_to_db(data, key_words):
                            times += 1
                            increment_get_content_url_counter(get_content_url_counter, lock)  # 成功爬取到内容的url总数+1

                # 情况3：url在index_page_dict被当做列表页面爬取过
                elif url in index_page_dict:
                    if time.time() - index_page_dict[url] < 3600:  # 小于1小时就不爬了
                        continue
                    else:
                        index_page_dict[url] = round(time.time(), 0)
                        extract_link_to_queue(url, q, url_scope_list)
                        increment_crawl_url_counter(crawl_url_counter, lock)  # 爬取数量+1
            else:
                break
            # 把两个字典，序列化到本地的文件中保存
            pickle_dump_dicts(content_page_dict, index_page_dict)
            print("-------------进程%s退出了！" % process_name)
        except queue.Empty:
            print("队列为空，任务结束。")
            break
        except Exception as e:
            # 使用 sys.stderr 打印异常消息
            sys.stderr.write(f"{process_name} 捕获异常: {str(e)}\n")

            continue

    #os._exit(0)

def main(crawl_urls,key_words):
    #设定需要爬取的关键字列表

    #设定开始爬取的种子url入口
    #crawl_urls = ["https://www.sohu.com", "https://www.sina.com.cn", "https://www.163.com"]
    #crawl_urls = ["https://www.sohu.com"]
    #从种子url中提取出域名，限定爬取url的所属域名范围，不在这个域名范围内的url不进行爬取
    url_scope = get_url_scope(crawl_urls)

    # 使用 Manager 创建共享变量：包括字典、列表、字符串和字符串类型，让不同的进程之间可以共享这个变量
    # 创建 Manager 实例
    manager = multiprocessing.Manager()
    content_page_dict = manager.dict()   # 创建共享字典,存储新闻正文页面的url
    index_page_dict = manager.dict()    # 创建共享字典,存储新闻列表页面的url
    url_scope_list = manager.list()  # 创建共享列表，存储域名范围的url
    #shared_value = manager.Value('c', "Initial")  # 创建共享字符串，'c' 表示字符类型
    crawl_url_counter = manager.Value('i', 0)  # 创建共享整数计数器,统计当前已经爬取的url总数
    get_content_url_counter = manager.Value('i', 0)  # 创建共享整数计数器，统计当前已经获取正文内容的url总数

    lock = multiprocessing.Lock()#声明了进程锁，在共享数字变量+1的时候进行加锁操作
    url_scope_list = url_scope#把域名范围赋值给共享列表变量

    try:
        #使用pickle从本地序列化的文件中读取两个dict的内容：dict1：存储爬取过正文页面的url，dict2:存储爬取过的列表页面url
        content_page_dict, index_page_dict = pickle_load_dicts()
    except Exception as e:
        print("提取文件中的存储url的2个字典变量时候出错，异常信息：%s" % e)

    # 用于收集每个进程任务计数的队列
    q = multiprocessing.Queue()
    get_seed_url(crawl_urls, q)#把种子url页面中的所有url提取出来，加入到队列中，作为起始的一批url进行爬取
    # 创建和启动多个线程
    processes = []
    for i in range(5):#生成5个进程对象，加入到列表中
        process = multiprocessing.Process(target=task, args=(lock,key_words,url_scope_list,content_page_dict,index_page_dict,crawl_url_counter,get_content_url_counter, q))
        processes.append(process)

    # 启动列表中，所有的进程对象
    for process in processes:
        process.start()

    # 等待所有进程全部执行完任务函数
    for process in processes:
        process.join()
        print(process,"------成功退出了！")

    # 显式关闭 Manager
    manager.shutdown()


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")  # Windows上使用'spawn'启动方式
    try:
        crawl_urls = ["https://www.sohu.com"]
        main(crawl_urls,key_words)
    except BrokenPipeError:#进程退出的时候可能触发了管道异常，捕获后不处理即可。
        pass

