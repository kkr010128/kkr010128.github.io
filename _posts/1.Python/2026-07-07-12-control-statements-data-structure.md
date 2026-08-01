---
title: 제어문과 자료구조
description: Python 메모리 구조, 제어문, 자료구조 심화 정리
date: 2026-07-07
series: Python
tags:
  - Python
  - AutoEver SW School
---

# 메모리 구조

## Stack

- 지역 변수(Local Variable)가 저장되는 영역임.
- 함수가 호출되면 생성되고, 함수가 종료되면 자동으로 제거됨.
- 컴파일 시 크기가 결정되는 데이터가 저장됨.
- LIFO(Last In First Out) 구조임.

## Heap

- 동적으로 생성한 객체가 저장되는 영역임.
- 개발자가 직접 생성하는 메모리 영역임.
- Python에서는 GC(Garbage Collector)가 사용하지 않는 객체를 자동으로 제거함.
- Java에서는 Garbage Collector가 관리함.
- C에서는 `malloc()`으로 생성하고 `free()`로 직접 해제해야 함.

## Instance

- Heap 영역에 생성된 객체(인스턴스)를 의미함.

## Literal / Class

- 문자열 리터럴, 클래스 정보 등이 저장되는 영역임.
- 프로그램 실행 중 변경되지 않는 데이터가 저장됨.
- Static 영역이라고도 함.

---

# 연산자

- 연산자는 우선순위를 가짐.
- 괄호 `()`를 사용하면 우선순위를 변경할 수 있음.

---

# 자료형 변환(Type Casting)

## 개요

- 데이터의 자료형을 다른 자료형으로 변경하는 것임.
- 변환 가능한 경우 자동 또는 명시적으로 변환됨.
- 변환이 불가능하면 오류가 발생함.

## 특징

- 실수를 정수로 변환하면 소수 부분이 제거됨.

```python
int(3.9)
# 3
```

- bool을 숫자로 변환하면

```python
True  -> 1
False -> 0
```

---

# 제어문(Control Statement)

## 개요

- 프로그램의 실행 흐름을 제어하는 명령문임.

---

# 분기문(Selection)

## if / elif / else

```python
if score >= 90:
    print("A")
elif score >= 80:
    print("B")
else:
    print("F")
```

---

## match (Python 3.10 이상)

- Java의 switch와 유사한 문법임.
- Python 3.10 이상에서만 지원됨.

```python
weekday = 2

match weekday:
    case 0:
        print("일요일")
    case 1:
        print("월요일")
    case 2:
        print("화요일")
    case _:
        print("기타")
```

---

## 삼항 연산자

```python
b = True if a > 20 else False
```

Java

```java
boolean b = (a > 20) ? true : false;
```

---

# 반복문

## while

```python
var = 1

while var < 4:
    print(var)
    var += 1
```

- 조건이 False가 될 때까지 반복 수행함.

---

## for

기본 문법

```python
for 변수 in iterable:
    실행문
```

예시

```python
for x in ["excel1", "excel2", "excel3"]:
    print(x)
```

- iterable의 데이터를 하나씩 꺼내 변수에 저장하면서 반복 수행함.
- 변수를 사용하지 않으면 `_`를 사용함.

```python
for _ in range(5):
    print("Hello")
```

---

# range()

## 문법

```python
range(start, stop, step)
```

### 특징

- start 생략 가능
- step 생략 가능
- stop은 포함하지 않음.

예시

```python
range(10)
```

↓

```text
0 ~ 9
```

예시

```python
range(1, 10)
```

↓

```text
1 ~ 9
```

예시

```python
range(10, 0, -1)
```

↓

```text
10 9 8 7 ... 1
```

---

# break

- 반복문을 즉시 종료함.

```python
for i in range(10):
    if i == 5:
        break
```

---

# continue

- 현재 반복만 종료하고 다음 반복을 수행함.

```python
for i in range(5):
    if i == 2:
        continue
    print(i)
```

출력

```text
0
1
3
4
```

---

# Python의 for / while + else

Python에서는 반복문 뒤에 else를 사용할 수 있음.

- `break` 없이 정상적으로 반복이 종료되면 else가 실행됨.
- `break`로 종료되면 else는 실행되지 않음.

예시

```python
for i in range(1, 10):
    print(i)

    if i % 3 == 0:
        break
else:
    print("정상 종료")
```

위 코드는 `break`가 발생하므로

```text
정상 종료
```

는 출력되지 않음.

반대로

```python
for i in range(3):
    print(i)
else:
    print("정상 종료")
```

출력

```text
0
1
2
정상 종료
```

---

# 반복문 중첩

- 반복문 안에 반복문을 사용할 수 있음.

```python
for i in range(3):
    for j in range(2):
        print(i, j)
```

---

# 실습 문제

## 1. 완전수(Perfect Number)

- 2부터 1000까지의 완전수 개수를 출력함.
- 완전수는 자신을 제외한 약수의 합이 자기 자신인 수임.

예시

```text
6

약수
1, 2, 3, 6

1 + 2 + 3 = 6
```

---

## 2. 윤년(Leap Year)

1년부터 2026년까지 윤년의 개수를 출력함.

윤년 조건

- 4의 배수이고 100의 배수가 아니면 윤년임.
- 또는 400의 배수이면 윤년임.

즉,

```python
(year % 4 == 0 and year % 100 != 0) or year % 400 == 0
```

---

## 3. 피보나치 수열

- n번째 피보나치 수를 구하는 프로그램 작성

피보나치 수열

```text
1 1 2 3 5 8 13 ...
```

---

# input()

- 사용자로부터 입력을 받는 함수임.
- 입력값은 항상 문자열(String)로 반환됨.

```python
age = input("나이를 입력하세요.")
```

숫자로 사용하려면 자료형 변환이 필요함.

```python
age = int(input("나이를 입력하세요."))
```