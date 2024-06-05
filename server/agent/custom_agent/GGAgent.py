# GGAgent.py
from __future__ import annotations
import json
import requests
from langchain.agents.agent import Agent
from langchain.chains.llm import LLMChain
from langchain.prompts.chat import ChatPromptTemplate
from langchain.agents.agent import AgentExecutor
from langchain.callbacks.base import BaseCallbackManager
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema.language_model import BaseLanguageModel
from langchain.tools.base import BaseTool
from typing import Any, List, Sequence, Tuple, Optional, Union
import logging

import yaml
from langchain.agents.structured_chat.output_parser import StructuredChatOutputParser
from langchain.memory import ConversationBufferWindowMemory
from typing import Any, List, Sequence, Tuple, Optional, Union
import os
from langchain.agents.agent import Agent
from langchain.chains.llm import LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate, MessagesPlaceholder,
)
import json
import logging
from langchain.agents.agent import AgentOutputParser
from langchain.output_parsers import OutputFixingParser
from langchain.pydantic_v1 import Field
from langchain.schema import AgentAction, AgentFinish, OutputParserException, BasePromptTemplate
from langchain.agents.agent import AgentExecutor
from langchain.callbacks.base import BaseCallbackManager
from langchain.schema.language_model import BaseLanguageModel
from langchain.tools.base import BaseTool

logger = logging.getLogger(__name__)

class GGAgent(Agent):
    """Custom GG Agent."""

    @property
    def observation_prefix(self) -> str:
        """Prefix to append the observation with."""
        return "Observation:"

    @property
    def llm_prefix(self) -> str:
        """Prefix to append the llm call with."""
        return "Thought:"

    def call_knowledge_base(self, query: str, history: List[dict]) -> Tuple[Optional[str], int]:
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
                response_text = self.clean_response_text(response.text)
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

    def call_search_engine(self, query: str, history: List[dict]) -> Tuple[Optional[str], int]:
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
                response_text = self.clean_response_text(response.text)
                response_json = json.loads(response_text)
                answer = response_json.get("answer")
                return answer, 1
            else:
                return None, 1
        except requests.exceptions.RequestException as e:
            return None, 1

    def clean_response_text(self, response_text: str) -> str:
        if response_text.startswith("data:"):
            response_text = response_text[len("data:"):].strip()
        return response_text

    def main_process(self, query: str, history: List[dict]) -> Tuple[Optional[str], int]:
        answer, status_code = self.call_knowledge_base(query, history)
        if status_code == 1:  # 知识库无法回答，调用搜索引擎
            answer, status_code = self.call_search_engine(query, history)
            if not answer:  # 如果搜索引擎也未能提供回答
                status_code = 1
        return answer, status_code

    @classmethod
    def from_llm_and_tools(
            cls,
            llm: BaseLanguageModel,
            tools: Sequence[BaseTool],
            prompt: str = None,
            callback_manager: Optional[BaseCallbackManager] = None,
            input_variables: Optional[List[str]] = None,
            memory_prompts: Optional[List[BasePromptTemplate]] = None,
            **kwargs: Any,
    ) -> Agent:
        """Construct an agent from an LLM and tools."""
        llm_chain = LLMChain(
            llm=llm,
            prompt=ChatPromptTemplate.from_template(prompt),
            callback_manager=callback_manager,
        )
        return cls(
            llm_chain=llm_chain,
            allowed_tools=[tool.name for tool in tools],
            **kwargs,
        )

def initialize_gg_agent(
        tools: Sequence[BaseTool],
        llm: BaseLanguageModel,
        prompt: str = None,
        callback_manager: Optional[BaseCallbackManager] = None,
        memory: Optional[ConversationBufferWindowMemory] = None,
        agent_kwargs: Optional[dict] = None,
        *,
        tags: Optional[Sequence[str]] = None,
        **kwargs: Any,
) -> AgentExecutor:
    agent_kwargs = agent_kwargs or {}
    agent_obj = GGAgent.from_llm_and_tools(
        llm=llm,
        tools=tools,
        prompt=prompt,
        callback_manager=callback_manager,
        **agent_kwargs
    )
    return AgentExecutor.from_agent_and_tools(
        agent=agent_obj,
        tools=tools,
        callback_manager=callback_manager,
        memory=memory,
        tags=tags or [],
        **kwargs,
    )

# 测试函数
if __name__ == "__main__":
    agent = initialize_gg_agent(
        tools=[],
        llm=None,
        prompt="",
    )
    result = agent.main_process("小米su7车的价格", [])
    print("回答:", result)
