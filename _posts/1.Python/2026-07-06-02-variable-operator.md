---
title: 변수와 연산자
description: Python의 기본 문법, 변수, 연산자, 데이터 타입, 입출력 정리
date: 2026-07-06
series: Python
tags:
  - Python
  - AutoEver SW School
---

> Python의 기본 문법, 데이터 타입, 변수, 연산자, 입출력을 학습한다.

---

#Python #Variable #Operator #DataType

## 학습 목표

- Python 기본 문법 이해
- 데이터 타입 이해
- 변수 생성 및 사용
- 연산자 활용
- 콘솔 입출력
- 자료형 변환

---

# Python 기본 문법

## Python 구성 요소

|구성 요소|설명|
|---|---|
|Literal|직접 입력한 값|
|Variable|데이터를 저장하는 이름|
|Function|재사용 가능한 기능|
|Class|데이터와 기능을 묶은 설계도|
|Object|클래스로 생성된 실제 객체|
|Module|Python 파일 하나|
|Package|여러 모듈의 집합|
|Comment|실행되지 않는 설명|

---

## Python 문법 특징

- 문장 끝에 `;`는 생략 가능
- 코드 블록은 **들여쓰기**로 구분
- 블록 시작에는 `:` 사용
- 표준 들여쓰기는 공백 4칸

예시

```python
if score >= 60:
    print("Pass")
else:
    print("Fail")
```

---

# 주석(Comment)

## 한 줄 주석

```python
# Comment
```

---

## 여러 줄 문자열

```python
"""
여러 줄 문자열
"""
```

> 엄밀히는 주석이 아니라 여러 줄 문자열이다.

---

# 도움말 확인

사용 가능한 메서드

```python
dir(100)
```

도움말

```python
help(print)
```

---

# 예약어(Keyword)

예약어는 변수명으로 사용할 수 없다.

예시

```python
if
for
while
class
def
return
True
False
None
```

확인

```python
import keyword

print(keyword.kwlist)
```

---

# Python 데이터 타입

## 데이터 분류

```text
Data
├── Scalar
└── Container
```

---

## Scalar

|자료형|예시|
|---|---|
|int|10|
|float|3.14|
|complex|3+4j|
|bool|True|

---

## Container

|자료형|특징|
|---|---|
|string|문자열|
|list|순서 O, 변경 O|

### 제어문자 (Escape Sequence)

`\` 다음에 하나의 영문자를 추가하여 특별한 의미를 부여한 문자

| 제어문자 | 의미 |
|---------|------|
| `\n` | 줄 바꿈 |
| `\t` | 탭 |
| `\0` | null |
|tuple|순서 O, 변경 X|
|set|중복 X|
|dict|Key-Value|

---

### Iterator

데이터를 **순차적으로 접근할 수 있도록 해주는 포인터**

- `__iter__` 메서드가 있으면 iterator로 간주
- `for` 문을 사용할 수 있는 객체는 iterator 기반으로 동작

```python
for item in [1, 2, 3]:
    print(item)
# 내부적으로 iterator를 생성하여 순차 접근
```

---

## None

값이 존재하지 않음을 의미

```python
value = None
```

---

# Literal

Literal은 코드에 직접 작성한 값이다.

```python
10
3.14
True
"Python"
[1,2,3]
```

---

# 식별자(Identifier)

## 규칙

가능

```text
name
_name
student1
```

불가능

```text
1name
if
@temp
```

규칙

- 문자 또는 `_`로 시작
- 숫자로 시작 불가
- 특수문자 사용 불가
- 예약어 사용 불가
- 대소문자 구분

---

# 변수(Variable)

## 변수란?

데이터를 저장하기 위한 이름

```python
score = 100
name = "Kim"
```

Python은 자료형을 자동 결정한다.

---

## 여러 변수 생성

```python
x, y, z = 10, 20, 30
```

---

## 변수 삭제

```python
del score
```

---

## 변수 주의사항

예약어 사용 금지

```python
# 오류
if = 10
```

내장 함수 이름 사용 지양

```python
abs = 10

# 이후 abs() 사용 불가
```

---

# 연산자

## 할당 연산자

```python
=
```

---

## 산술 연산자

|연산자|설명|
|---|---|
|+|덧셈 / 문자열 연결|
|-|뺄셈|
|*|곱셈 / 문자열 반복|
|/|나눗셈|
|//|몫|
|%|나머지|
|**|거듭제곱|

예시

```python
11 / 2
# 5.5

