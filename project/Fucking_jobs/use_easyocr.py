import easyocr

reader = easyocr.Reader(['ch_sim', 'en'])  # 首次会自动下载模型
result = reader.readtext('H:\pycharm_project\github_projects\PI-MAPP\project\Fucking_jobs\screenshots\ScreenShot_2026-04-13_140714_532.png')

for bbox, text, prob in result:
    print(f'{text}')