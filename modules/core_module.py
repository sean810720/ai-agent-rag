'''
核心模組
'''
import numpy as np
import configparser

# 設定檔設置
config = configparser.ConfigParser()
config.read('config.ini')

# 比較相似度
def FindSimalarestAnswer(messageEmbedded, jsons, mode='RAG'):
    answer = ''
    qas = []
    qas_similarity = []
    for json_data in jsons:
        qas.append(json_data)

        # 計算兩個向量的相似度
        qas_similarity.append(
            AdjustedCosineSimilarity(
                np.array(messageEmbedded),
                np.array(json_data['question-embedded'])
            )
        )

    # 找出最相似 Q&A
    similarity = max(qas_similarity)
    qa = qas[qas_similarity.index(similarity)]
    print("\n{} 最接近問題: {} (相似度: {})".format(mode, qa['question'], similarity))
    print("\n{} 最接近回答: {} (相似度: {})".format(mode, qa['answer'], similarity))

    # 相似門檻檢查

    # 是否正確答案
    correct = False

    if len(qa) > 0:
        # 記憶庫
        if mode == 'MEMORY':
            if similarity >= float(config.get(
                'similarity-threshold',
                'memory'
            )):
                answer = qa['answer']
                correct = True
        # RAG
        elif mode == 'RAG':
            if similarity >= float(config.get(
                'similarity-threshold',
                'rag'
            )):
                answer = "{}。只用繁體中文輸出".format(qa['answer'])
                correct= True
            else:
                answer = "這個問題超出可回答範圍"
    print("\n{} 搜尋結果: {}".format(mode, answer))
    return answer, qa, correct


# 餘弦相似度
def AdjustedCosineSimilarity(v1, v2):

    # 計算向量平均值
    v1_mean = np.mean(v1)
    v2_mean = np.mean(v2)

    # 計算調整後的向量
    v1_adj = v1 - v1_mean
    v2_adj = v2 - v2_mean

    # 計算分子和分母
    numerator = np.dot(v1_adj, v2_adj)
    denominator = np.linalg.norm(v1_adj) * np.linalg.norm(v2_adj)

    # 計算調整餘弦相似度
    # 處理分母為零的情況
    similarity = numerator / denominator if denominator > 0 else 0

    return similarity
