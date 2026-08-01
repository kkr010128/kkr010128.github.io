---
title: 예외 처리
description: Python의 오류 종류, try-except, 예외 처리 구문 정리
date: 2026-07-09
series: Python
tags:
  - Python
  - AutoEver SW School
---

> Python의 예외(Exception), 예외 처리(Exception Handling), Assertion, 사용자 정의 예외를 학습한다.

---

#Python #Exception #ExceptionHandling #Debugging #Assertion

## 학습 목표

- 오류와 예외 이해
- try-except
- else와 finally
- raise
- assert
- 사용자 정의 예외

---

# 오류(Error)

## 오류 종류

|종류|설명|
|---|---|
|Compile Error|문법 오류로 실행 불가|
|Exception|실행 중 발생하는 오류|
|Logical Error|실행은 되지만 결과가 잘못됨|
|Assertion|조건을 만족하지 않으면 강제로 오류 발생|

---

## Debugging

오류의 원인을 찾고 수정하는 과정

대표 방법

- Logging
- IDE Debugger
- 로그 파일 분석
- 테스트 코드 작성

---

# 예외(Exception)

## 예외란?

문법에는 문제가 없지만 **프로그램 실행 중(Runtime)** 발생하는 오류이다.

대표 예외

- 0으로 나누기
- 존재하지 않는 파일
- Index 범위 초과
- 잘못된 형 변환
- Dictionary Key 없음

---

## 예외 발생 예

```python
def divide(x):
    return 10 / x

print(divide(2))
print(divide(0))
```

↓

```text
ZeroDivisionError
```

---

# 예외 처리(Exception Handling)

## 기본 구조

```python
try:
    실행 코드
except:
    예외 처리
```

---

## 예제

```python
try:
    x = int(input())
    print(10 / x)

except:
    print("예외 발생")
```

---

# 특정 예외 처리

특정 예외만 처리할 수 있다.

```python
try:
    ...
except ZeroDivisionError:
    ...
```

---

## 여러 예외 처리

```python
try:
    ...
except ZeroDivisionError:
    ...

except IndexError:
    ...

except ValueError:
    ...
```

---

# 예외 객체 받기

오류 메시지를 확인할 수 있다.

```python
try:
    ...

except ZeroDivisionError as e:
    print(e)
```

---

# 예외 클래스

대표 예외

|예외|설명|
|---|---|
|Exception|최상위 예외|
|ZeroDivisionError|0으로 나누기|
|IndexError|Index 범위 초과|
|KeyError|없는 Key 접근|
|TypeError|자료형 오류|
|ValueError|잘못된 값|
|AttributeError|속성 없음|
|FileNotFoundError|파일 없음|
|ImportError|모듈 오류|

---

# else

예외가 발생하지 않았을 때만 실행된다.

```python
try:
    result = 10 / 2

except ZeroDivisionError:
    print("Error")

else:
    print(result)
```

---

# finally

예외 발생 여부와 관계없이 항상 실행된다.

```python
try:
    ...

except:
    ...

finally:
    print("Finish")
```

주요 용도

- 파일 닫기
- DB 연결 종료
- Socket 종료
- 자원 해제

---

# 전체 구조

```python
try:
    실행 코드

except Exception:
    예외 처리

else:
    정상 처리

finally:
    항상 실행
```

---

# raise

예외를 직접 발생시킨다.

```python
raise Exception("Error")
```

---

## 조건 검사

```python
x = int(input())

if x % 3 != 0:
    raise Exception("3의 배수가 아닙니다.")
```

---

# 예외 다시 발생(Re-raise)

현재 예외를 상위로 전달

```python
try:
    ...

except Exception:
    raise
```

---

# Assertion

프로그램의 조건을 검증한다.

```python
assert 조건식
```

또는

```python
assert 조건식, "오류 메시지"
```

예

```python
assert x % 3 == 0, "3의 배수가 아닙니다."
```

조건이 거짓이면

```text
AssertionError
```

발생

---

# 사용자 정의 예외(Custom Exception)

Exception을 상속하여 생성한다.

```python
class NotThreeMultipleError(Exception):

    def __init__(self):
        super().__init__("3의 배수가 아닙니다.")
```

---

## 사용자 정의 예외 발생

```python
raise NotThreeMultipleError()
```

---

## 처리

```python
try:
    ...

except NotThreeMultipleError as e:
    print(e)
```

---

# 예외 처리 흐름

```text
프로그램 실행
        │
        ▼
     try 실행
        │
        ├──────────────┐
        │              │
   예외 없음        예외 발생
        │              │
        ▼              ▼
      else         except
        │              │
        └──────┬───────┘
               ▼
           finally
               ▼
           프로그램 종료
```

---

# 예외 처리 원칙

- 예외가 발생할 가능성이 있는 코드만 `try`에 작성한다.
- `except:`만 사용하는 것보다 구체적인 예외 클래스를 사용한다.
- 필요한 경우 `as`로 예외 객체를 받아 메시지를 확인한다.
- 자원 해제는 `finally`에서 수행한다.
- 의도적인 오류는 `raise`를 사용한다.
- 프로그램의 전제 조건 검사는 `assert`를 사용한다.
- 비즈니스 로직에는 사용자 정의 예외를 사용하는 것이 좋다.

---

# 핵심 암기

- Compile Error : 문법 오류
- Exception : 실행 중 오류
- Logical Error : 논리 오류
- `try` : 예외 감시
- `except` : 예외 처리
- `else` : 예외가 없을 때 실행
- `finally` : 항상 실행
- `raise` : 예외 발생
- `raise` : 현재 예외 재전파
- `assert` : 조건 검증
- `Exception`을 상속하면 사용자 정의 예외를 만들 수 있다.

---

# 한 페이지 요약

```text
Exception Handling
│
├── Error
│   ├── Compile Error
│   ├── Exception
│   ├── Logical Error
│   └── Assertion
│
├── try
├── except
├── else
├── finally
│
├── raise
├── assert
│
└── Custom Exception
    └── Exception Inheritance
```

