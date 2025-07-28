# DeepSeek Web Client

## 项目简介

DeepSeek Web Client 是一个基于 Flask 的 Web 应用程序，用于与 DeepSeek AI 模型进行交互。该项目提供了一个简单的用户界面，允许用户通过浏览器与 AI 进行对话。

## 功能特性

- 简洁的 Web 界面与 AI 交互
- 对话历史记录功能
- 用户配置文件管理
- 响应式设计，适配不同设备

## 安装指南

### 前提条件

- Python 3.7 或更高版本
- pip 包管理工具

### 安装步骤

1. 克隆仓库：
   ```bash
   git clone https://github.com/JiexuantroNic/deepseek_web_client.git
   cd deepseek_web_client
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 配置环境变量：
   - 复制 `.env.example` 为 `.env`
   - 根据需求修改 `.env` 文件中的配置

## 运行项目

```bash
python app.py
```

服务器启动后，在浏览器中访问 `http://localhost:5000` 即可使用。

## 项目结构

```
deepseek_web_client/
├── static/            # 静态资源文件
├── templates/         # HTML 模板文件
├── .env               # 环境变量配置文件
├── app.py             # Flask 主应用文件
├── conversation_history.json  # 对话历史记录
├── profile.json       # 用户配置文件
└── requirements.txt   # Python 依赖列表
```

## 贡献指南

欢迎提交 Pull Request 或 Issue 来改进项目。在提交代码前，请确保：

1. 代码符合 PEP 8 规范
2. 添加适当的测试
3. 更新相关文档

## 许可证

本项目采用 MIT 许可证 - 详情请参阅 LICENSE 文件。

## 联系方式

如有任何问题，请联系项目维护者或提交 Issue。
