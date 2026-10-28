# pip install openai
from openai import OpenAI

# 1. LM Studio 로컬 서버 연결
client = OpenAI(
    base_url="http://localhost:1235/v1",
    api_key="lm-studio"
)

# 2. 사용 가능한 모델 확인
models = client.models.list()

if not models.data:
    raise RuntimeError("사용 가능한 모델이 없습니다.")

# 3. 첫 번째 모델 선택
model_id = models.data[0].id
print(f"사용 모델: {model_id}")

# 4. 사용자 질문 입력
user_input = input("질문을 입력하세요: ")

# 5. AI 모델에 질문 전달
response = client.chat.completions.create(
    model=model_id,
    messages=[
        {
            "role": "system",
            "content": "당신은 친절한 한국어 AI 어시스턴트입니다."
        },
        {
            "role": "user",
            "content": user_input
        }
    ],
    temperature=0.7
)

# 6. AI 응답 출력
print("\nAI 응답:")
print(response.choices[0].message.content)