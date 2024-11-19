import os
# 获得当前文件所在的目录
proj_path = os.path.dirname(os.path.dirname(__file__))

# ini文件的路径
ini_file_path = os.path.join(proj_path,"config","config.ini")

key_words = ["体育", "汽车", "教育", "股市", "中东", "金融", "娱乐", "技术", "基金", "半导体", "暴雨", "获刑",
                 "会议", "房地产", "航天", "电影","美国","中国","欧洲","音乐","火灾","联合国","互联网","旅游","文化","经济","历史",
                 "手机","乌克兰","战争","土地","少年","奖金","律师","楼市","报警","朝鲜","伊朗","以色列","挑衅"]

process_num = 3
per_process_crawl_max_page_count_count = 3
exclude_content_file_path = os.path.join(proj_path,"config","禁止爬取内容大全列表.txt")
exclude_urls_file_path = os.path.join(proj_path,"config","禁爬url列表.txt")
