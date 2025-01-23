import json
import aiohttp
from tool.count import count_tokens
import google.generativeai as genai
import dingtalk_stream
from dingtalk_stream import AckMessage, ChatbotMessage
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
dd_message = {}
logotype = "DD "


def run(GOOGLE_API_KEY, client_id, client_secret):
    try:
        genai.configure(api_key=GOOGLE_API_KEY)

        # 修改model配置
        generation_config = {
            "temperature": 0.8,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 4096,
        }
        MAX_TOKENS_LIMIT = 32000

        model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp",
                                      generation_config=genai.GenerationConfig(**generation_config))

        logging.info(logotype + "启动DD-Gemini成功，开始接收消息")

        class CalcBotHandler(dingtalk_stream.ChatbotHandler):
            async def reply_text(self, text: str, incoming_message: ChatbotMessage):
                values = {
                    'msgtype': 'text',
                    'text': {
                        'content': text,
                    },
                    'at': {}
                }

                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.post(
                                incoming_message.session_webhook,
                                headers={
                                    'Content-Type': 'application/json',
                                    'Accept': '*/*',
                                },
                                data=json.dumps(values)
                        ) as response:
                            response.raise_for_status()
                            return await response.json()
                    except aiohttp.ClientError as e:
                        logging.error(logotype + 'reply text failed, error=%s', e)
                        return None

            async def process(self, callback: dingtalk_stream.CallbackMessage):
                incoming_message = dingtalk_stream.ChatbotMessage.from_dict(callback.data)
                global dd_message
                user_id = callback.data.get('senderStaffId')
                dd_message.setdefault(user_id, {'flag': False, 'chat': []})
                expression = incoming_message.text.content.strip()
                logging.info(f"{logotype}[{user_id}] 接收到消息：{expression}")

                if expression == "万物复苏":
                    await self.reply_text("万物复苏成功！", incoming_message)
                    dd_message[user_id]['flag'] = False
                    dd_message[user_id]['chat'] = []
                    logging.info(f"{logotype}[{user_id}] 执行重置操作")
                    logging.info(f"{logotype}执行重置操作[{user_id}]")
                    return AckMessage.STATUS_OK, 'OK'

                if dd_message[user_id]['flag']:
                    logging.info(f"{logotype}[{user_id}] 正在回答上一个问题，拒绝回答本次问题")
                    await self.reply_text("我还在忙着回答其他问题呢，你过会儿再来问吧！", incoming_message)
                    return AckMessage.STATUS_OK, 'OK'

                dd_message[user_id]['flag'] = True
                logging.info(f"{logotype}[{user_id}] 回答消息中，上锁，拒绝回答消息")

                try:
                    if dd_message[user_id]['chat']:
                        if dd_message[user_id]['chat'][-1]['role'] == 'user':
                            dd_message[user_id]['chat'].pop()
                    dd_message[user_id]['chat'].append({'role': 'user', 'parts': [expression]})
                    if count_tokens([{'role': 'user', 'parts': [expression]}]) > 4096:
                        logging.info(f"{logotype}[{user_id}] 提问字数太多，拒绝回答。解锁，开始接收消息")
                        await self.reply_text("你发送的字数太多啦！我都看不完啦，删除一点文字再来问吧！", incoming_message)
                        dd_message[user_id]['flag'] = False
                        return AckMessage.STATUS_OK, 'OK'
                    # 在调用 model.generate_content 前检查 token 数是否超过限制
                    while count_tokens(dd_message[user_id]['chat']) > MAX_TOKENS_LIMIT:
                        # 获取 chat 列表中的对象数量
                        chat_length = len(dd_message[user_id]['chat'])
                        # 计算要删除的对象的数量（前一半）
                        chat_remove = chat_length // 2
                        # 删除前一半对象
                        dd_message[user_id]['chat'] = dd_message[user_id]['chat'][chat_remove:]
                    response = model.generate_content(dd_message[user_id]['chat'])
                    if not response.parts:
                        dd_message[user_id]['flag'] = False
                        dd_message[user_id]['chat'].pop()
                        logging.info(f"{logotype}[{user_id}] 没有接收到Gemini发送回来的消息，解锁。开始接收消息")
                        await self.reply_text("此次回答被神秘的力量干扰，无法回答哦，请换个问题吧！", incoming_message)
                        return AckMessage.STATUS_OK, 'OK'
                    dd_message[user_id]['chat'].append({'role': 'model',
                                                        'parts': [response.text.replace('*', '')]})
                    max_chunk_size = 2000
                    for i in range(0, len(response.text.replace('*', '')), max_chunk_size):
                        chunk = response.text.replace('*', '')[i:i + max_chunk_size]
                        await self.reply_text(chunk, incoming_message)

                    logging.info(f"{logotype}[{user_id}] 回复用户消息：" + response.text)
                    logging.info(f"{logotype}[{user_id}] 解锁，开始接收消息")
                except Exception as e:
                    logging.error(logotype + str(e).replace('\n', ' '))
                    await self.reply_text("发生了异次元危机：" + str(
                        e) + '\n\n如果这个神秘咒语持续出现，可以回复[万物复苏]让我将所有的一切恢复到最开始的状态！',
                                          incoming_message)
                dd_message[user_id]['flag'] = False
                return AckMessage.STATUS_OK, 'OK'

        credential = dingtalk_stream.Credential(client_id, client_secret)
        client = dingtalk_stream.DingTalkStreamClient(credential)
        client.register_callback_handler(dingtalk_stream.ChatbotMessage.TOPIC, CalcBotHandler())
        client.start_forever()

    except Exception as err:
        logging.error(logotype + str(err).replace('\n', ' '))
