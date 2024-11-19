from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

def extract_valid_links(html,base_url):
    # 解析页面
    soup = BeautifulSoup(html, 'html.parser')
    valid_links = []

    # 遍历所有 <a> 标签
    for link in soup.find_all('a', href=True):
        href = link['href']

        # 过滤掉无效链接
        if href.startswith(('javascript:', 'mailto:', '#')) or \
                href.endswith(('.ico', '.png', '.jpg', '.jpeg', '.gif', '.js', '.css')):
            # print("*****************", href)
            continue

        if href.startswith("//"):
            href = "http://"+href[2:]
        elif href.startswith("/"):
            href = base_url+href
        elif (not href.startswith("http://"))  and (not  href.startswith("https://")):
            href = base_url+href

        if href.strip():
            valid_links.append(href.strip())

    return valid_links

if __name__ =="__main__":
    options = Options()
    options.add_argument('headless')  # 使用无头模式,不用打开浏览器，从底层进行通讯
    options.add_argument('--log-level=3')  # 不打印驱动的日志
    # driver:一个chrome的浏览器对象
    driver = webdriver.Chrome(options=options, executable_path="e:\\chromedriver.exe")
    # driver = webdriver.Chrome( executable_path="e:\\chromedriver.exe")
    driver.get("https://www.sohu.com/")  # 浏览器对象访问某个网址
    html = driver.page_source  # 获取页面的源码
    soup = BeautifulSoup(html, 'html.parser')
    for url in extract_valid_links(html,"https://www.sohu.com/"):
        print("----",url)

