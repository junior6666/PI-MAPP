import json
import csv
# 导入自动化模块
from DrissionPage import ChromiumPage

f = open('data/data.csv', mode='w', encoding='utf-8', newline='')
csv_w = csv.DictWriter(f,fieldnames=['评论','昵称'])
csv_w.writeheader()
driver = ChromiumPage()
# 监听数据包
driver.listen.start('aweme/v1/web/comment/list/')
# 访问网站
driver.get('https://www.douyin.com/video/7353500880198536457')

for page in range(20):
    print(f'正在爬取第{page+1}页的内容')
    driver.scroll.to_bottom()
    resp = driver.listen.wait()

    data_str = resp.response.body
    comments = data_str['comments']

    for comment in comments:
        text = comment['text']
        nickname = comment['user']['nickname']
        dic = {
            '评论': text,
            '昵称': nickname
        }
        csv_w.writerow(dic)
        print(dic)



