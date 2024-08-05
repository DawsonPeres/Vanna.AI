import spacy
import jieba.posseg as pseg

# 加载中文模型
nlp = spacy.load("zh_core_web_sm")


def extract_keywords(sentence):
    """查找中文关键词"""
    doc = nlp(sentence)
    if len(doc) < 2:
        return [sentence]
    keywords = []
    for token in doc:
        # 查找名词
        if token.pos_ in ["NOUN", "PROPN"]:
            # 收集名词及其修饰词
            phrase = ''.join([child.text for child in token.subtree if child.pos_ in ["NOUN", "PROPN"]])
            if phrase and phrase not in keywords:
                keywords.append(phrase)
    return keywords


def cut_sentence(sentence: str) -> list:
    """
    分句
    """
    return_list = []
    if "表" in sentence:
        sentence = sentence.split("表")
        return_list.append(sentence[0])
    words = pseg.cut(sentence[0])
    for word, flag in words:
        # if flag in ['n', 'nr', 'ns', 'nt', 'nz', 'vn']:
        if flag in ['n', 'eng'] and len(word) > 1:
            return_list.append(word)
    return return_list


def split_sentence(sentences: list, documentation_type: str = "table") -> list:
    """
    拆分句子，区分表信息和字段信息
    """
    sentences_list = []
    if documentation_type == "table":
        for sentence in sentences:
            _key, _value = sentence.split("是")
            if _key == _value:
                continue
            sentences_list.append((_key, _value))
    elif documentation_type == "column":
        for sentence in sentences:
            _, column_value = sentence.split("的"), sentence.split("的")[-1]
            _key, _value = column_value.split("字段是")
            if _key == _value:
                continue
            sentences_list.append((_key, _value))
            print(_key, _value)
    return sentences_list


if __name__ == '__main__':
    # 示例用法
    # _sentence = "结合三季度的销售清单和现存物料，输出四季度的方案"
    # print--> ['三季度', '销售', '销售清单', '三季度销售清单物料', '四季度', '三季度销售清单物料四季度方案']
    # _sentence = "你打我我骂他他要你，剩余的物料，你踹他"
    # _sentence = '给我十条物料'
    # print--> ['物料']
    # keyword = extract_keywords(_sentence)
    # _sentence = "工程报价主表的报价日期-到期日期字段是DUE_DATE"
    _sentence = "物料库存组表的前十条的物料id"
    keyword = cut_sentence(_sentence)
    print(keyword)
