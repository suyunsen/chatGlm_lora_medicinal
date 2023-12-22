"""
 -*- coding: utf-8 -*-
time: 2023/11/13 15:39
author: suyunsen
email: suyunsen2023@gmail.com
"""


from datasets import load_dataset

import torch

def token(example):
    return{'input_ids':example['query'],'labels':example['response']}

def test():
    path = '/T53/temp/bigmodle/datas/ChatMed_Consult-v0.3.json'
    data = load_dataset("json", data_files=path)
    column_names = data['train'].column_names
    res = data['train'].map(lambda example: token(example), batched=False, remove_columns=column_names)
    print(res[0])
    print("你好啊")

if __name__ == '__main__':

    a = torch.rand(2,3)
    b = a
    print(a == b)