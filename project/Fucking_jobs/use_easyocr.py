import easyocr

reader = easyocr.Reader(['ch_sim', 'en'])  # 首次会自动下载模型
result = reader.readtext('H:\pycharm_project\github_projects\PI-MAPP\project\Fucking_jobs\screenshots\quick_20260413_114303_173.png')

for bbox, text, prob in result:
    print(f'{text}')