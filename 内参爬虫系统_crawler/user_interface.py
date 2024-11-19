import sys
import time
import multiprocessing
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                             QTextEdit, QPushButton, QSizePolicy, QLabel)
from crawler import get_url_scope,pickle_load_dicts,get_seed_url,pickle_dump_dicts
from crawler import task,get_page_data,extract_valid_links,extract_link_to_queue,increment_crawl_url_counter,judge_page_content_if_write_to_db,judge_keyword_in_page,increment_get_content_url_counter
from config.proj_vars import process_num
from config.proj_vars import per_process_crawl_max_page_count_count
import os
import queue
from multiprocessing import current_process
from PyQt5.QtCore import QTimer
import traceback
import threading
from PyQt5.QtCore import QTimer, QThread, pyqtSignal,Qt
from PyQt5 import QtWidgets, QtCore, QtGui
import logging
from config.proj_vars import ini_file_path,exclude_content_file_path,exclude_urls_file_path
from util.file_util import read_file_lines


class Crawler(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

        self.process = None
        self.is_running = False
        # 创建一个定时器，每500毫秒检查一次输出队列
        #self.timer = QTimer(self)
        #self.timer.timeout.connect(self.check_status)
        # 创建队列
        self.mesage_queue = multiprocessing.Queue()
        # 设置定时器
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.check_queue)
        self.timer.start(100)  # 每100毫秒检查一次队列

    def initUI(self):
        self.setWindowTitle('多进程爬虫')
        self.setGeometry(100, 100, 1200, 1000)  # 初始窗口大小
        self.setMinimumSize(800, 600)  # 设置最小尺寸, 以便可调整

        layout = QVBoxLayout()
        # 增加字体大小
        font = QtGui.QFont()
        font.setPointSize(16)  # 设置字体大小为24（约为现有字体的3倍）

        self.url_label = QLabel("爬虫的种子url网址：")
        self.url_label.setFont(font)
        # 输入框 (使用 QTextEdit 允许多行输入)
        self.url_input = QTextEdit(self)
        self.url_input.setPlaceholderText('输入多个网址，使用逗号分隔，每行一个网址')
        self.url_input.setFixedHeight(500)  # 设置高度以足够显示20行
        self.url_input.setFont(font)
        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)

        #爬取内容的关键词
        self.keyword_label = QLabel("爬取内容的关键词：")
        self.keyword_label.setFont(font)

        # 输入框 (使用 QTextEdit 允许多行输入)
        self.key_word_input = QTextEdit(self)
        self.key_word_input.setPlaceholderText('输入多个网址，使用逗号分隔，每行一个网址')
        self.key_word_input.setFixedHeight(150)  # 设置高度以足够显示20行
        self.key_word_input.setFont(font)
        self.key_word_input.setText("体育,汽车,教育,股市,中东,金融,娱乐,技术,基金,半导体,暴雨,获刑,会议,房地产,航天,电影,美国,中国,欧洲,音乐,火灾,联合国,互联网,旅游,文化,经济,历史,手机,乌克兰,战争,土地,少年,奖金,律师,楼市,报警,朝鲜,伊朗,以色列,挑衅")

        layout.addWidget(self.keyword_label)
        layout.addWidget(self.key_word_input)


        # 设置按钮字体大小为现有文本框大小的5倍
        button_font = QtGui.QFont()
        button_font.setPointSize(20)  # 按钮字体大小为120

        # 启动/停止按钮
        self.start_stop_button = QPushButton('开始爬取', self)
        self.start_stop_button.setFont(button_font)
        self.start_stop_button.clicked.connect(self.toggle_crawling)
        layout.addWidget(self.start_stop_button)

        # 输出区域
        self.output_area = QTextEdit(self)
        self.output_area.setReadOnly(True)
        self.output_area.setFixedHeight(300)  # 设置输出区域高度
        self.output_area.setFont(font)
        layout.addWidget(self.output_area)

        # 设置布局
        self.setLayout(layout)

        # 设置输入框和输出区域宽度
        self.url_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.output_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.url_input.setText("https://www.163.com")


    def toggle_crawling(self):
        if not self.is_running:
            self.start_crawling()
        else:
            self.stop_crawling()

    def start_crawling(self):
        self.is_running = True
        self.start_stop_button.setText('停止爬取')
        self.output_area.clear()
        key_words = self.key_word_input.toPlainText().split(",")
        urls = [url.strip() for url in self.url_input.toPlainText().splitlines() if url.strip()]
        self.crawler_thread = CrawlerThread(urls,self.mesage_queue,key_words)
        self.crawler_thread.update_output_signal.connect(self.update_output)
        self.crawler_thread.finished_signal.connect(self.finish_crawling)
        self.crawler_thread.start()

    def stop_crawling(self):#点击按钮主动结束爬虫任务
        if self.crawler_thread and self.crawler_thread.isRunning():
            # Terminate the crawling thread
            self.crawler_thread.terminate()  # Terminate the thread
            self.crawler_thread.wait()  # Wait for the thread to finish
        self.is_running = False
        self.start_stop_button.setText('开始爬取')

    def finish_crawling(self):#爬虫都爬取完毕了，触发这个方法
        print("$$$$$$$$$$$$$$$$$$$$$$------所有的进程都退出了！",)
        self.is_running = False
        self.start_stop_button.setText('开始爬取')
        self.update_output("所有的爬虫都完成了爬取任务！")
        time.sleep(10)

    def update_output(self, message):
        self.output_area.append(message)
        self.output_area.moveCursor(Qt.Descending)  # Move the cursor to the end

    def check_queue(self):
        """检查队列并更新QTextEdit"""
        while not self.mesage_queue.empty():
            message = self.mesage_queue.get()
            self.output_area.append(message)  # 将消息添加到文本框
            if "所有的进程都完成了爬取任务，退出！" in message:
                self.stop_crawling()

