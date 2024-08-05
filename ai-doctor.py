import os
import requests
import json

# 載入 Langchain
from langchain_openai import (
    ChatOpenAI,
    OpenAIEmbeddings
)
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate
)
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# 載入 Groq
from langchain_groq import ChatGroq

# 載入 Gradio
import gradio as gr

# 載入核心模組
from modules.core_module import(
    config,
    FindSimalarestAnswer
)

# OpenAI 初始化
os.environ["OPENAI_API_KEY"] = config.get(
    'openai',
    'api_key'
)
embeddings = OpenAIEmbeddings()

# Groq 初始化
os.environ["GROQ_API_KEY"] = config.get(
    'groq',
    'api_key'
)

# 指定 llm
# llm = ChatOpenAI(
#      model_name=(
#         'openai',
#         'model'
#     ),
#     temperature=0.5,
#     streaming=True,
#     callbacks=CallbackManager([StreamingStdOutCallbackHandler()])
# )

llm = ChatGroq(model_name=config.get(
        'groq',
        'model'
    ),
    temperature=0.5,
    streaming=True,
    callbacks=CallbackManager([StreamingStdOutCallbackHandler()])
)

# 初始化 conversation
conversation = ConversationChain(
    llm=llm,
    verbose=False,
)

# 記憶庫初始化
memory_jsons = []

# 抓回 QA 學習資料
res = requests.get(
    "https://starnic-linebot-default-rtdb.firebaseio.com/ClinicQA.json", verify=True)
res.encoding = 'utf8'
jsons = json.loads(res.text)

# 機器人開講
async def Chat(message, history):
    print("\n\n=================")
    print("\n提問內容：「{}」".format(message))

    # 輸入文字向量化
    messageEmbedded = embeddings.embed_query(message.strip().replace('\n', ''))

    # 回答初始化
    answer = ''

    # 比對記憶庫
    if len(memory_jsons) > 0:
        answer, qa, correct = FindSimalarestAnswer(messageEmbedded, memory_jsons, 'MEMORY')
        if len(answer) > 0 and correct:
            yield answer

    # 比較向量庫
    if len(answer) == 0:
        answer, qa, correct = FindSimalarestAnswer(messageEmbedded, jsons, 'RAG')

        # 設定人設
        template = '''
        你的回答語氣專業又嚴謹不開玩笑
        提到醫學專有名詞時解釋為容易理解的語言
        提到醫學專有名詞時使用生活化比喻性例子解釋
        提到醫學專有名詞時避免過於專業的術語或技術性細節
        請潤飾所有回答為你的語氣
        不管多少字都只用繁體中文輸出
        '''
        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        human_template = """
        請潤飾以下文字為你的語氣:「{}」
        有任何錯別字也幫忙修正
        只輸出潤飾好的內容文字
        不用任何帶解釋說明與格式
        """.format(answer)
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages([
            system_message_prompt,
            human_message_prompt
        ])

        # 輸出結果
        partial_message = ''
        async for event in conversation.astream_events(
            chat_prompt.format(input=answer),
            version="v1",
        ):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                partial_message += event['data']['chunk'].content
                yield partial_message

        # 只記住有效問答
        if len(qa) > 0 and correct:
            memory_jsons.append({
                "question-embedded": qa['question-embedded'],
                "question": qa['question'],
                "answer": partial_message,
            })

# Chatbot
chatbot = gr.ChatInterface(
    Chat,
    chatbot=gr.Chatbot(
        height=500,
        label="諮詢記錄",
        bubble_full_width=False,
        avatar_images=(None, (os.path.join(os.path.dirname(__file__), "img/AIP.jpg")))
    ),
    textbox=gr.Textbox(placeholder="輸入任何問題", container=False, scale=7),
    title="DR. 數位醫師",
    description=None,
    theme="ParityError/Anime",
    examples=["要怎麼預防癌症?", "我有乳癌怎麼辦?"],
    cache_examples=False,
    submit_btn="發問 ▶️",
    retry_btn=None,
    undo_btn=None,
    clear_btn=None,
    stop_btn="停止 ⏸"
).queue()

if __name__ == "__main__":
    chatbot.launch()
    #chatbot.launch(share=True)
