---
title: 예외 처리
description: Python의 오류 종류, try-except, 예외 처리 구문 정리
date: 2026-07-09
series: Python
tags:
  - Python
  - AutoEverSW
---

## 1) 오류와 예외
---
### 구문 오류 (Syntax Error)
- 문법 자체가 잘못되어 프로그램 실행 자체가 불가능

### 예외 (Exception)
- 실행 중에 발생하는 오류
- 예외 처리를 통해 프로그램이 비정상 종료되는 것을 방지

## 2) try - except
---
```python
try:
    실행 코드
except 예외종류 as 변수:
    예외 발생 시 처리 코드
else:
    예외가 발생하지 않으면 실행
finally:
    항상 실행 (리소스 정리 등)
```

## 3) 주요 예외 종류
---

| 예외                  | 설명        |
| ------------------- | --------- |
| `ValueError`        | 부적절한 값    |
| `TypeError`         | 타입 불일치    |
| `IndexError`        | 인덱스 범위 초과 |
| `KeyError`          | 딕셔너리 키 없음 |
| `FileNotFoundError` | 파일 없음     |
| `ZeroDivisionError` | 0으로 나눔    |
| `AttributeError`    | 속성 없음     |
| `ImportError`       | 모듈 임포트 실패 |

## 4) raise
---
강제로 예외 발생
```python
raise ValueError("사용자 정의 에러 메시지")
```

## 5) 사용자 정의 예외
---
```python
class MyError(Exception):
    def __init__(self, msg):
        self.msg = msg

raise MyError("사용자 정의 예외")
```