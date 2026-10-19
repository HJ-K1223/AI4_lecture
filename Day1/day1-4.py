#구구단 만들기
# i=1
# print(f"2 x {i} = {2*i}")

# i=2
# print(f"2 x {i} = {2*i}")

# i=3
# print(f"2 x {i} = {2*i}")

# i=4
# print(f"2 x {i} = {2*i}")

# for dan in range(2,5):
#     for i in range(1,5):
#         print(f"{dan} x {i} = {dan*i}", end="\t")
#     print("\n===================")

for dan in range(1,5):
    for i in range(2,5):
        print(f"{i} x {dan} = {dan*i}", end="\t")
    print("\n===================")