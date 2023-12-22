"""
 -*- coding: utf-8 -*-
time: 2023/11/24 21:09
author: suyunsen
email: suyunsen2023@gmail.com
"""


import os
import math
import pathlib
from typing import Optional, Dict
from dataclasses import dataclass, field
import json

import torch
from torch.utils.data import Dataset
import transformers
from transformers.training_args import TrainingArguments

from loguru import logger

import transformers
from transformers import (
    AutoModel,
    AutoTokenizer,
    HfArgumentParser,
    set_seed,
    TrainingArguments,
    Trainer,
    BitsAndBytesConfig,
    AutoModelForCausalLM
)

from peft import set_peft_model_state_dict, prepare_model_for_kbit_training, get_peft_model, LoraConfig, TaskType
from typing import List, Dict, Optional
from peft.utils import TRANSFORMERS_MODELS_TO_LORA_TARGET_MODULES_MAPPING

import argparse


def parse_args():
    parser = argparse.ArgumentParser(description='ChatGLM-6B QLoRA')
    parser.add_argument('--train_args_json', type=str, required=True, help='TrainingArguments的json文件')
    parser.add_argument('--model_name_or_path', type=str, default='THUDM/chatglm-6b', help='模型id或local path')
    parser.add_argument('--train_data_path', type=str, required=True, help='训练数据路径')
    parser.add_argument('--eval_data_path', type=str, default=None, help='验证数据路径')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--max_input_length', type=int, default=512, help='instruction + input的最大长度')
    parser.add_argument('--max_output_length', type=int, default=1536, help='output的最大长度')
    parser.add_argument('--lora_rank', type=int, default=4, help='lora rank')
    parser.add_argument('--lora_alpha', type=int, default=32, help='lora_alpha')
    parser.add_argument('--lora_dropout', type=float, default=0.05, help='lora dropout')
    parser.add_argument('--resume_from_checkpoint', type=str, default=None, help='恢复训练的checkpoint路径')
    parser.add_argument('--prompt_text', type=str, default='', help='统一添加在所有数据前的指令文本')
    parser.add_argument('--compute_dtype', type=str, default='fp32',
                        choices=['fp32', 'fp16', 'bf16'], help='计算数据类型')
    parser.add_argument("--local_rank", type=int, default=1)
    parser.add_argument("--cache_dir", type=str, default=None)
    return parser.parse_args()


class SupervisedDataset(Dataset):
    """Dataset for supervised fine-tuning."""

    def __init__(
        self,
        data_path,
        tokenizer,
        model_max_length,
        user_tokens=[195],
        assistant_tokens=[196],
    ):
        super(SupervisedDataset, self).__init__()
        self.data = json.load(open(data_path))
        self.tokenizer = tokenizer
        self.model_max_length = model_max_length
        self.user_tokens = user_tokens
        self.assistant_tokens = assistant_tokens
        self.ignore_index = -100
        item = self.preprocessing(self.data[0])
        # print("input:", self.tokenizer.decode(item["input_ids"]))
        labels = []
        for id_ in item["labels"]:
            if id_ == -100:
                continue

            labels.append(id_)
        print("label:", self.tokenizer.decode(labels))

    def __len__(self):
        return len(self.data)

    def preprocessing(self, example):
        input_ids = []
        labels = []

        for message in example:
            human_value = message['Human']
            model_value = message['Model']
            # from_ = message["from"]
            # value = message["value"]

            human_value_ids = self.tokenizer.encode(human_value)
            model_value_ids = self.tokenizer.encode(model_value)

            # value_ids = self.tokenizer.encode(value)
            #
            # if from_ == "human":
            #     input_ids += self.user_tokens + value_ids
            #     labels += [self.tokenizer.eos_token_id] + [self.ignore_index] * len(
            #         value_ids
            #     )
            # else:
            #     input_ids += self.assistant_tokens + value_ids
            #     labels += [self.ignore_index] + value_ids

            #处理人的说话
            input_ids += self.user_tokens + human_value_ids
            labels += [self.tokenizer.eos_token_id] + [self.ignore_index] * len(human_value_ids)

            #处理机器说话
            input_ids += self.assistant_tokens + model_value_ids
            labels += [self.ignore_index] + model_value_ids


        input_ids.append(self.tokenizer.eos_token_id)
        labels.append(self.tokenizer.eos_token_id)
        input_ids = input_ids[: self.model_max_length]
        labels = labels[: self.model_max_length]
        input_ids += [self.tokenizer.pad_token_id] * (
            self.model_max_length - len(input_ids)
        )
        labels += [self.ignore_index] * (self.model_max_length - len(labels))
        input_ids = torch.LongTensor(input_ids)
        labels = torch.LongTensor(labels)
        attention_mask = input_ids.ne(self.tokenizer.pad_token_id)
        return {
            "input_ids": input_ids,
            "labels": labels,
            "attention_mask": attention_mask,
        }

    def __getitem__(self, idx) -> Dict[str, torch.Tensor]:
        return self.preprocessing(self.data[idx])

class MyLoraTrainer(Trainer):
    def save_model(self, output_dir: Optional[str] = None, _internal_call: bool = False):
        """只保存adapter"""
        if output_dir is None:
            output_dir = self.args.output_dir
        self.model.save_pretrained(output_dir)
        torch.save(self.args, os.path.join(output_dir, "training_args.bin"))

def train(global_args):

    hf_parser = HfArgumentParser(TrainingArguments)

    hf_train_args, = hf_parser.parse_json_file(json_file=global_args.train_args_json)

    model = transformers.AutoModelForCausalLM.from_pretrained(
        global_args.model_name_or_path,
        trust_remote_code=True,
        cache_dir=global_args.cache_dir,
    )
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        global_args.model_name_or_path,
        use_fast=False,
        trust_remote_code=True,
        model_max_length=4096,
        cache_dir=global_args.cache_dir,
    )


    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        target_modules=["W_pack"],
        inference_mode=False,
        r=global_args.lora_rank,
        lora_alpha=global_args.lora_alpha,
        lora_dropout=0.1,
    )
    model.enable_input_require_grads()
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()
    dataset = SupervisedDataset(
        global_args.train_data_path, tokenizer, 1000
    )
    trainer = MyLoraTrainer(
        model=model, args=hf_train_args, train_dataset=dataset, tokenizer=tokenizer
    )
    trainer.train()
    trainer.model.save_pretrained(hf_train_args.output_dir)


if __name__ == "__main__":
    # mode_p = '/T53/temp/bigmodle/baichuan'
    # tokenizer = AutoTokenizer.from_pretrained(mode_p, use_fast=False, trust_remote_code=True)
    # dataset = SupervisedDataset(
    #     './data/dialogue_data.json', tokenizer, 4000
    # )
    pa = parse_args()
    train(pa)