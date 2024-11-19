import os.path
from config.proj_vars import exclude_urls_file_path,exclude_content_file_path

def read_file_lines(file_path):
    if not os.path.exists(file_path):
        print("读取的文件路径 %s 不存在！" %file_path)
        return []
    else:
        try:
            with open(file_path,"r",encoding="utf-8") as fp:
                lines = fp.readlines()
                return [line.strip() for line in lines]
        except:
            try:
                with open(file_path, "r", encoding="gbk") as fp:
                    lines = fp.readlines()
                    return [line.strip() for line in lines]
            except Exception as e:
                print("读取的文件路径 %s 出现异常，异常原因：%s" %(file_path,e))
                return []

if __name__=="__main__":
    print(read_file_lines(exclude_urls_file_path))
    print(read_file_lines(exclude_content_file_path))

