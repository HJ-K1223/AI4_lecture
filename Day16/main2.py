import os
from dotenv import load_dotenv

import requests
import streamlit as st

load_dotenv(override=True)
base_url = os.getenv('LLAMA_BASE_URL',"").strip()
model = os.getenv('LLAMA_MODEL',"")
timeout_text = int(os.getenv('LLAMA_TIMEOUT_SECONDS','180').strip())

name = st.text_input('이름')
question = st.text_input('질문')

with st.chat_message('user'):
    st.text(f'{name} : {question}')

if st.button('AI 답변 받기'):
    headers={}
    with st.spinner('AI가 답변을 생성하고 있습니다.'): # 동기
        with requests.post(
            f'{base_url}/v1/chat/completions', # 채팅 API 주소
            headers = headers,
            json = {
                'model': model, # 서버의 --alias와 일치해야함
                'messages' : [
                    {'role':'system', 'content':'한국어로 쉽고 간결하게 대답하는 에이전트'},
                    {'role':'user', 'content':question},
                ],
                "temperature":0.7, # 값은 0(최대한 추론 자제, 있는 것만) ~ 1(추론력 최대) 사이
                "max_tokens":512,
                "stream":False, # 토큰별 스트리밍 대신 json 응답 수신
            },
            timeout=(5,timeout_text)
        )as response:
            response.raise_for_status()
            data = response.json() # 객체로 복원
        choice = data['choices'][0]
        answer = choice['message']['content']
        with st.chat_message('assistant'):
            st.text(answer.strip())
