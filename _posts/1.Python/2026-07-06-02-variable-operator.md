---
title: 변수와 연산자
description: Python의 기본 문법, 변수, 연산자, 데이터 타입, 입출력 정리
date: 2026-07-06
series: Python
tags:
  - Python
  - AutoEverSW
---

## 1) Python 기본 문법
---
### Python 구성 요소

| 요소 | 설명 |
| ---- | ---- |
| **Literal** | 직접 입력한 값 |
| **Variable** | 데이터를 저장하는 이름 |
| **Function** | 재사용 가능한 기능 |
| **Class** | 데이터와 기능을 묶은 설계도 |
| **Object** | 클래스로 생성된 실제 객체 |
| **Module** | Python 파일 하나 |
| **Package** | 여러 모듈의 집합 |
| **Comment** | 실행되지 않는 설명 |

### 문법 특징
- 문장 끝 `;`는 생략 가능
- **들여쓰기**(공백 4칸 권장)로 코드 블록 구분
- 블록 시작에는 `:` 사용

```python
if score >= 60:
    print("Pass")
else:
    print("Fail")
```

## 2) 주석(Comment)
---
- 한 줄: `# 내용`
- 여러 줄: `""" 내용 """` 또는 `''' 내용 '''` (엄밀히는 여러 줄 문자열)

## 3) 도움말 확인
---
```python
dir(100)       # 사용 가능한 메서드 목록
help(print)    # 함수 도움말
```

## 4) 예약어(Keyword)
---
변수명으로 사용할 수 없는 Python 내장 명령어

```python
import keyword
print(keyword.kwlist)
```

## 5) 데이터 타입
---
### 분류
```text
Data
├── Scalar (단일 값)
└── Container (모음)
```

### Scalar

| 자료형 | 예시 |
| ----- | ---- |
| `int` | 10 |
| `float` | 3.14 |
| `complex` | 3+4j |
| `bool` | True |

### Container

| 자료형 | 특징 |
| ----- | ---- |
| `str` | 문자열, Immutable, Sequence |
| `list` | 순서 O, 변경 O (Mutable) |
| `tuple` | 순서 O, 변경 X (Immutable) |
| `set` | 중복 X, Mutable |
| `dict` | Key-Value, Mutable, Mapping |

### 제어문자 (Escape Sequence)

| 문자 | 의미 |
| ---- | ---- |
| `\n` | 줄 바꿈 |
| `\t` | 탭 |
| `\0` | null |

### Iterator
데이터를 **순차적으로 접근**할 수 있도록 해주는 포인터

- `__iter__` 메서드가 있으면 iterator로 간주
- `for` 문 사용 가능

```python
for item in [1, 2, 3]:
    print(item)
```

### None
값이 존재하지 않음을 의미

```python
value = None
```

### Literal
코드에 직접 작성한 값

```python
10, 3.14, True, "Python", [1,2,3]
```

## 6) 식별자(Identifier)
---
### 규칙
- 문자 또는 `_`로 시작
- 숫자로 시작 불가
- 특수문자 사용 불가
- 예약어 사용 불가
- 대소문자 구분

## 7) 변수(Variable)
---
### 생성과 사용
```python
score = 100          # 자료형 자동 결정
name = "Kim"
x, y, z = 10, 20, 30 # 여러 변수 한 번에
del score            # 변수 삭제
```

### 주의사항
- 예약어 사용 금지: `if = 10` → 오류
- 내장 함수 이름 사용 지양: `abs = 10` → 이후 `abs()` 사용 불가

## 8) 연산자
---
### 할당 연산자
```python
=
```

### 산술 연산자

| 연산자 | 설명 | 예시 |
| ----- | ---- | ---- |
| `+` | 덧셈 / 문자열 연결 | |
| `-` | 뺄셈 | |
| `*` | 곱셈 / 문자열 반복 | |
| `/` | 나눗셈 (실수) | `11 / 2` → `5.5` |
| `//` | 몫 | `11 // 2` → `5` |
| `%` | 나머지 | `11 % 2` → `1` |
| `**` | 거듭제곱 | `2 ** 3` → `8` |

`%` 연산은 반복 패턴 생성(요일 계산, 순환 메뉴 등)에 자주 활용됨

### 비교 연산자

| 연산자 | 의미 |
| ----- | ---- |
| `>` | 크다 |
| `<` | 작다 |
| `>=` | 이상 |
| `<=` | 이하 |
| `==` | 같다 (값 비교, `__eq__`) |
| `!=` | 다르다 |
| `is` | id 비교 (오버라이딩 불가) |

### 비트 연산자

| 연산자 | 설명 |
| ----- | ---- |
| `&` | AND (둘 다 1) |
| `\|` | OR (하나만 1) |
| `^` | XOR (서로 다름) |
| `~` | NOT (1의 보수) |
| `<<` | 왼쪽 시프트 (×2) |
| `>>` | 오른쪽 시프트 (÷2) |

> 시스템 프로그래밍이나 성능 최적화에서 주로 사용됨

### 논리 연산자

| 연산자 | 설명 |
| ----- | ---- |
| `and` | 모두 True |
| `or` | 하나만 True |
| `not` | 반전 |

**Short Circuit**: `False and func()` → `func()` 실행 안 됨, `True or func()` → `func()` 실행 안 됨

### 복합 대입 연산자
```python
+=  -=  *=  /=  %=  **=  //=
```

### type() / id()
```python
type(a)  # 자료형 확인
id(a)    # 객체 주소(식별값) 확인
```

## 9) 자료형 변환
---
```python
int(3.8)    # 3
int("10")   # 10
float("3.14")
bool(1)     # True
bool(0)     # False
str(100)    # "100"
```

### Bool 특징
```python
True == 1    # True
False == 0   # True
True + True  # 2
```

### Truthy / Falsy
- 숫자: **0이 아닌 값은 `True`**, **0은 `False`**
- 컨테이너: **데이터가 있으면 `True`**, **비어있거나 `None`이면 `False`**

```python
bool("hello")  # True
bool("")       # False
bool([1, 2])   # True
bool([])       # False
bool(None)     # False

if name:       # name이 비어있지 않으면 True
    print(name)
```

## 10) 콘솔 출력
---
```python
print("Hello")               # 기본
print("A", end="")           # 줄바꿈 제거
print(1, 2, 3, sep="-")      # 1-2-3
```

### 문자열 포맷팅
```python
# % Formatting
print("%d" % 10)

# format()
print("{} {}".format(name, age))

# f-string (권장, Python 3.6+)
print(f"{name} {age}")
```

## 11) 콘솔 입력
---
```python
name = input("이름:")         # 문자열
age = int(input("나이:"))     # 정수 변환
x, y, z = input().split()    # 공백 기준 분리
x, y, z = input().split(",") # 쉼표 기준 분리
```

> `input()`은 항상 문자열을 반환하므로 숫자는 `int()`, `float()` 등으로 형변환 필요