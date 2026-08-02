---
title: 제어문
description: Python의 조건문(if, match-case)과 반복문(while, for) 및 break/continue 정리
date: 2026-07-07
series: Python
tags:
  - Python
  - AutoEverSW
---

## 1) 조건문
---
### if
조건이 **True**일 때만 실행

```python
if 조건식:
    실행문
```

### if - else
조건에 따라 두 가지 실행 경로

```python
if 조건:
    실행문
else:
    실행문
```

### if - elif - else
여러 조건을 순차적으로 검사

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

```python
score = int(input())
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

### 삼항 연산식
```python
result = True if score >= 60 else False
```

### True / False 판단

| True로 판단 | False로 판단 |
| ---------- | ----------- |
| `True`, `1`, `-10` | `False`, `0`, `0.0` |
| `[1]`, `"Python"` | `None`, `[]`, `()`, `{}`, `''` |

### switch 대체

**Dictionary 활용**
```python
menu = {1: "Americano", 2: "Cafe Latte", 3: "Espresso"}
print(menu.get(2))
```

**match - case (Python 3.10+)**
```python
match weekday:
    case 0:
        print("일요일")
    case 1:
        print("월요일")
    case _:
        print("요일 없음")
```

## 2) 반복문
---
### while
조건이 **True인 동안** 반복

```python
while 조건:
    실행문
```

예시
```python
count = 0
while count < 5:
    print(count)
    count += 1
```

**무한 반복**
```python
while True:
    ...
    if 조건:
        break
```

### for
**순회 가능한(iterable) 객체**를 반복

```python
for 변수 in 반복가능객체:
    실행문
```

예시
```python
for i in [1, 2, 3]:
    print(i)

for _ in range(3):
    print("반복")  # _는 값 무시
```

### range()
```python
range(stop)           # 0 ~ stop-1
range(start, stop)    # start ~ stop-1
range(start, stop, step)
```

```python
range(5)          # 0, 1, 2, 3, 4
range(5, 10)      # 5, 6, 7, 8, 9
range(10, 0, -1)  # 10, 9, ... 1
```

### while / for - else
반복문이 **정상 종료**되었을 때만 `else` 실행 (break 시 실행 안 됨)

```python
for i in range(5):
    if i == 3:
        break
else:
    print("정상 종료")  # break 발생으로 실행 안 됨
```

### 반복 제어

| 키워드 | 기능 |
| ------ | ---- |
| `break` | 반복문 즉시 종료 |
| `continue` | 현재 반복 건너뛰고 다음 반복으로 |

```python
for i in range(10):
    if i % 2:
        continue
    print(i)  # 0, 2, 4, 6, 8
```

### 조건문 작성 팁
Python은 비교 연산 연결 가능
```python
# 좋지 않음
if score >= 80 and score <= 100:

# 더 좋은 표현
if 80 <= score <= 100:
```

### 반복문 선택 기준

| 반복문 | 사용 상황 |
| ------ | -------- |
| `while` | 반복 횟수를 모를 때 |
| `for` | 반복 횟수를 알 때 |
| `range()` | 숫자 반복 |
| `for + iterable` | 리스트, 문자열 등 순회 |

## 3) 중첩 반복문
---
### 구구단
```python
for x in range(2, 10):
    for y in range(1, 10):
        print(f"{x} x {y} = {x*y}")
```

### 별 출력
```text
# 사각형
*****
*****

# 삼각형
*
**
***

# 피라미드
   *
  ***
 *****
```

## 4) 실습 예제
---
- 합격/불합격 판정
- 메뉴 선택
- **윤년 계산**: 4의 배수이고 100의 배수가 아닌 경우 또는 400의 배수인 경우
- **완전수**: 자신을 제외한 약수의 합이 자기 자신인 수 (예: 6)
- **피보나치 수열**: 첫 두 수는 1, 이후는 앞 두 수의 합
- 소수 판별, 구구단, 별 출력