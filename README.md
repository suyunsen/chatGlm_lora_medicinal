# chatGlm_lora_medicinal
使用lora在医药领域的数据集上微雕chatglm，得到一个医疗问答机器人


--train_args_json chatGLM_6B_QLoRA.json \
--model_name_or_path /T53/temp/bigmodle/chat_c \
--train_data_path /T53/temp/bigmodle/datas/ChatMed_Consult-v0.3.json \
--eval_data_path /T53/temp/bigmodle/datas/test.json \
--lora_rank 4 \
--lora_dropout 0.05 \
--compute_dtype bf16 \


deepspeed启动：
deepspeed --num_gpus=5 main.py  \
--train_args_json chatGLM_6B_QLoRA.json \
--model_name_or_path /T53/temp/bigmodle/chat_c \
--train_data_path /T53/temp/bigmodle/datas/ChatMed_Consult-v0.3.json \
--eval_data_path /T53/temp/bigmodle/datas/test.json \
--lora_dropout 0.05 \
--compute_dtype bf16 

--num_gpus=5

deepspeed --exclude="localhost:0,2" baichuanfinetune.py  \
--train_args_json Baichuan_conf.json \
--model_name_or_path /T53/temp/bigmodel/models/baichuan \
--train_data_path /T53/temp/bigmodel/chatGlm_lora_medicinal/data/test_all.json \
--lora_dropout 0.05 \
--compute_dtype bf16 

