import gradio as gr
from langchain_core.messages import HumanMessage

from graph.graph import create_agent_app
from utils.helper import get_thread_id

USE_LLM_TYPE = "qianwen"


# Streaming and main message processing generator
async def process_message(user_message, chatbot_history, debug_history):
    chatbot_history.append({"role": "user", "content": user_message})  # User message without label
    # yield chatbot_history, "" # 先把问题输出一下
    app = create_agent_app(model_type=USE_LLM_TYPE)
    thread_id = get_thread_id()
    print("thread_id:", thread_id)
    config = {"configurable": {"thread_id": thread_id}}

    formatted_user_message = HumanMessage(content=user_message)
    # print('formatted_user_message:',formatted_user_message)
    # 2. 累积完整回复
    full_response = ""

    async for event in app.astream_events({"messages": formatted_user_message}, config=config, version="v2"):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                full_response += content
                # print(f"累积: {full_response}")  # 调试

                # 3. 更新或创建 AI 消息（只有一条！）
                if chatbot_history and chatbot_history[-1].get("role") == "assistant":
                    # 更新已有的 AI 消息
                    chatbot_history[-1]["content"] = full_response
                else:
                    # 第一次添加 AI 消息
                    chatbot_history.append({"role": "assistant", "content": full_response})

                # 4. yield 更新后的历史
                yield chatbot_history, debug_history
        elif kind == "on_tool_start":
            debug_history = f"Starting tool: {event['name']} with inputs: {event['data'].get('input')}\n"
            print("debug_history:", debug_history)
            yield chatbot_history, debug_history  # Stream tool start info
        elif kind == "on_tool_end":
            debug_history += f"Done tool: {event['name']}\nTool output: {event['data'].get('output')}\n--\n"
            print("debug_history:", debug_history)
            yield chatbot_history, debug_history  # Stream tool end info
        elif kind == "on_chat_model_end":
            pass


def clear_input():
    return ""


list_show = []


def test_process_message(user_input, chatbot, debug_info):
    list_show.append({"role": "user", "content": "Hello"})
    return list_show, "World"