class CrawlerThread(QThread):
    update_output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, urls,mesage_queue,key_words):
        super().__init__()
        self.urls = urls
        self.output_queue = multiprocessing.Queue()
        self.processes = []
        self.manager = multiprocessing.Manager()
        self.lock = multiprocessing.Lock()
        self.mesage_queue = mesage_queue
        self.key_words = key_words
        self.exclude_url_list = read_file_lines(exclude_urls_file_path)
        self.exclude_content_list = read_file_lines(exclude_content_file_path)

    def run(self):
        content_page_dict = self.manager.dict()  # 创建共享字典,存储新闻正文页面的url
        index_page_dict = self.manager.dict()  # 创建共享字典,存储新闻列表页面的url
        url_scope_list = self.manager.list()  # 创建共享列表，存储域名范围的url
        exclude_url_list = self.manager.list()
        exclude_url_list.extend(self.exclude_url_list)
        exclude_content_list=self.manager.list()
        exclude_content_list.extend(self.exclude_content_list)
        # shared_value = manager.Value('c', "Initial")  # 创建共享字符串，'c' 表示字符类型
        crawl_url_counter = self.manager.Value('i', 0)  # 创建共享整数计数器,统计当前已经爬取的url总数
        get_content_url_counter = self.manager.Value('i', 0)  # 创建共享整数计数器，统计当前已经获取正文内容的url总数
        crawl_page_max_count = self.manager.Value('i', process_num*per_process_crawl_max_page_count_count)#爬虫任务最多爬取文章的总量
        cur_crawl_page_count =self.manager.Value('i', 0) #当前爬取文章的总量
        url_scope = get_url_scope(self.urls)
        url_scope_list = url_scope
        try:
            # 使用pickle从本地序列化的文件中读取两个dict的内容：dict1：存储爬取过正文页面的url，dict2:存储爬取过的列表页面url
            content_page_dict, index_page_dict = pickle_load_dicts()
        except Exception as e:
            print("提取文件中的存储url的2个字典变量时候出错，异常信息：%s" % e)

        try:
            q = multiprocessing.Queue()
            get_seed_url(self.urls, q)
            for _ in range(process_num):
                process = multiprocessing.Process(target=task, args=(self.mesage_queue,
                                                                     self.lock, self.key_words, url_scope_list,
                                                                     content_page_dict,
                                                                     index_page_dict, crawl_url_counter,
                                                                     get_content_url_counter, q,
                                                                     crawl_page_max_count, cur_crawl_page_count,
                                                                     per_process_crawl_max_page_count_count,exclude_url_list,
                                                                     exclude_content_list
                                                                     ))
                self.processes.append(process)

            for process in self.processes:
                process.start()

                # Wait for processes to complete
            for process in self.processes:
                process.join()

                # Emit finished signal
            self.finished_signal.emit()
        except Exception as e:
            print(f"在 CrawlerThread 中发生错误: {str(e)}")

