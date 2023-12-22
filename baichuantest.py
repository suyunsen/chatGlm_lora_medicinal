"""
 -*- coding: utf-8 -*-
time: 2023/11/19 15:44
author: suyunsen
email: suyunsen2023@gmail.com
"""


import torch
from transformers import AutoModelForCausalLM, AutoTokenizer,BitsAndBytesConfig
from transformers.generation.utils import GenerationConfig



if __name__ == '__main__':
    mode_p = '/T53/temp/bigmodle/baichuan'
    tokenizer = AutoTokenizer.from_pretrained(mode_p, use_fast=False, trust_remote_code=True)
    q_config = BitsAndBytesConfig(load_in_4bit=True,
                                  bnb_4bit_quant_type='nf4',
                                  bnb_4bit_use_double_quant=True,
                                  bnb_4bit_compute_dtype=torch.float32)
    model = AutoModelForCausalLM.from_pretrained(mode_p , quantization_config = q_config,device_map="auto",
                                                 torch_dtype=torch.float16, trust_remote_code=True)
    model.generation_config = GenerationConfig.from_pretrained(mode_p)
    messages = []
    messages.append({"role": "user", "content": "2016年3月21日发生一次很严重，脖子发软抬不起头，做CT，脑电波验血都没问题今天又出现一次晕倒"})
    response = model.chat(tokenizer, messages)
    print(response)