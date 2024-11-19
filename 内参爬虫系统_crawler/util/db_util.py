import pymysql
from config.proj_vars import ini_file_path
from util.ini_util import IniReader
class MySQLDatabase:
    def __init__(self):
        ini_parser = IniReader(ini_file_path)
        host = ini_parser.get_value("db", "host")
        username = ini_parser.get_value("db", "username")
        password = ini_parser.get_value("db", "password")
        port = ini_parser.get_int("db", "port")
        database = ini_parser.get_value("db", "database")
        self.host = host
        self.user = username
        self.password = password
        self.database = database
        self.port = port
        self.connection = None

    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                cursorclass=pymysql.cursors.DictCursor
            )
        except pymysql.MySQLError as e:
            print(f"Error connecting to MySQL Database: {e}")
            self.connection = None

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_query(self, query, params=None):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
                return cursor.fetchall()
        except pymysql.MySQLError as e:
            print(f"Query execution error: {e}")
            self.connection.rollback()
            return None

    def execute_update(self, query, params=None):#进行增删改查的通用方法
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
                return cursor.rowcount  # Returns the number of affected rows
        except pymysql.MySQLError as e:
            print(f"Update execution error: {e}")
            self.connection.rollback()
            return None


    def insert(self, table, data):
        keys = ', '.join(data.keys())
        values = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table} ({keys}) VALUES ({values})"
        return self.execute_update(query, tuple(data.values()))

    def insert_many(self, table, data_list):
        if not data_list:
            return 0  # 如果数据列表为空，直接返回
        keys = ', '.join(data_list[0].keys())
        values_placeholder = ', '.join(['%s'] * len(data_list[0]))
        query = f"INSERT INTO {table} ({keys}) VALUES ({values_placeholder})"
        try:
            with self.connection.cursor() as cursor:
                cursor.executemany(query, [tuple(data.values()) for data in data_list])
                self.connection.commit()
                return cursor.rowcount  # 返回插入的行数
        except pymysql.MySQLError as e:
            print(f"Batch insert error: {e}")
            self.connection.rollback()
            return None

    def update(self, table, data, condition):
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        return self.execute_update(query, tuple(data.values()))

    def delete(self, table, condition):
        query = f"DELETE FROM {table} WHERE {condition}"
        return self.execute_update(query)

    def select(self, table, columns='*', condition=None):
        query = f"SELECT {columns} FROM {table}"
        if condition:
            query += f" WHERE {condition}"
        return self.execute_query(query)

    # 新增内容检查方法
    def content_exists(self, content):
        query = "SELECT COUNT(*) as count FROM crawler_data WHERE news_content = %s"
        result = self.execute_query(query, (content,))
        if result and result[0]['count'] > 0:
            return True
        return False

    # 新增标题检查方法
    def title_exists(self, title):
        query = "SELECT COUNT(*) as count FROM crawler_data WHERE news_title = %s"
        result = self.execute_query(query, (title,))
        if result and result[0]['count'] > 0:
            return True
        return False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

if __name__=="__main__":

    # 使用类
    with MySQLDatabase() as db:
        # 插入数据
        data = {"name": "Alice", "age": 25}
        db.insert("users", data)

        # 查询数据
        users = db.select("users", columns="name, age")
        print("Users:", users)

        # 更新数据
        db.update("users", {"age": 26}, "name = 'Alice'")

        # 查询数据
        users = db.select("users", columns="name, age")
        print("Users:", users)

        # 删除数据
        db.delete("users", "name = 'Alice'")

        # 查询数据
        users = db.select("users", columns="name, age")
        print("Users:", users)

    # 插入多条数据
        data_list = [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30},
            {"name": "Charlie", "age": 28}
        ]
        rows_inserted = db.insert_many("users", data_list)
        print(f"Inserted {rows_inserted} rows.")

        # 查询数据
        users = db.select("users", columns="name, age")
        print("Users:", users)

        # 插入新用户
        insert_query = "INSERT INTO users (name, age, email) VALUES (%s, %s, %s)"
        affected_rows = db.execute_update(insert_query, ("Charlie", 28, "charlie@example.com"))
        print(f"Inserted {affected_rows} row(s).")

        # 更新用户年龄
        update_query = "UPDATE users SET age = %s WHERE name = %s"
        affected_rows = db.execute_update(update_query, (29, "Charlie"))
        print(f"Updated {affected_rows} row(s).")

        # 删除用户
        delete_query = "DELETE FROM users WHERE name = %s"
        affected_rows = db.execute_update(delete_query, ("Charlie",))
        print(f"Deleted {affected_rows} row(s).")

        # 示例内容
        content_to_check = """热门：大众丰田奔驰本田宝马奥迪
A奥迪阿斯顿马丁阿尔法罗密欧ALPINA爱驰安凯客车
B本田奔驰宝马别克比亚迪保时捷宝骏标致宾利北京越野BEIJING汽车北汽制造北汽新能源宝沃北汽幻速布加迪BRABUS巴博斯北汽威旺比速北汽道达奔腾
C长安长安欧尚长城长安凯程昌河长安新能源成功汽车
D大众东风风行东风启辰东风风神东风风光东南DS道奇东风东风郑州日产东风小康大乘汽车大运东风风度电咖汽车
F丰田福特法拉利福田菲亚特飞驰福迪福汽启腾枫叶汽车法乐第未来
G广汽传祺广汽新能源观致GMC广汽广汽吉奥国机智骏广汽中兴
H红旗哈弗海马黄海汉腾华泰哈飞汉龙汽车华颂合众新能源海格红星汽车华泰新能源汇众合创恒天华凯华骐
J吉利Jeep捷豹捷达江淮捷途金杯江铃金旅九龙江铃集团新能源几何汽车江铃集团轻汽君马汽车金龙汽车
K凯迪拉克克莱斯勒开瑞凯翼科尼赛克康迪卡威KTM开沃汽车
L雷克萨斯林肯路虎领克铃木劳斯莱斯兰博基尼雷诺猎豹理想汽车陆风路特斯力帆零跑汽车雷丁理念LITE陆地方舟领途汽车凌宝汽车领志
M马自达玛莎拉蒂MINIMG迈凯伦摩根迈迈
N纳智捷南京金龙NEVS
O讴歌欧拉
PPolestar帕加尼
Q奇瑞起亚乔治巴顿前途
R日产荣威如虎瑞驰新能源
S斯柯达三菱上汽大通MAXUS斯巴鲁smart双龙斯威赛麟SHELBY思铭SERES赛力斯SRM鑫源上喆陕西通家思皓
T特斯拉腾势天际天美汽车
W沃尔沃五菱WEY蔚来汽车五十铃威马汽车潍柴汽车威兹曼威麟
X现代雪佛兰雪铁龙新宝骏小鹏汽车星途新凯新特汽车
Y英菲尼迪一汽依维柯野马汽车英致宇通客车云雀汽车云度银隆新能源御捷新能源永源一汽凌河裕路
Z众泰中华中欧中兴知豆中誉之诺"""

        # 查询内容是否存在
        exists = db.content_exists(content_to_check)
        if exists:
            print("The content already exists in the database.")
        else:
            print("The content does not exist in the database.")