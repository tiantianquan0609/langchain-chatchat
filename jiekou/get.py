import requests

# 定义请求数据
data = {
    "query": "什么是工业互联网",
    "history": [
        {
            "role": "user",
            "content": "我们来玩成语接龙，我先来，生龙活虎"
        },
        {
            "role": "assistant",
            "content": "虎头虎脑"
        }
    ]
}

# 发送POST请求
response = requests.post('http://127.0.0.1:5000/api/query', json=data)

# 输出响应内容
print("POST响应状态码:", response.status_code)
print("POST响应内容:", response.json())

# 发送GET请求（尽管API没有实现这个方法，但用于验证API是否处理GET请求）
response = requests.get('http://127.0.0.1:5000/api/query')

# 输出响应内容
print("GET响应状态码:", response.status_code)
print("GET响应内容:", response.text)
