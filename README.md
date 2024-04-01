# 项目运行说明

## 依赖安装

在运行项目之前，请确保已经安装以下依赖项：

```bash
pip install google.generativeai telebot dingtalk_stream
```

## 项目介绍

该项目是一个使用 Google 的 generativeai 库、telebot 库和 dingtalk_stream 库的机器人应用。它使用 Google 的生成模型进行自然语言处理，并与 Telegram 机器人以及钉钉机器人进行集成。

## 配置

在运行项目之前，请确保在config/config.json中配置了以下参数：

- `GOOGLE_API_KEY`: 你的 Google API 密钥
- `bot_token`: 你的 Telegram 机器人令牌
- `chat_id`: 你的 Telegram 机器人聊天ID
- `client_id`: 你的钉钉机器人 ID
- `client_secret`: 你的钉钉机器人密钥

配置机器人可以二选一，也可以都填写，但至少填写一个，如果不需要请删除无需配置的机器人配置项。
## 运行

在项目根目录下运行以下命令启动应用：

```bash
python app.py
```

## 注意事项

- 请提前申请并配置好 [Google API 密钥](https://ai.google.dev/pricing)。
- 在 Telegram 上创建一个新的机器人并[获取机器人令牌和聊天ID](https://blog.xiny.cc/archives/mTaUz0TW)。
- 在钉钉开放平台上创建一个新的机器人并[获取机器人 ID 和密钥](https://blog.xiny.cc/archives/tJNIk1Xa)。
- 钉钉群需要@机器人才能获得回复，TG机器人接收群消息需要在消息前加上/g，例：“/g 你是哪个公司研发的？”
