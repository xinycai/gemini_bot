import asyncio
import json
import multiprocessing

import dd_gemini
import tg_gemini


def start_tg_gemini():
    asyncio.run(tg_gemini.main())


if __name__ == '__main__':
    # 读取配置文件
    with open("config.json", 'r') as file:
        config = json.load(file)

    if not config.get("GOOGLE_API_KEY"):
        print("错误：GOOGLE_API_KEY未配置或为空。")
        exit()

    if "tg_config" in config and config["tg_config"]:
        process_tg = multiprocessing.Process(target=start_tg_gemini)
        process_tg.start()
        print("启动TG-Gemini成功")

    if "dd_config" in config and config["dd_config"]:
        process_dd = multiprocessing.Process(target=dd_gemini.main)
        process_dd.start()
        print("启动DD-Gemini成功")

    if "tg_config" not in config and "dd_config" not in config:
        print("错误：没有tg_config或dd_config的配置。")
        exit()
