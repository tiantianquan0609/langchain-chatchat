# custom_agent.py

def work(input_data):
    import json
    import requests

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
                response_json = json.loads(response_text)
                answer = response_json.get("answer")
                docs = response_json.get("docs", [])
                if answer == "未找到相关文档,该回答为大模型自身能力解答！" or any("未找到相关文档" in doc for doc in docs):
                    return None, 1
                return answer, 0
            else:
                return None, 1
        except requests.exceptions.RequestException as e:
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
                response_json = json.loads(response_text)
                answer = response_json.get("answer")
                return answer, 1
            else:
                return None, 1
        except requests.exceptions.RequestException as e:
            return None, 1

    def main_process(query, history):
        answer, status_code = call_knowledge_base(query, history)
        if status_code == 1:  # 知识库无法回答，调用搜索引擎
            answer, status_code = call_search_engine(query, history)
            if not answer:  # 如果搜索引擎也未能提供回答
                status_code = 1
        return answer, status_code

    # 在这里将 input_data 传递给 main_process 函数
    query = input_data
    history = []  # 由于工具调用不会传递历史记录，因此这里简化为一个空列表
    answer, status_code = main_process(query, history)
    return answer

# 测试函数
if __name__ == "__main__":
    result = work("小米su7车的价格")
    print("回答:", result)
