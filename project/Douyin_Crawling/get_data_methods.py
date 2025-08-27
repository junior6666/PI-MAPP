import json
import re
import time

from DrissionPage import ChromiumPage

"""
获取用户主页视频的抖音数据 该函数得配合用户手动滚动页面 
                '文案'
                '作者'
                '点赞数'
                '评论数'
                '播放数'
                '收藏数'
                '分享数'
                '推荐数'
                '发布时间'
"""
def get_data_from_homepage(
        listen_url = 'aweme/v1/web/aweme/post/',
        pages = 2,
        url='https://www.douyin.com/user/MS4wLjABAAAApX522hgyNjhiAtiOGTZpWWDC3SQtdJvjWLX6pg00g4UyNnS-Zp9ISM190WvyYacK?from_tab_name=main&vid=7413737675921837350'
):
    driver = ChromiumPage()
    # 监听数据包
    driver.listen.start(listen_url)
    # 访问网站
    driver.get(url)
    for i in range(pages):
        print(f'正在爬取第{i + 1}页的内容')
        resp = driver.listen.wait()
        data_str = resp.response.body
        for aweme in data_str["aweme_list"]:

            dic = {
                '文案':aweme["desc"],
                '作者':aweme["author"]["nickname"],
                '点赞数':aweme["statistics"]["digg_count"],
                '评论数':aweme["statistics"]["comment_count"],
                '播放数':aweme["statistics"]["play_count"],
                '收藏数':aweme["statistics"]["collect_count"],
                '分享数':aweme["statistics"]["share_count"],
                '推荐数':aweme["statistics"]["recommend_count"],
                '发布时间': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(aweme["create_time"])),

            }
            print(dic)
            # 滚动到底部
        driver.scroll.to_bottom()

def deal_first_data_form_search(data_str):
    lines = data_str.strip().splitlines()
    i = 0
    dic_list = []
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
                    dic_list.append(dic)
            i += 1
    return dic_list


def deal_not_first_data_form_search(data):
    dic_list = []
    for item in data.get("data", []):
        aweme_info = item.get("aweme_info", {})
        desc = aweme_info.get("desc", "").strip()
        author = aweme_info.get("author", {})
        nickname = author.get('nickname', '无').strip()
        signature = author.get('signature', '无').strip()
        item_data = {
            '文案': desc,
            '作者': nickname,
            '签名': signature
        }
        dic_list.append(item_data)
    return dic_list
def get_data_from_search(
        first_listen_url = 'aweme/v1/web/general/search/stream/',
        not_first_listen_url = 'aweme/v1/web/general/search/single/',
        pages = 2,
        theme = '街拍'
):
    # 初始化浏览器
    driver = ChromiumPage()
    # 监听数据包
    driver.listen.start(first_listen_url)
    # 访问网站
    url = f"https://www.douyin.com/jingxuan/search/{theme}"
    driver.get(url)
    for i in range(pages):
        print(f'正在爬取第{i + 1}页的内容')
        resp = driver.listen.wait()
        data_str = resp.response.body
        if i == 0:
            dict_list= deal_first_data_form_search(data_str)
        else:
            dict_list = deal_not_first_data_form_search(data_str)
        for dic in dict_list:
            print(dic)
        driver.scroll.to_bottom()
        driver.listen.start(not_first_listen_url)

if __name__ == '__main__':
    get_data_from_homepage(pages=3)
    # get_data_from_search(pages=3,theme='街拍')
