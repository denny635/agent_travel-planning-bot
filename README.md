# Travel Planning Bot

## 介绍
这个项目是一个旅游规划机器人的Agent, 有网络搜索, ip 定位等工具. 全程改成异步实现，前端使用 Gradio 框架。

## 部署运行

### 1. 配置环境变量

```bash
cp .env.example .env
```
然后往 .env 中加入自己的模型参数、搜索引擎参数、地图搜索参数。

### 2. 安装python依赖库

```bash
conda create -n agent_env python=3.11 # agent_env 也可替换成自己的名称
conda activate agent_env
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 运行

```bash
conda activate agent_env
python web_run.py
```

然后，浏览器中打开对应链接地址，例如：http://0.0.0.0:7860/

