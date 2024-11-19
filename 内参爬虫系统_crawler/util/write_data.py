from util.db_util import  MySQLDatabase
from util.page_parser import get_page_data



def write_data_to_db(data,exclude_url_list=[],exclude_content_list=[]):

    with MySQLDatabase() as db:
        exists1 = db.content_exists(data["news_content"])
        exists2 = db.title_exists(data["news_title"])
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$",exclude_url_list,exclude_content_list)
        for url in exclude_url_list:
            print("-------------------------", url, data["suburl"], url in data["suburl"] )
            if url in data["suburl"] :
                return
        for content in exclude_content_list:
            print("-------------------------",content , data["news_title"],content in data["news_title"])
            if content in data["news_title"] :
                return
        for content in  exclude_content_list:
            print("-------------------------",content, data["news_content"], content in data["news_content"])
            if content in data["news_content"]:
                return
        if exists1 or exists2:
            return
        else:
            db.insert("crawler_crawlerdata", data)



if __name__ =="__main__":
    # data={"url":"www.sohu.com",
    #       "suburl":"https://www.sohu.com/a/821021739_120578424?scm=10001.247_14-200000.0.10006.a3_504043-a2_3X2523&spm=smpc.channel_217.block3_93_gPMjDz_1_fd.4.1730164289905Lsz16yJ_397",
    #       "keyword":"","news_title":"云南省有了家书博物馆",
    #       "news_content":"近日，云南省首个家书博物馆落地昆明市呈贡区七彩云南第壹城。走进家书博物馆，首先映入眼帘的是冰心写给呈贡人民的一封信，随后，红色家书、将军之嘱、求学之路、金兰之谊等主题展区依次排开。一张张泛黄的纸片，传递着多样的情感与温度，静静地诉说着过往的故事，让观者感受到跨越时空的共鸣。本报记者 高吴双 摄返回搜狐，查看更多责任编辑：",
    #       "news_release_time":"2024-10-28 08:44",
    #       "crawler_date":"2024-10-28 08:44"}
    data = get_page_data("https://baijiahao.baidu.com/s?id=1813844243039980555&wfr=spider&for=pc")
    write_data_to_db(data)
