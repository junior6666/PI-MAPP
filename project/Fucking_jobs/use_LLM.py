import requests

url = "https://api.longcat.chat/openai/v1/chat/completions"
headers = {
    "Authorization": "Bearer ak_2Fw1hL0xA8H33yj1wn4pW8ag0w84y",
    "Content-Type": "application/json"
}

data = {
    "model": "LongCat-Flash-Chat",# 备用:LongCat-Flash-Lite
    "messages": [
        {"role": "user", "content": "你好，请介绍一下自己"}
    ],
    "max_tokens": 1000,
    "temperature": 0.7
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
# 输出 {'id': '2c29ca8d5ee244b6ac7aa1f4399ef79d', 'object': 'chat.completion', 'created': 1775984296, 'model': 'longcat-flash-chatai-api', 'usage': {'completion_tokens': 180, 'prompt_tokens': 16, 'total_tokens': 196, 'cache_write_tokens': 0, 'cache_read_tokens': 0, 'input_tokens': 0, 'output_tokens': 0, 'cached_tokens': 0}, 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': '你好！我是美团研发的大模型 LongCat，也是一位 AI 助手。\n\n我存在的目的是帮助你解决问题和满足你的需求。无论是需要信息查询、创意建议、文本处理、数据分析，还是日常闲聊，我都可以为你提供支持。\n\n我的优势在于：\n\n- 广泛的知识储备： 我在训练过程中学习了大量的文本数据，因此我可以提供涵盖多个领域的信息和知识。\n- 强大的文本生成能力： 我可以生成流畅、自然的文本，包括文章、故事、诗歌、代码、邮件、翻译等。\n- 多轮对话能力： 我可以与你进行连贯的多轮对话，理解上下文，并根据你的反馈调整我的回应。\n- 遵循指令： 我会尽力理解并遵循你的指令，提供你所需要的帮助。\n\n你可以把我当作一个随时待命的智能伙伴，有任何问题或需要，都可以随时告诉我！ 😊'}, 'finish_reason': 'stop', 'matched_stop': 2, 'logprobs': None}]}

