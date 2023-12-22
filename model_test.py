"""
 -*- coding: utf-8 -*-
time: 2023/11/30 17:05
author: suyunsen
email: suyunsen2023@gmail.com
"""

from transformers import (
    BertModel,BertTokenizer,BertPreTrainedModel
)

if __name__ == '__main__':

    modelpath = '/T53/temp/bigmodel/models/chinese_bert'

    bertmodel = BertModel.from_pretrained(modelpath)
    berttoken = BertTokenizer.from_pretrained(modelpath)
    # bertmodel.embeddings
    print(bertmodel.embeddings)
    print(bertmodel)