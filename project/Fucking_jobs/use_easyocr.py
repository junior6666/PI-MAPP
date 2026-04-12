import easyocr

reader = easyocr.Reader(['ch_sim', 'en'])  # 首次会自动下载模型
result = reader.readtext('test.png')

for bbox, text, prob in result:
    print(f'{text}')