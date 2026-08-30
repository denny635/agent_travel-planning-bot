from langchain_core.tools import tool
from typing import Annotated
import re
import requests
from lxml.html import etree
from duckduckgo_search import DDGS

@tool
def web_search(
    keywords: Annotated[str, "要搜索的关键词，根据你当前的任务目标确定，尽量精确和详细"],
    max_results: Annotated[int, ("最多返回多少条搜索结果. 如果返回的搜索结果没有太多有用信息，可以指定返回更多搜索结果")] = 10
) -> list:
    """网络搜索工具。在搜索引擎上搜索关键词，返回指定数目的搜索结果，每个结果包含网页的标题、链接和开头内容。"""
    with DDGS() as ddgs:
        results = [r for r in ddgs.text(
            keywords=keywords,
            region='cn-zh',
            max_results=max_results)]
        return results


# To install: pip install tavily-python
import asyncio
import os
from tavily import AsyncTavilyClient

# ✅ 推荐：模块级全局实例
tavily_client = None #AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool
async def async_web_search(
    keywords: Annotated[str, "要搜索的关键词，根据你当前的任务目标确定，尽量精确和详细"],
    max_results: Annotated[int, ("最多返回多少条搜索结果. 如果返回的搜索结果没有太多有用信息，可以指定返回更多搜索结果")] = 10
) -> list:
    """网络搜索工具。在搜索引擎上搜索关键词，返回指定数目的搜索结果，每个结果包含网页的标题、链接和开头内容。"""
    # 自动读取环境变量 TAVILY_API_KEY
    global tavily_client
    if tavily_client is None:
        tavily_client = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    
    # 直接使用全局客户端，无需 with 上下文
    response = await tavily_client.search(
        query=keywords,
        max_results=max_results,
        search_depth="basic"  # 或 "advanced"
    )
    # Tavily 返回的结果结构略有不同，需要提取
    results = response.get("results", [])
    list_data = [
        {
            "title": r.get("title", ""),
            "body": r.get("content", ""),
            "href": r.get("url", ""),
            "score": r.get("score", ""),
        }
        for r in results
    ]
    return list_data


def test():
    # "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"
    from tavily import TavilyClient 
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    response = client.search(
        query="长沙 景点",
        search_depth="advanced"
    )
    print(response)


# test the tool
if __name__ == "__main__":
    # # 使用 'lite' 或 'html' 后端，通常更稳定
    # results = DDGS().text("Python programming", backend='html', max_results=5)
    # print(results) 
    
    asyncio.run(async_web_search())
    
    # print(web_search.args_schema.model_json_schema())
    # a=web_search.invoke({"keywords": "长沙 景点"})
    # print(a)
    # pass