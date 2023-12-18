import json

import google.generativeai as genai
from count import count_tokens

import aiohttp
import dingtalk_stream
from dingtalk_stream import AckMessage, ChatbotMessage

with open("config.json", 'r') as file:
    config = json.load(file)
client_id = config["dd_config"]["client_id"]
client_secret = config["dd_config"]["client_secret"]
GOOGLE_API_KEY = config.get("GOOGLE_API_KEY")

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

# 变量用于跟踪上一个请求是否已经返回
last_response_returned = True
all_chat = {}


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
                self.logger.error('reply text failed, error=%s', e)
                return None

    async def process(self, callback: dingtalk_stream.CallbackMessage):
        incoming_message = dingtalk_stream.ChatbotMessage.from_dict(callback.data)
        mes_id = callback.data.get('senderStaffId')
        print(mes_id)
        global all_chat
        if mes_id not in all_chat:
            all_chat[mes_id] = []
        expression = incoming_message.text.content.strip()

        global last_response_returned

        if expression == "万物复苏":
            await self.reply_text("万物复苏成功！", incoming_message)
            last_response_returned = True
            all_chat[mes_id] = []
            return AckMessage.STATUS_OK, 'OK'

        if not last_response_returned:
            await self.reply_text("我还在忙着回答其他问题呢，你过会儿再来问吧！", incoming_message)
            return AckMessage.STATUS_OK, 'OK'

        last_response_returned = False
        try:
            if all_chat[mes_id]:
                if all_chat[mes_id][-1]['role'] == 'user':
                    all_chat[mes_id].pop()
            all_chat[mes_id].append({'role': 'user', 'parts': [expression]})
            if count_tokens([{'role': 'user', 'parts': [expression]}]) > 4096:
                await self.reply_text("你发送的字数太多啦！我都看不完啦，删除一点文字再来问吧！", incoming_message)
                last_response_returned = True
                return AckMessage.STATUS_OK, 'OK'
            # 在调用 model.generate_content 前检查 token 数是否超过限制
            while count_tokens(all_chat[mes_id]) > MAX_TOKENS_LIMIT:
                # 获取 chat 列表中的对象数量
                chat_length = len(all_chat[mes_id])
                # 计算要删除的对象的数量（前一半）
                chat_remove = chat_length // 2
                # 删除前一半对象
                all_chat[mes_id] = all_chat[mes_id][chat_remove:]
            response = model.generate_content(all_chat[mes_id])
            if not response.parts:
                last_response_returned = True
                all_chat[mes_id].pop()
                await self.reply_text("这个问题暂时不能回答你哦，请换个问题吧！", incoming_message)
                return AckMessage.STATUS_OK, 'OK'
            all_chat[mes_id].append({'role': 'model',
                                     'parts': [response.text]})
            await self.reply_text(response.text, incoming_message)
        except Exception as err:
            await self.reply_text("发生了异次元危机：" + str(
                err) + '\n\n如果这个神秘咒语持续出现，可以回复[万物复苏]让我将所有的一切恢复到最开始的状态！',
                                  incoming_message)
        last_response_returned = True
        return AckMessage.STATUS_OK, 'OK'


def main():
    try:
        credential = dingtalk_stream.Credential(client_id, client_secret)
        client = dingtalk_stream.DingTalkStreamClient(credential)
        client.register_callback_handler(dingtalk_stream.ChatbotMessage.TOPIC, CalcBotHandler())
        client.start_forever()
    except Exception as err:
        print(err)
