from flask import Flask, render_template, request, jsonify, Response
import json
import os
import requests
import markdown2
from typing import Dict, List

app = Flask(__name__)


class DeepSeekClient:
    def __init__(self, api_key: str, profile_path: str = "profile.json",
                 history_path: str = "conversation_history.json"):
        self.api_key = api_key
        self.profile_path = profile_path
        self.history_path = history_path
        self.base_url = "https://api.deepseek.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.profile = self._load_profile()
        self.conversation_history = self._load_history()

    def _load_profile(self) -> Dict:
        """加载个人资料"""
        try:
            with open(self.profile_path, "r", encoding="utf-8") as f:
                profile_data = json.load(f)
                return profile_data.get("my_profile", {})
        except FileNotFoundError:
            print(f"警告: 个人资料文件 {self.profile_path} 未找到")
            return {}
        except json.JSONDecodeError:
            print(f"错误: 个人资料文件 {self.profile_path} 格式不正确")
            return {}

    def _load_history(self) -> List[Dict]:
        """加载对话历史"""
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_history(self):
        """保存对话历史"""
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)

    def _render_markdown(self, text: str) -> str:
        """将Markdown文本转换为HTML"""
        return markdown2.markdown(
            text,
            extras=["fenced-code-blocks", "tables", "break-on-newline"]
        )

    def _get_system_prompt(self) -> str:
        """生成系统提示词，包含用户资料和历史对话"""
        # 构建个人资料部分
        profile_info = "## 用户详细资料\n"
        if self.profile:
            profile_info += f"- 姓名: {self.profile.get('name', '未提供')}\n"
            profile_info += f"- 年龄: {self.profile.get('age', '未提供')}\n"
            profile_info += f"- 职业/兴趣: {self.profile.get('profession', '未提供')}\n"

            if 'interests' in self.profile:
                profile_info += f"- 兴趣爱好: {', '.join(self.profile['interests'])}\n"

            if 'memory' in self.profile:
                profile_info += "\n## 重要经历和现状\n"
                for memory in self.profile['memory']:
                    profile_info += f"- {memory}\n"

        # 构建历史对话部分
        history_info = ""
        if self.conversation_history:
            history_info = "\n## 最近对话记录\n"
            for msg in self.conversation_history[-5:]:  # 只使用最近的5条历史记录
                role = "用户" if msg["role"] == "user" else "你"
                history_info += f"{role}: {msg['content']}\n"

        # 特殊指示 - 基于用户情况定制
        special_instructions = """
        ## 特别注意事项
        1. 用户目前有心理健康问题，请保持温和、支持性的语气
        2. 避免使用可能触发负面情绪的词汇
        3. 对技术话题(如服务器运维)可以详细讨论
        4. 当用户提到抑郁或自杀倾向时，应适当安抚并提供帮助资源
        5. 用户喜欢被倾听和理解，多给予积极反馈
        """

        return f"""
        你是一个专门为石轩丞定制的AI助手。请根据以下信息与用户对话:
        {special_instructions}
        {profile_info}
        {history_info}

        回答时请注意:
        - 使用自然、口语化的表达
        - 对技术问题可以深入讨论
        - 适当询问用户的猫和服务器近况
        - 避免说教或批评性语言
        """

    def chat_stream(self, prompt: str, model: str = "deepseek-chat", temperature: float = 0.7, max_tokens: int = 2000):
        """
        与DeepSeek API交互

        :param prompt: 用户输入
        :param model: 使用的模型
        :param temperature: 生成温度
        :param max_tokens: 最大token数
        """
        # 添加用户消息到历史
        self.conversation_history.append({"role": "user", "content": prompt})

        # 准备请求数据
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": self._get_system_prompt()},
                *self.conversation_history
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True  # 启用流式输出
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                stream=True
            )

            if response.status_code != 200:
                print(f"API请求失败: {response.status_code} - {response.text}")
                yield f"data: {json.dumps({'error': f'API请求失败: {response.status_code}'})}\n\n"
                return

            full_response = ""

            # 处理流式响应
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data:"):
                        json_data = decoded_line[5:].strip()
                        if json_data == "[DONE]":
                            continue
                        try:
                            chunk = json.loads(json_data)
                            if "choices" in chunk and chunk["choices"]:
                                content = chunk["choices"][0].get("delta", {}).get("content", "")
                                if content:
                                    full_response += content
                                    yield f"data: {json.dumps({'content': content})}\n\n"
                        except json.JSONDecodeError:
                            continue

            # 添加AI响应到历史
            if full_response:
                self.conversation_history.append({"role": "assistant", "content": full_response})
                self._save_history()

        except requests.exceptions.RequestException as e:
            print(f"请求出错: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"


# 从环境变量获取API密钥
api_key = os.getenv("DEEPSEEK_API_KEY", "your_api_key_here")
client = DeepSeekClient(api_key)


@app.route('/')
def index():
    return render_template('index.html', profile=client.profile)


@app.route('/chat', methods=['POST'])
def chat():
    prompt = request.json.get('prompt')
    if not prompt:
        return jsonify({"error": "请输入内容"}), 400

    return Response(client.chat_stream(prompt), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)