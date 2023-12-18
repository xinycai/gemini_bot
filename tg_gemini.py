import json

import google.generativeai as genai
from telebot.async_telebot import AsyncTeleBot

from count import count_tokens

with open("config.json", 'r') as file:
    config = json.load(file)
bot_token = config["tg_config"]["bot_token"]
chat_id = int(config["tg_config"]["chat_id"])
GOOGLE_API_KEY = config.get("GOOGLE_API_KEY")

bot = AsyncTeleBot(bot_token)
genai.configure(api_key=GOOGLE_API_KEY)
# 修改model配置
generation_config = {
    "temperature": 0.8,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 4096,
}
MAX_TOKENS_LIMIT = 32000

model = genai.GenerativeModel(model_name="gemini-pro",
                              generation_config=genai.GenerationConfig(**generation_config))


@bot.message_handler(commands=['start'])
async def send_welcome(message):
    await bot.send_message(message.chat.id, """\
我是一个基于Gemini的聊天机器人。
你可以向我发送消息以获得我的帮助哦！\
""")


# 变量用于跟踪上一个请求是否已经返回
last_response_returned = True
chat = []


@bot.message_handler(func=lambda message: message.chat.id == chat_id)
async def echo_message(message):
    global last_response_returned
    global chat
    if message.text == "万物复苏":
        await bot.send_message(message.chat.id, "万物复苏成功！")
        last_response_returned = True
        chat = []
        return
    if not last_response_returned:
        await bot.send_message(message.chat.id, "我还在忙着回答其他问题呢，你过会儿再来问吧！")
        return
    last_response_returned = False
    try:
        if chat:
            if chat[-1]['role'] == 'user':
                chat.pop()
        chat.append({'role': 'user', 'parts': [message.text]})
        if count_tokens([{'role': 'user', 'parts': [message.text]}]) > 4096:
            await bot.send_message(message.chat.id, "你发送的字数太多啦！我都看不完啦，删除一点文字再来问吧！")
            return
        # 在调用 model.generate_content 前检查 token 数是否超过限制
        while count_tokens(chat) > MAX_TOKENS_LIMIT:
            # 获取 chat 列表中的对象数量
            chat_length = len(chat)
            # 计算要删除的对象的数量（前一半）
            chat_remove = chat_length // 2
            # 删除前一半对象
            chat = chat[chat_remove:]
        response = model.generate_content(chat)
        if not response.parts:
            last_response_returned = True
            chat.pop()
            await bot.send_message(message.chat.id, "这个问题暂时不能回答你哦，请换个问题吧！")
            return
        chat.append({'role': 'model',
                     'parts': [response.text]})
        await bot.send_message(message.chat.id, response.text)
    except Exception as err:
        await bot.send_message(message.chat.id, "发生了异次元危机：" + str(
            err) + '\n\n如果这个神秘咒语持续出现，可以回复[万物复苏]让我将所有的一切恢复到最开始的状态！')
    last_response_returned = True


async def main():
    # 启动机器人
    await bot.polling()
