import json
import multiprocessing
import logging
from src import dd_gemini, tg_gemini

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == '__main__':
    try:
        # 读取配置文件
        with open("config/config.json", 'r') as file:
            config = json.load(file)
            logging.info("配置文件读取成功")

        if not config.get("GOOGLE_API_KEY"):
            logging.error("GOOGLE_API_KEY未配置")
            exit()

        tg = config.get("tg")
        if tg:
            logging.info("读取到TG机器人配置，获取配置中")
            if not tg.get("bot_token") or not tg.get("chat_id"):
                logging.error("TG机器人配置获取失败，请检查bot_token和chat_id")
            else:
                logging.info("正在启动TG-Gemini")
                process_tg = multiprocessing.Process(
                    target=tg_gemini.run,
                    args=(config.get("GOOGLE_API_KEY"), tg.get("bot_token"), tg.get("chat_id"))
                )
                process_tg.start()

        dd = config.get("dd")
        if dd:
            logging.info("读取到钉钉机器人配置，获取配置中")
            if not dd.get("client_id") or not dd.get("client_secret"):
                logging.error("钉钉机器人配置获取失败，请检查client_id和client_secret")
            else:
                logging.info("正在启动DD-Gemini")
                process_dd = multiprocessing.Process(
                    target=dd_gemini.run,
                    args=(config.get("GOOGLE_API_KEY"), dd.get("client_id"), dd.get("client_secret"))
                )
                process_dd.start()

        if not tg and not dd:
            logging.error("没有读取到任何机器人配置，程序退出")

    except FileNotFoundError:
        logging.error("找不到配置文件")
    except json.JSONDecodeError:
        logging.error("配置文件解析失败")
    except Exception as err:
        logging.error(str(err).replace('\n', ' '))
