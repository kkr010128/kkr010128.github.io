---
title: 제어문
description: Python의 조건문(if, match-case)과 반복문(while, for) 및 break/continue 정리
date: 2026-07-07
series: Python
tags:
  - Python
  - AutoEver SW School
---

> 프로그램의 실행 흐름을 제어하는 조건문과 반복문을 학습한다.

---

#Python #ControlStatement #Conditional #Loop

## 학습 목표

- 제어문의 개념 이해
- if 문 활용
- while, for 반복문 이해
- range() 활용
- break, continue 사용법
- 중첩 반복문 작성

---

## 제어문(Control Statement)

### 제어문이란?

프로그램은 기본적으로 **위에서 아래로 순차 실행**된다.

제어문은 이러한 실행 흐름을 변경하는 문법이다.

```text
순차 실행
      ↓
조건 판단(if)
      ↓
반복 수행(while, for)
      ↓
프로그램 종료
```

---

## 코드 블록(Block)

Python은 `{}` 대신 **들여쓰기**로 블록을 구분한다.

규칙

- 공백 4칸 권장
- 같은 블록은 같은 깊이
- 탭과 공백 혼용 금지

예시

```python
if score >= 60:
    print("Pass")
```

---

# 조건문(Conditional Statement)

## if

조건이 True일 때만 실행한다.

```python
if 조건식:
    실행문
```

---

### True로 판단되는 값

```python
True
1
-10
[1]
"Python"
```

---

### False로 판단되는 값

```python
False
0
0.0
None
[]
()
{}
''
```

---

## if - else

조건에 따라 두 가지 실행 경로를 만든다.

```python
if 조건:
    실행문
else:
    실행문
```

예시

```python
score = int(input())

if score >= 60:
    print("합격")
else:
    print("불합격")
```

---

## 삼항 연산식

한 줄로 조건식을 작성할 수 있다.

```python
result = True if score >= 60 else False
```

---

## if - elif - else

여러 조건을 순차적으로 검사한다.

```python
if 조건1:
    ...

elif 조건2:
    ...

elif 조건3:
    ...

else:
    ...
```

예시

```python
if score >= 90:
    print("수")
elif score >= 80:
    print("우")
elif score >= 70:
    print("미")
elif score >= 60:
    print("양")
else:
    print("가")
```

---

## switch 대체 방법

### Dictionary 사용

```python
menu = {
    1: "Americano",
    2: "Cafe Latte",
    3: "Espresso"
}

print(menu.get(2))
```

---

### match-case (Python 3.10+)

```python
match menu:
    case 1:
        print("Americano")
    case 2:
        print("Cafe Latte")
    case _:
        print("Unknown")
```

> Python 3.10 이상에서는 `match-case`가 switch 문법 역할을 수행한다.

---

# 반복문(Loop)

## while

조건이 True인 동안 반복한다.

```python
while 조건:
    실행문
```

---

예시

```python
count = 0

while count < 5:
    print(count)
    count += 1
```

---

## while else

반복문이 **정상 종료**되었을 때만 else가 실행된다.

```python
while 조건:
    ...
else:
    print("정상 종료")
```

> `break`로 종료되면 else는 실행되지 않는다.

---

## 무한 반복

```python
while True:
    ...
```

종료는 일반적으로

```python
break
```

를 사용한다.

---

# for 반복문

순회 가능한(iterable) 객체를 반복한다.

```python
for 변수 in 반복가능객체:
    실행문
```

예시

```python
for i in [1,2,3]:
    print(i)
```

---

## for else

```python
for item in data:
    ...
else:
    print("정상 종료")
```

역시 `break`가 발생하지 않을 때만 else가 실행된다.

---

# range()

### 기본 형태

```python
range(stop)
range(start, stop)
range(start, stop, step)
```

---

예시

```python
range(5)

# 0 1 2 3 4
```

```python
range(5,10)

# 5 6 7 8 9
```

```python
range(10,0,-1)

# 10 9 8 ... 1
```

---

짝수 출력

```python
for i in range(0,20,2):
    print(i)
```

---

# 중첩 반복문

## 구구단

```python
for x in range(2,10):
    for y in range(1,10):
        print(f"{x} x {y} = {x*y}")
```

---

## 별 출력

사각형

```text
*****
*****
*****
*****
*****
```

삼각형

```text
*
**
***
****
*****
```

피라미드

```text
    *
   ***
  *****
 *******
*********
```

---

# 반복 제어

## continue

현재 반복만 건너뛰고 다음 반복 수행

```python
for i in range(10):

    if i % 2:
        continue

    print(i)
```

결과

```text
0
2
4
6
8
```

---

## break

반복문 즉시 종료

```python
while True:

    if count == 100:
        break
```

---

## break와 else

```python
for i in range(5):

    if i == 3:
        break

else:
    print("정상 종료")
```

break가 발생했으므로

```
else는 실행되지 않는다.
```

---

# 조건문 작성 팁

좋지 않은 예

```python
if score >= 80 and score <= 100:
```

더 좋은 표현

```python
if 80 <= score <= 100:
```

Python에서는 비교 연산을 연결해서 작성할 수 있다.

---

# 반복문 선택 기준

|반복문|사용 상황|
|---|---|
|while|반복 횟수를 모를 때|
|for|반복 횟수를 알 때|
|range()|숫자 반복|
|for + iterable|리스트, 문자열 등 순회|

---

# 알고리즘 사고(Computational Thinking)

문제를 해결하는 과정

```text
문제 분석
      ↓
분해
      ↓
패턴 인식
      ↓
추상화
      ↓
알고리즘 작성
      ↓
코드 구현
```

---

# 실습 예제

대표 예제

- 합격/불합격 판정
- 메뉴 선택
- 윤년 계산
- 교통카드 요금 계산
- 구구단 출력
- 별 출력
- 뉴스 URL 생성
- 피보나치 수열
- 소수 판별
- 완전수 찾기

---

# 핵심 암기

- Python은 들여쓰기로 블록을 구분한다.
- `if`는 조건이 참일 때만 실행된다.
- `elif`는 여러 조건을 처리한다.
- Python 3.10부터 `match-case`를 지원한다.
- `while`은 조건 기반 반복이다.
- `for`는 순회 기반 반복이다.
- `range()`의 종료값은 포함되지 않는다.
- `break`는 반복 종료, `continue`는 다음 반복으로 이동한다.
- 반복문의 `else`는 `break` 없이 종료될 때만 실행된다.
- 중첩 반복문은 2차원 구조를 처리할 때 자주 사용된다.

---

# 한 페이지 요약

```text
Control Statement
        │
        ├── if
        ├── if-else
        ├── if-elif-else
        ├── match-case
        │
        ├── while
        ├── for
        ├── range()
        │
        ├── break
        ├── continue
        └── 중첩 반복문
```