# Gradio app interface
def start_gradio():
    with (
        gr.Blocks() as demo
    ):  # Gradio 自定义布局顶级容器，对比简易 gr.Interface： Interface：固定「输入 - 输出」左右结构，只能单流程；Blocks：自由写页面布局，支持多行多列、Tab、折叠、多按钮、跨组件联动，复杂 AI 页面必备。
        gr.Markdown(
            "# 基于Langgraph的旅游规划助手"
        )  # 页面富文本组件，支持标准 Markdown 语法（标题 #、加粗**、表格、链接、代码块）；用来写页面标题、说明文档、提示文字，纯展示，不可交互。
        with (
            gr.Row(equal_height=True) as chat_interface
        ):  # gr.Row() 横向布局容器 内部所有组件水平并排，搭配 scale 分配宽度占比；equal_height=True：该行内所有 Column 高度强制统一（你左右两栏等高）；
            chat_interface.elem_classes = [
                "full-height"
            ]  # elem_classes：给当前 DOM 元素附加 CSS 类名； 作用：配合自定义 CSS 实现面板高度铺满页面，避免上下留白。 同类属性：elem_id="xxx" 给组件设置唯一 HTML ID，用于精准写 CSS 样式。
            # Left column for debug info
            with gr.Column(
                scale=1
            ):  # gr.Column() 纵向布局容器, 内部组件垂直堆叠，Row 套 Column 实现「左右分栏」经典布局。scale=1 宽度权重分配, 同一 Row 下多个 Column 通过 scale 按比例瓜分总宽度：左栏 scale=1，右栏 scale=3, 宽度比例 = 1 : 3，右侧聊天区宽度是调试区 3 倍。
                debug_info = gr.Textbox(label="Debug Info", lines=30, interactive=False, elem_id="debug-info")
                """
                单行 / 多行文本输入展示组件，这里用作只读调试日志面板：
                label="Debug Info"：组件上方显示标题；
                lines=30：默认渲染 30 行高度，撑起大面板；
                interactive=False：只读模式，用户无法手动编辑，只能后端代码填充内容；
                elem_id="debug-info"：唯一 DOM ID，自定义 CSS 精准控制大小、滚动、配色。
                """

            # Right column for chat interface
            with gr.Column(scale=3):  # 右侧 gr.Column(scale=3) 聊天区域组件
                chatbot = gr.Chatbot(  # Gradio 内置聊天渲染控件，专门存储、展示人机对话历史： 存储格式：[(用户消息1, AI回复1), (用户消息2, AI回复2)]； show_label=False：隐藏组件顶部的标题文字，界面更简洁； elem_id="chatbot"：自定义 ID 用于样式调整。
                    label="User-AI Chat",
                    show_label=False,
                    elem_id="chatbot",
                    group_consecutive_messages=False,
                    # type="tuples"  # 关键一行
                )
                """
                （2）gr.Textbox 用户输入框
                聊天底部输入框，可多行输入：
                placeholder="Type your message here"：输入框灰色占位提示文字；
                lines=3 默认 3 行高度，max_lines=5 自动扩容上限 5 行；
                show_label=False 隐藏标题。
                """

                user_input = gr.Textbox(
                    label="Your message",
                    placeholder="输入您的旅游景点问题，例如：北京有哪些好玩的景点？",
                    lines=3,
                    max_lines=5,
                    show_label=False,
                    elem_id="user-input",
                )
                # （3）gr.Button("Send") 按钮交互组件
                # 触发后端函数的核心控件，点击执行绑定的逻辑。
                submit_click = gr.Button("Send")  # Submit function for message input

        # Define the submission action
        def submit_action():
            return process_message, [user_input, chatbot, debug_info], [chatbot, debug_info]
            # 第二个参数是 参数, 第三个参数是输出到的 地方

        # 把 fn, inputs, outputs 打包成元组，再用 * 解包传入 .click()
        # submit_click.click(process_message, [user_input, chatbot, debug_info], [chatbot, debug_info])
        # 缺陷：之前提到过，这种封装会破坏异步生成器识别，流式更新容易异常。

        # submit_click.click(
        #     process_message,                # fn：要执行的函数
        #     [user_input, chatbot, debug_info],  # 第二个参数 inputs
        #     [chatbot, debug_info]               # 第三个参数 outputs
        # )
        # 执行逻辑：
        #     点击按钮时，Gradio 自动依次读取这三个组件当前的值，按顺序打包成参数传给 process_message。
        # outputs = [chatbot, debug_info]
        # 含义：函数 yield /return 出来的结果，要更新到页面上哪些组件
        # 你的函数最后会 yield chatbot_history, debug_history，返回一个二元元组：

        # Bind the submission action to both the button click and the input box
        submit_click.click(process_message, [user_input, chatbot, debug_info], [chatbot, debug_info]).then(
            clear_input, None, user_input
        )
        # 第一个参数	clear_input	要执行的函数（清空输入框）
        # 第二个参数	None	该函数的输入（不需要数据）
        # 第三个参数	user_input	该函数的输出目标（更新到 user_input 组件）
        # .click 绑定按钮鼠标点击；
        # user_input.submit(*submit_action()).then(
        #     clear_input, None, user_input
        # ) # .submit()：绑定输入框回车提交，聊天框标配
        # .then(clear_input, None, user_input) 链式回调

        # Gradio 事件链式语法：主函数执行完成后，再执行第二个函数：
        # 主逻辑：process_message 流式回复 AI 内容；
        # 后置回调：clear_input 清空输入框；
        # None：第二个函数无输入组件；
        # user_input：clear_input 的返回值赋值给输入框，实现清空。
    demo.queue()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)


if __name__ == "__main__":
    start_gradio()
