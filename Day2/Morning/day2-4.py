user_score = 85
if user_score >= 80:
    grade = 'Pass'
else:
    grade = 'Fail'

# 삼항연산자 (위와 같은 코드지만 간단한 경우)
grade = 'Pass' if user_score >=80 else 'Fail'
print(grade)