11 // 2
# 5

11 % 2
# 1

2 ** 3
# 8
```

---

## % 연산자의 활용

반복되는 패턴 생성

```python
i % 4
```

대표 활용

- 요일 계산
- 순환 메뉴
- 색상 반복
- 배열 인덱스

---

# 비교 연산자

|연산자|의미|
|---|---|
|>|크다|
|<|작다|
|>=|이상|
|<=|이하|
|==|같다|
|!=|다르다|

결과는 항상

```python
True
False
```

---

# 비트 연산자

|연산자|설명|
|---|---|
|&|AND|
|\||OR|
|^|XOR|
|~|NOT|
|<<|왼쪽 이동|
|>>|오른쪽 이동|

> 비트 연산은 시스템 프로그래밍이나 성능 최적화에서 주로 사용된다.

---

# 논리 연산자

|연산자|설명|
|---|---|
|and|모두 True|
|or|하나만 True|
|not|반전|

예시

```python
age >= 20 and age < 30
```

---

## Short Circuit

```python
False and func()
```

→ `func()`는 실행되지 않는다.

```python
True or func()
```

→ `func()`는 실행되지 않는다.

---

# all() / any()

모두 참

```python
all([True, True, True])
```

하나라도 참

```python
any([False, False, True])
```

---

# 복합 대입 연산자

```python
+=
-=
*=
/=
%=
**=
//=
```

예시

```python
count += 1
```

---

# type() / id()

자료형 확인

```python
type(a)
```

객체 주소 확인

```python
id(a)
```

---

# 자료형 변환

## int

```python
int(3.8)
int("10")
```

---

## float

```python
float("3.14")
```

---

## bool

```python
bool(1)
bool(0)
```

결과

```python
True
False
```

---

## str

```python
str(100)
```

---

# Bool 특징

```python
True == 1
False == 0
```

따라서

```python
True + True
```

결과

```python
2
```

## Truthy / Falsy

숫자 중에서 **0이 아닌 값은 `True`**로 간주하고, **0은 `False`**로 간주한다.

```python
bool(1)    # True
bool(-1)   # True
bool(0)    # False
```

컨테이너(문자열, 리스트 등)는 **데이터가 있으면 `True`**, **비어 있거나 `None`이면 `False`**로 간주한다.

```python
bool("hello")  # True
bool("")       # False
bool([1, 2])   # True
bool([])       # False
bool(None)     # False
```

이 특성은 조건문에서 자주 활용된다.

```python
if name:         # name이 비어있지 않으면 True
    print(name)
```

---

# 콘솔 출력

기본

```python
print("Hello")
```

---

줄바꿈 제거

```python
print("A", end="")
```

---

구분자 변경

```python
print(1,2,3, sep="-")
```

---

# 문자열 포맷팅

## % Formatting

```python
print("%d" % 10)
```

---

## format()

```python
print("{} {}".format(name, age))
```

---

## f-string (권장)

```python
print(f"{name} {age}")
```

Python 3.6 이상에서는 가장 많이 사용하는 방식이다.

---

# 콘솔 입력

문자열

```python
name = input("이름:")
```

정수

```python
age = int(input("나이:"))
```

---

## 여러 값 입력

공백 기준

```python
x, y, z = input().split()
```

쉼표 기준

```python
x, y, z = input().split(",")
```

---

# Computational Thinking

문제 해결 과정

```text
문제
 ↓
분해
 ↓
패턴 인식
 ↓
추상화
 ↓
알고리즘
 ↓
프로그램
```

---

# 핵심 암기

- Python은 들여쓰기로 블록을 구분한다.
- 예약어는 변수명이 될 수 없다.
- Python은 동적 타이핑 언어이다.
- `%`는 나머지뿐 아니라 반복 패턴 구현에 자주 사용된다.
- `//`는 몫을 반환한다.
- `and`, `or`는 Short Circuit을 수행한다.
- `type()`은 자료형 확인, `id()`는 객체 식별값 확인에 사용한다.
- 문자열 포맷팅은 f-string이 가장 권장된다.
- `input()`은 항상 문자열을 반환한다.
- 필요한 경우 `int()`, `float()` 등으로 형변환해야 한다.

---

# 한 페이지 요약

```text
Literal
      ↓
Variable
      ↓
Data Type
      ↓
Operator
      ↓
Input / Output
      ↓
Type Conversion
      ↓
Algorithm Thinking
```