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
                return profile_data.get("my_profile", {})  # 获取my_profile下的内容
        except FileNotFoundError:
            print(f"警告: 个人资料文件 {self.profile_path} 未找到")
            return {}
        except json.JSONDecodeError:
            print(f"错误: 个人资料文件 {self.profile_path} 格式不正确")
            return {}

    def _load_history(self) -> List[Dict]:
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_history(self):
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)

    def _get_system_prompt(self) -> str:
        profile_info = ""
        if self.profile:
            profile_info = "用户信息:\n"
            for key, value in self.profile.items():
                profile_info += f"- {key}: {value}\n"

        history_info = ""
        if self.conversation_history:
            history_info = "\n历史对话:\n"
            for msg in self.conversation_history[-5:]:
                role = "用户" if msg["role"] == "user" else "AI助手"
                history_info += f"{role}: {msg['content']}\n"

        return f"""
        你是一个有帮助的AI助手。请根据以下信息与用户对话:
        {profile_info}
        {history_info}
        """

    def chat_stream(self, prompt: str, model: str = "deepseek-chat", temperature: float = 0.7, max_tokens: int = 2000):
        self.conversation_history.append({"role": "user", "content": prompt})

        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": self._get_system_prompt()},
                *self.conversation_history
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=data,
            stream=True
        )

        full_response = ""
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
                                # 保留原始格式，前端会处理换行和Markdown
                                full_response += content
                                yield f"data: {json.dumps({'content': content})}\n\n"
                    except json.JSONDecodeError:
                        continue

        if full_response:
            self.conversation_history.append({"role": "assistant", "content": full_response})
            self._save_history()


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