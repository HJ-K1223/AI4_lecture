class PromptEmptyError(Exception):
    pass

prompt = " "
try:
    if not prompt.strip():
        raise PromptEmptyError()
    
except PromptEmptyError as e:
    print('프롬프트는 반드시 제공되어야 합니다')

print('정상 종료')

class AgeOverError(Exception):
    pass

for i in range(5):
    try:
        age = int(input("나이를 입력하세요 : "))
        if age > 100 or age <0:
            raise AgeOverError()
    except AgeOverError as e:
        print("나이에 맞는 숫자를 입력하세요")
    except Exception as e:
        print("숫자를 입력하세요")
    else:
        print(f"당신의 나이는 {age}세입니다.")
    break