def task(mesage_queue,lock, key_words, url_scope_list, content_page_dict, index_page_dict, crawl_url_counter,
         get_content_url_counter, q, crawl_page_max_count,cur_crawl_page_count,crawl_page_num,exclude_url_list,exclude_content_list):
    try:
        times = 0
        process_name = current_process().name
        while times < crawl_page_num:
            try:
                if q.qsize() > 0:
                    url = q.get(timeout=10).strip()  # 设置超时，防止永久阻塞
                    print("进程 %s :当前爬取的Url:%s" % (process_name, url))
                    # 发送信号到主线程

                    mesage_queue.put("进程 %s :当前爬取的Url:%s" % (process_name, url))
                    # output_area_list[0].append(f"当前爬取的Url: {url}")
                    # 情况1：url没有出现在2个字典中，说明从来没有被爬取过
                    if url not in content_page_dict and url not in index_page_dict:
                        data = get_page_data(url)
                        extract_link_to_queue(url, q, url_scope_list)
                        increment_crawl_url_counter(crawl_url_counter, lock)  # 爬取过的url总数+1
                        content_page_dict[url] = round(time.time(), 0)  # 爬取过的url加入到字典中，设定好时间戳作为value
                        # 如果爬取的正文或者标题包含了关键字，则写入到数据库
                        if judge_page_content_if_write_to_db(data, key_words,exclude_url_list,exclude_content_list):
                            times += 1  # 爬取的数量加1
                            increment_get_content_url_counter(get_content_url_counter, lock)  # 成功爬取到内容的url总数+1
                            cur_crawl_page_count.value += 1

                    # 情况2：url在conent_page_dict被当做正文页面爬取过
                    elif url in content_page_dict:
                        if time.time() - content_page_dict[url] < 3600 * 24:  # 小于1天就不爬了
                            continue
                        else:
                            data = get_page_data(url)
                            extract_link_to_queue(url, q, url_scope_list)
                            increment_crawl_url_counter(crawl_url_counter, lock)  # 爬取数量+1

                            if judge_page_content_if_write_to_db(data, key_words,exclude_url_list,exclude_content_list):
                                times += 1
                                cur_crawl_page_count.value += 1
                                increment_get_content_url_counter(get_content_url_counter, lock)  # 成功爬取到内容的url总数+1

                    # 情况3：url在index_page_dict被当做列表页面爬取过
                    elif url in index_page_dict:
                        if time.time() - index_page_dict[url] < 3600:  # 小于1小时就不爬了
                            continue
                        else:
                            index_page_dict[url] = round(time.time(), 0)
                            extract_link_to_queue(url, q, url_scope_list)
                            increment_crawl_url_counter(crawl_url_counter, lock)  # 爬取数量+1
                    print("&&&&&&&&&&&&&&", process_name, times)
                    mesage_queue.put("进程 %s:成功抓取内容的数量 %s" % (process_name, times))
                else:
                    break
                # 把两个字典，序列化到本地的文件中保存
                pickle_dump_dicts(content_page_dict, index_page_dict)

            except queue.Empty:
                print("队列为空，任务结束。")
                break
            except Exception as e:
                # 使用 sys.stderr 打印异常消息
                sys.stderr.write(f"{process_name} 捕获异常: {str(e)}\n")
                mesage_queue.put(f"{process_name} 捕获异常: {str(e)}\n")
                traceback.print_exc()
                continue

        print("-------------进程%s退出了！" % process_name)
        mesage_queue.put("-------------进程%s退出了！" % process_name)
        # os._exit(0)
        if cur_crawl_page_count.value >= crawl_page_max_count.value:
            print("###################已经达到了最大抓取的文章数量！")
            mesage_queue.put("所有的进程都完成了爬取任务，退出！")
    except Exception as e:
        print("任务函数发生了异常，信息如下：" ,e)


if __name__ == '__main__':
    multiprocessing.set_start_method("spawn")  # Windows上使用'spawn'启动方式
    #multiprocessing.log_to_stderr()
    #logger = multiprocessing.get_logger()
    # 设置输出日志的级别
    #logger.setLevel(logging.INFO)
    app = QApplication(sys.argv)
    ex = Crawler()
    ex.show()
    sys.exit(app.exec_())
    # 设置日志输出到控制台
