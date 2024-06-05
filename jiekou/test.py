from flask import Flask, request, jsonify
import json
import requests
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)


def clean_response_text(response_text):
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
        "history": [],
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
            logging.info("知识库API响应文本: %s", response_text)
            try:
                response_json = json.loads(response_text)
                answer = response_json.get("answer")
                docs = response_json.get("docs", [])
                if answer == "未找到相关文档,该回答为大模型自身能力解答！" or any(
                        "未找到相关文档" in doc for doc in docs):
                #根据已知信息无法回答该问题。
                    return None, 1
                return answer, 0
            except json.JSONDecodeError:
                logging.error("知识库API响应不是有效的JSON：%s", response_text)
                return None, 1
        else:
            logging.error("调用知识库API请求失败，状态码：%d", response.status_code)
            return None, 1
    except requests.exceptions.RequestException as e:
        logging.error("知识库API请求发生异常: %s", e)
        return None, 1


def call_search_engine(query, history):
    url = "http://10.2.14.80:7861/chat/search_engine_chat"
    body = {
        "query": query,
        "search_engine_name": "bing",
        "top_k": 3,
        "history": [],
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
            logging.info("搜索引擎API响应文本: %s", response_text)
            try:
                response_json = json.loads(response_text)
                answer = response_json.get("answer")
                return answer, 1
            except json.JSONDecodeError:
                logging.error("搜索引擎API响应不是有效的JSON：%s", response_text)
                return None, 1
        else:
            logging.error("调用搜索引擎API请求失败，状态码：%d", response.status_code)
            return None, 1
    except requests.exceptions.RequestException as e:
        logging.error("搜索引擎API请求发生异常: %s", e)
        return None, 1


def main_process(query, history):
    answer, status_code = call_knowledge_base(query, history)
    if status_code == 1:
        answer, status_code = call_search_engine(query, history)
        if not answer:
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
