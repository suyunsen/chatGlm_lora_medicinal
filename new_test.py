"""
 -*- coding: utf-8 -*-
time: 2023/11/13 17:06
author: suyunsen
email: suyunsen2023@gmail.com
"""

from datasets import load_dataset

import torch
import os
import transformers
from transformers import (
    AutoModel,
    AutoTokenizer,
    HfArgumentParser,
    TrainingArguments,
    Trainer,
    BitsAndBytesConfig,
    AutoModelForCausalLM
)

from peft import PeftModel, PeftConfig

def atoken(example):
    return{'input_ids':example['query'],'labels':example['response']}

# def aatest():
#     path = '/T53/temp/bigmodle/datas/ChatMed_Consult-v0.3.json'
#     data = load_dataset("json", data_files=path)
#     column_names = data['train'].column_names
#     res = data['train'].map(lambda example: token(example), batched=False, remove_columns=column_names)
#     print(res[0])
#     print("你好啊")

def t_bigmod():
    modepath = './chat_c'

    tokenizer = AutoTokenizer.from_pretrained(modepath, trust_remote_code=True)
    model = AutoModel.from_pretrained(modepath, trust_remote_code=True).half().cuda()
    response, history = model.chat(tokenizer, "你好", history=[])
    print(response)
    #
    print(model)


def t_test_lora():
    modepath = './chat_c'
    peft_p = './saved_files/chatGLM_6B_QLoRA_t32'
    q_config = BitsAndBytesConfig(load_in_4bit=True,
                                  bnb_4bit_quant_type='nf4',
                                  bnb_4bit_use_double_quant=True,
                                  bnb_4bit_compute_dtype=torch.float32)

    base_model = AutoModel.from_pretrained(modepath,
                                           quantization_config = q_config,
                                           trust_remote_code=True,
                                           device_map='auto')
    model = PeftModel.from_pretrained(base_model,peft_p)

    tokenizer = AutoTokenizer.from_pretrained(modepath , trust_remote_code=True)

    input_text = '2016年3月21日发生一次很严重，脖子发软抬不起头，做CT，脑电波验血都没问题今天又出现一次晕倒'
    response, history = model.chat(tokenizer=tokenizer, query=input_text)
    response1, history1 = base_model.chat(tokenizer=tokenizer, query=input_text)

    print(f'微调后回答 {response}')
    print(f'微调前回答 {response1}')

if __name__ == '__main__':
    t_test_lora()

