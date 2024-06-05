from flask import Flask, request, jsonify
import json
import requests

app = Flask(__name__)


def clean_response_text(response_text):
    # 去除响应文本中的非JSON部分
    if response_text.startswith("data:"):
        response_text = response_text[len("data:"):].strip()
    return response_text


def call_knowledge_base(query, history):
    url = "http://10.2.14.80:7861/chat/knowledge_base_chat"
    body = {
        "query": query,
        "knowledge_base_name": "百科问答csv",
        "top_k": 3,
        "score_threshold": 0.6,
        "history": history,
        "stream": False,
        "model_name": "chatglm3-6b",
        "temperature": 0.7,
        "max_tokens": 0,
        "prompt_name": "default"
    }
    try:
        response = requests.post(url, json=body)
        if response.status_code == 200:
            response_text = clean_response_text(response.text)
            print("知识库API响应文本:", response_text)
            try:
                response_json = json.loads(response_text)
                answer = response_json.get("answer")
                docs = response_json.get("docs", [])
                if answer == "未找到相关文档,该回答为大模型自身能力解答！" or any(
                        "未找到相关文档" in doc for doc in docs):
                    return None, 1
                return answer, 0
            except json.JSONDecodeError:
                print("知识库API响应不是有效的JSON：", response_text)
                return None, 1
        else:
            print("调用知识库API请求失败，状态码：", response.status_code)
            return None, 1
    except requests.exceptions.RequestException as e:
        print("知识库API请求发生异常", e)
        return None, 1


def call_search_engine(query, history):
    url = "http://10.2.14.80:7861/chat/search_engine_chat"
    body = {
        "query": query,
        "search_engine_name": "bing",
        "top_k": 3,
        "history": history,
        "stream": False,
        "model_name": "chatglm3-6b",
        "temperature": 0.7,
        "max_tokens": 0,
        "prompt_name": "default",
        "split_result": False
    }
    try:
        response = requests.post(url, json=body)
        if response.status_code == 200:
            response_text = clean_response_text(response.text)
            print("搜索引擎API响应文本:", response_text)
            try:
                response_json = json.loads(response_text)
                answer = response_json.get("answer")
                return answer, 1
            except json.JSONDecodeError:
                print("搜索引擎API响应不是有效的JSON：", response_text)
                return None, 1
        else:
            print("调用搜索引擎API请求失败，状态码：", response.status_code)
            return None, 1
    except requests.exceptions.RequestException as e:
        print("搜索引擎API请求发生异常", e)
        return None, 1


def main_process(query, history):
    answer, status_code = call_knowledge_base(query, history)
    if status_code == 1:  # 知识库无法回答，调用搜索引擎
        answer, status_code = call_search_engine(query, history)
        if not answer:  # 如果搜索引擎也未能提供回答
            status_code = 1
    return answer, status_code


@app.route('/api/query', methods=['POST'])
def query():
    data = request.get_json()
    query = data.get('query')
    history = data.get('history', [])

    if not query:
        return jsonify({"error": "Query is required"}), 400

    answer, status_code = main_process(query, history)

    return jsonify({
        "answer": answer,
        "status_code": status_code
    })


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
