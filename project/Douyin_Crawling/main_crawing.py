import csv
import json
import re

# 导入自动化模块
from DrissionPage import ChromiumPage

def parse_chunked_data(data_str,csv_w):
    lines = data_str.strip().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # 跳过空行
        if not line:
            i += 1
            continue
        # 匹配十六进制数字（块大小）
        if re.fullmatch(r'[0-9a-fA-F]+', line):
            i += 1  # 下一行是数据
            if i < len(lines):
                json_line = lines[i].strip()
                try:
                    data = json.loads(json_line)
                    for item in data.get("data", []):
                        aweme_info = item.get("aweme_info", {})
                        desc = aweme_info.get("desc", "")
                        author = aweme_info.get("author", {})
                        nickname = author.get('nickname','无')
                        signature = author.get('signature','无')
                        dic = {
                            '文案': desc,
                            '作者': nickname,
                            '签名': signature
                        }
                        print(dic)
                        csv_w.writerow(dic)

                except json.JSONDecodeError as e:
                    print(f"JSON 解析失败: {e}")
            i += 1

def get_data(raw_json: dict) -> dict:
    # raw_json 就是你上面贴的那种结构
    ai = raw_json['data'][0]['aweme_info']   # 如果有多条再循环
    return {
        '文案': ai['desc'],
        '作者': ai['author']['nickname'],
        '签名': '无'
    }

# 打开 CSV 文件
f = open('data/data_wenan.csv', mode='w', encoding='utf-8', newline='')
csv_w = csv.DictWriter(f, fieldnames=['文案', '作者', '签名'])
csv_w.writeheader()

# 初始化浏览器
driver = ChromiumPage()

# 监听数据包
driver.listen.start('aweme/v1/web/general/search/stream/')

# 访问网站
url = "https://www.douyin.com/jingxuan/search/%E8%87%AA%E5%BE%8B"
driver.get(url)

# 爬取多页内容
for page in range(10):
    print(f'正在爬取第{page + 1}页的内容')

    try:
        # 等待监听到数据包
        resp = driver.listen.wait()
        data_str = resp.response.body
        # print(data_str)
        if page!=0:
            print(get_data(data_str))
        else:
            parse_chunked_data(data_str=data_str,csv_w=csv_w)
        driver.scroll.to_bottom()
        driver.listen.start('aweme/v1/web/general/search/')
    except Exception as e:
        print(f"监听数据包时出错: {e}")

# 关闭文件
f.close()

