# Reference: https://langchain-ai.github.io/langgraph/tutorials/introduction/#part-2-enhancing-the-chatbot-with-tools
# from langgraph.graph import StateGraph, START
# from states.state import PublicState
# from langgraph.prebuilt import ToolNode, tools_condition
from datetime import datetime, timezone

# def create_graph(model_name, is_async=True):
#     graph = StateGraph(PublicState)
#     tools = [
#             async_web_search,
#              get_location_coordinate,
#             #  get_attractions_information,
#              route_planning,
#              search_nearby_poi,
#              save_info_and_clear_history,
#             ]
#     if is_async:
#         from agents.agents import AsyncAgent as MainAgent
#     else:
#         from agents.agents import SyncAgent as MainAgent
#     travel_agent = MainAgent(
#         model_name=model_name,
#         temperature=0,
#         prompt_template=agent_prompt_template,
#         tools=tools)
#     # Pass the "__call__" function in the ChatterAgent class to add_node. This function will be called when the node is invoked.
#     # The function should be able to use extractor's 'llm' and 'prompt_template' attributes as they have been initialized when created
#     # the extractor instance.
#     graph.add_node("agent", travel_agent)
#     tool_node = ToolNode(tools)
#     graph.add_node("tools", tool_node)
#     # graph.add_edge(START, "init")
#     # graph.add_edge("init", "agent")
#     graph.add_edge(START, "agent")
#     graph.add_conditional_edges("agent", tools_condition)  # Will either direct to a specific tool in tools or to the END node
#     graph.add_edge("tools", "agent")
#     return graph
# def init_app_old(model_name, is_async=True):
#     graph = create_graph(model_name, is_async)
#     from langgraph.checkpoint.memory import InMemorySaver
#     memory = InMemorySaver()
#     # if is_async:
#     #     # memory = AsyncSqliteSaver.from_conn_string(":memory:")
#     #     memory = AsyncSqliteSaver.from_conn_string(":memory:")
#     #     print('memory1:',memory,dir(memory))
#     # else:
#     # memory = SqliteSaver.from_conn_string(":memory:")
#     print('memory2:',memory,dir(memory))
#     app = graph.compile(checkpointer=memory)
#     return app
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call
from langgraph.checkpoint.memory import MemorySaver

from prompts.system_prompt import agent_prompt_template
from tools import *


@wrap_model_call
async def logging_middleware(request, handler):
    """记录每次模型调用的日志"""
    print(f"\n{'=' * 50}")
    print("📝 调用模型")
    cur_msg = request.state.get("messages", [])
    print(f"📊 当前消息数: {len(cur_msg)}", cur_msg)
    print(f"{'=' * 50}")

    # 执行
    response = await handler(request)

    # 记录响应
    if hasattr(response, "messages") and response.messages:
        last_msg = response.messages[-1]
        print(f"✅ 模型响应: {last_msg.content[:50]}...")

    return response


from models.config import LLMManager

_agent = None


def create_agent_app(model_type: str = ""):
    """这里会根据传进的 model_type，选择对应的模型，并创建 agent

    Args:
        model_type (str): 使用的大模型的厂商类型

    Returns:
        _type_: 返回创建的 agent 客户端
    """
    global _agent
    if _agent:
        return _agent
    LLMManager.use_llm(model_type)
    tools = [
        async_web_search,
        get_location_coordinate,
        #  get_attractions_information,
        route_planning,
        search_nearby_poi,
        save_info_and_clear_history,
    ]

    # `create_agent` **创建出来的 Agent 对象本身不分同步 / 异步**，它同时提供两套调用入口；**默认调用方式（invoke）是同步阻塞**，异步需要你手动调用 `ainvoke` 并且加 `await`LangChain。
    _agent = create_agent(
        model=LLMManager.get_llm_client(),  # get_llm(),
        tools=tools,
        system_prompt=agent_prompt_template.format(
            current_time=datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z"), first_user_message=""
        ),  # ✅ 传入函数，而不是字符串
        checkpointer=MemorySaver(),
        debug=True,  # 启用详细输出
        middleware=[logging_middleware],
    )
    return _agent
