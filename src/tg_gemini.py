import asyncio
import logging
import time

import google.generativeai as genai
from telebot.async_telebot import AsyncTeleBot
from tool.count import count_tokens

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
tg_message = {}
logotype = "TG "


def run(GOOGLE_API_KEY, bot_token, chat_id):
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

    logging.info(logotype + "启动TG-Gemini成功，开始接收消息")

    @bot.message_handler(commands=['start'])
    async def send_welcome(message):
        print(message)
        await bot.send_message(message.chat.id, """\
    我是一个基于Gemini的聊天机器人。
    你可以向我发送消息以获得我的帮助哦！\
    """)

    @bot.message_handler(func=lambda message: message.chat.id in chat_id)
    async def echo_message(message):
        if message.text.startswith('/') and not (message.text.startswith('/g')) or message.text.startswith(
                '/g@') or not message.text.startswith('/') and not message.chat.type == "private":
            return

        if message.text.startswith('/g'):
            message.text = message.text[2:].strip()
        global tg_message

        user_id = message.from_user.id
        logging.info(f"{logotype}[{user_id}] 接收到消息：" + message.text)
        tg_message.setdefault(user_id, {'flag': False, 'chat': []})
        try:
            if message.text == "万物复苏":
                await bot.send_message(message.chat.id, "万物复苏成功！")
                tg_message[user_id]['flag'] = False
                tg_message[user_id]['chat'] = []
                logging.info(f"{logotype}[{user_id}] 执行重置操作")
                return

            if tg_message[user_id]['flag']:
                logging.info(f"{logotype}[{user_id}] 正在回答上一个问题，拒绝回答本次问题")
                await bot.send_message(message.chat.id, "我还在忙着回答其他问题呢，你过会儿再来问吧！")
                return
            tg_message[user_id]['flag'] = True
            logging.info(f"{logotype}[{user_id}] 回答消息中，上锁，拒绝回答消息")

            if tg_message[user_id]['chat']:
                if tg_message[user_id]['chat'][-1]['role'] == 'user':
                    tg_message[user_id]['chat'].pop()
            tg_message[user_id]['chat'].append({'role': 'user', 'parts': [message.text]})
            if count_tokens([{'role': 'user', 'parts': [message.text]}]) > 4096:
                logging.info(f"{logotype}[{user_id}] 提问字数太多，拒绝回答，解锁，开始接收消息")
                await bot.send_message(message.chat.id, "你发送的字数太多啦！我都看不完啦，删除一点文字再来问吧！")
                tg_message[user_id]['flag'] = False
                return
            # 在调用 model.generate_content 前检查 token 数是否超过限制
            while count_tokens(tg_message[user_id]['chat']) > MAX_TOKENS_LIMIT:
                # 获取 chat 列表中的对象数量
                chat_length = len(tg_message[user_id]['chat'])
                # 计算要删除的对象的数量（前一半）
                chat_remove = chat_length // 2
                # 删除前一半对象
                tg_message[user_id]['chat'] = tg_message[user_id]['chat'][chat_remove:]
            response = model.generate_content(tg_message[user_id]['chat'])
            if not response.parts:
                tg_message[user_id]['flag'] = False
                tg_message[user_id]['chat'].pop()
                logging.info(f"{logotype}[{user_id}] 没有接收到Gemini发送回来的消息，解锁，开始接收消息")
                await bot.send_message(message.chat.id, "此次回答被神秘的力量干扰，无法回答哦，请换个问题吧！")
                return
            tg_message[user_id]['chat'].append({'role': 'model',
                                                'parts': [response.text]})
            max_chunk_size = 2000
            for i in range(0, len(response.text), max_chunk_size):
                chunk = response.text[i:i + max_chunk_size]
                await bot.send_message(message.chat.id, chunk)

            logging.info(f"{logotype}[{user_id}] 回复用户消息：" + response.text)
            logging.info(f"{logotype}[{user_id}] 解锁，开始接收消息")

        except Exception as err:
            logging.error(logotype + str(err).replace('\n', ' '))
            await bot.send_message(message.chat.id, "发生了异次元危机：" + str(
                err) + '\n\n如果这个神秘咒语持续出现，可以回复[万物复苏]让我将所有的一切恢复到最原始的状态！')
        tg_message[user_id]['flag'] = False

    async def bot_run():
        while True:
            try:
                await bot.polling()
            except Exception as err:
                logging.error(logotype + str(err).replace('\n', ' '))
            time.sleep(10)

    asyncio.run(bot_run())
