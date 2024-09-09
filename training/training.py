'''
訓練 Q&A 資料
'''

import openai
import configparser
import pandas as pd

# Firebase
import firebase_admin
from firebase_admin import (
    credentials,
    db
)

# Firebase API 設定
cred = credentials.Certificate(
    "starnic-linebot-firebase-adminsdk-llmn2-8873441dd6.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://starnic-linebot-default-rtdb.firebaseio.com/'
})

# Firebase 初始化
qa_ref = db.reference('ClinicQA')

# openAI 設定
config = configparser.ConfigParser()
config.read('../config.ini')
openai.api_key = config.get(
    'openai',
    'api_key'
)


# 文字資料轉向量
def TextToEmbedding(inputPrompt=''):
    result = openai.Embedding.create(
        input=[inputPrompt], model='text-embedding-ada-002')['data'][0]['embedding']
    return result


# 訓練
def training():
    upload_data = []

    # 讀取 Excel 檔案-完整
    excel_data = pd.read_excel('./all_question.xlsx')

    # 彙整 Excel 資料
    count_index = 0
    for question in excel_data.question:
        if len(question) > 0 and len(excel_data.answer[count_index]) > 0:
            try:
                q = question
                a = excel_data.answer[count_index]
                r = excel_data.recommend[count_index]
                k = "{}{}".format(q, a)
                e = TextToEmbedding(k)
                upload_data.append({
                    'question': q,
                    'answer': "{}推薦使用我們的{}".format(a, r) if r != '無' else a,
                    'question-embedded': e
                })

                # 歷程
                print({
                    'question': q,
                    'answer': "{}推薦使用我們的{}".format(a, r) if r != '無' else a
                })
                count_index += 1
            except:
                pass

    # 上傳 Firebase
    if len(upload_data) > 0:
        qa_ref.set(upload_data)
        print('Q&A 訓練完成')


if __name__ == "__main__":
    training()
