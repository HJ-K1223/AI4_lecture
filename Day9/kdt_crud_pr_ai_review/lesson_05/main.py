def is_ready(value: str) -> bool:
    # return bool(value)
     return value.lower() == "true"

if __name__ == "__main__":
    print(is_ready("false"))
    