import os
import requests
import json

# 載入 Gradio
import gradio as gr

# 載入 Langchain Groq
from langchain_groq import ChatGroq

# 載入 Langchain Prompts
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate
)

# 載入 Langchain Agents
from langchain.agents import create_tool_calling_agent
from langchain.agents import AgentExecutor
from langchain.tools import tool

# 載入 Langchain Memory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# 載入 Langchain Callback
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# 載入 Langchain OpenAI
from langchain_openai import (
    ChatOpenAI,
    OpenAIEmbeddings
)

# 載入核心模組
from modules.core_module import(
    config,
    FindSimalarestAnswer
)

# Groq 初始化
os.environ["GROQ_API_KEY"] = config.get(
    'groq',
    'api_key'
)

# OpenAI 初始化
os.environ["OPENAI_API_KEY"] = config.get(
    'openai',
    'api_key'
)
embeddings = OpenAIEmbeddings()

# LLM 初始化
""" model = ChatGroq(model_name=config.get(
        'groq',
        'model'
    ),
    temperature=0.5,
    max_tokens=3000,
    n=1,
    streaming=True,
    callbacks=CallbackManager([StreamingStdOutCallbackHandler()])
)
"""
model = ChatOpenAI(model_name=config.get(
        'openai',
        'model'
    ),
    temperature=0.5,
    max_tokens=3000,
    n=1,
    streaming=True,
    callbacks=CallbackManager([StreamingStdOutCallbackHandler()])
)

# QA 初始化
res = requests.get(
    "https://starnic-linebot-default-rtdb.firebaseio.com/ClinicQA.json", verify=True)
res.encoding = 'utf8'
jsons = json.loads(res.text)

# 工具初始化
@tool
async def rag_doctor_answer(message: str) -> str:
    '''
    詢問任何醫療相關問題
    詢問任何身體不適問題
    詢問任何疾病防治問題
    詢問任何乳癌治療問題
    詢問任何乳癌預防問題
    詢問任何醫療資源問題
    詢問任何醫學相關問題
    詢問任何疑難雜症
    詢問任何問題
    '''
    # 輸入文字處理
    message = message.strip().replace('\n', '')
    messageEmbedded = embeddings.embed_query(message)

    # 比較向量庫
    answer, qa, correct = FindSimalarestAnswer(messageEmbedded, jsons, 'RAG')
    return answer

# Tools 設定
tools = [rag_doctor_answer]
llm_forced_to_use_tool = model.bind_tools(tools, tool_choice="any")

# Prompt 初始化
template = '''
你是一位經驗豐富又熱心的專業醫師
你的回答語氣專業嚴謹又不開玩笑
提到醫學專有名詞時解釋為容易理解的語言
提到醫學專有名詞時使用生活化比喻性例子解釋
提到醫學專有名詞時避免過於專業的術語或技術性細節
如果是寒暄或禮貌性提問，不使用工具與記憶，只回應對應的禮貌性回答，例如：「Human: 醫生你好 AI: 你好，有任何醫療問題我都可以協助您喔」
除了寒暄或禮貌性提問請優先透過工具回答問題
請潤飾所有透過工具取得的內容為你的語氣
不管多少字都只用繁體中文回答
'''
system_message_prompt = SystemMessagePromptTemplate.from_template(template)
human_template = '''
{input}
如果是透過工具取得的內容用你的語氣進行潤飾與擴增
如果是透過工具取得的內容回答不用任何帶解釋說明與格式
如果是寒暄或禮貌性提問，不使用工具與記憶，只回應對應的禮貌性回答，例如：「Human: 醫生你好 AI: 你好，有任何醫療問題我都可以協助您喔」
只用繁體中文回答
'''
human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
prompt = ChatPromptTemplate.from_messages([
    system_message_prompt,
    MessagesPlaceholder(variable_name='chat_history', optional=True),
    HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=['input'], template=human_template)),
    MessagesPlaceholder(variable_name='agent_scratchpad')
])

# 記憶初始化
session_id = '<foo>'
store = {}
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# 機器人開講
async def Chat(message, history, request: gr.Request):

    # 使用者 Session Hash
    if(request):
        session_id = request.session_hash
    print("\n\n===== User Session ID =====\n\n{}".format(session_id))

    # 使用者輸入
    print("\n===== User input =====\n\n{}".format(message))

    if not len(message):
        print("\n\n===== AI response =====\n\n哈囉，請問您想問些什麼呢?\n\n")
        yield "哈囉，請問您想問些什麼呢?"

    else:
        # Agent 設定
        agent = create_tool_calling_agent(llm_forced_to_use_tool, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools)
        agent_with_chat_history = RunnableWithMessageHistory(
            agent_executor,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history"
        )

        # 輸出結果
        partial_message = ''
        async for event in agent_with_chat_history.astream_events(
            {"input": message},
            config={"configurable": {"session_id": session_id}},
            version="v1",
        ):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                partial_message += event['data']['chunk'].content
                yield(partial_message)
        print("\n\n===== AI response =====\n\n{}\n\n".format(partial_message))

chatbot = gr.ChatInterface(
    Chat,
    chatbot=gr.Chatbot(
        height=500,
        label="諮詢記錄",
        bubble_full_width=False,
        avatar_images=(None, (os.path.join(os.path.dirname(__file__), "img/AIP.jpg")))
    ),
    textbox=gr.Textbox(placeholder="輸入任何問題", container=False, scale=7),
    title="Dr. 數位醫師",
    description=None,
    theme="ParityError/Anime",
    examples=[
        "什麼是精準醫療",
        "三陰性乳癌治療方式有哪些？",
        "良性腫瘤、惡性腫瘤、乳房鈣化，分別代表什麼？分別要如何治療？"
    ],
    cache_examples=False,
    submit_btn="發問 ▶️",
    retry_btn=None,
    undo_btn=None,
    clear_btn=None,
    stop_btn="停止 ⏸"
).queue()

if __name__ == "__main__":
    chatbot.launch()
