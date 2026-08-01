---
title: 모듈과 패키지
description: Python 모듈, 패키지, collections, itertools 등 내장 모듈 정리
date: 2026-07-09
series: Python
tags:
  - Python
  - AutoEver SW School
---

> Python에서 자주 사용하는 표준 라이브러리와 시스템 모듈, 멀티스레드, 네트워크 프로그래밍을 학습한다.

---

#Python #Module #Datetime #OS #Thread #Socket

## 학습 목표

- 날짜와 시간 처리
- Fraction
- 파일 시스템
- OS 및 System 모듈
- Copy
- Weak Reference
- Thread
- Socket Network

---

# 날짜와 시간(Date & Time)

## 시간 표현

|용어|설명|
|---|---|
|Timestamp|1970-01-01 00:00:00 UTC부터 경과한 시간|
|UTC|국제 표준시|
|GMT|그리니치 평균시|
|LST|지역 표준시|
|DST|일광 절약 시간제|

---

## struct_time

Timestamp를 사람이 읽기 쉬운 형태로 표현하는 객체

주요 속성

- tm_year
- tm_mon
- tm_mday
- tm_hour
- tm_min
- tm_sec
- tm_wday
- tm_yday
- tm_isdst

---

# time 모듈

```python
import time
```

주요 함수

|함수|설명|
|---|---|
|time()|Timestamp 반환|
|gmtime()|UTC 기준 시간|
|localtime()|로컬 시간|
|sleep()|일시 정지|
|asctime()|문자열 시간|

예

```python
import time

print(time.time())
print(time.localtime())
time.sleep(3)
```

---

# datetime 모듈

```python
import datetime
```

주요 클래스

- datetime
- date
- time
- timedelta
- tzinfo

---

## datetime 생성

```python
datetime.datetime.now()
```

현재 날짜와 시간

---

## 문자열 ↔ 날짜

문자열 → datetime

```python
datetime.datetime.strptime(
    "2024-01-01",
    "%Y-%m-%d"
)
```

datetime → 문자열

```python
dt.strftime("%Y-%m-%d")
```

---

## 날짜 연산

```python
from datetime import timedelta

today + timedelta(days=7)
```

날짜 차이

```python
dt2 - dt1
```

↓

```python
timedelta
```

---

## 날짜 포맷

|포맷|설명|
|---|---|
|%Y|4자리 연도|
|%y|2자리 연도|
|%m|월|
|%d|일|
|%H|24시간|
|%I|12시간|
|%M|분|
|%S|초|

---

# Fraction

```python
from fractions import Fraction
```

분수 표현

```python
Fraction(5,7)

Fraction("2/5")
```

지원

- 사칙연산
- floor
- ceil
- round

---

# 파일 시스템(File System)

## os.path

```python
import os.path
```

주요 함수

|함수|설명|
|---|---|
|abspath()|절대 경로|
|basename()|파일명|
|dirname()|디렉터리|
|exists()|존재 여부|
|join()|경로 연결|
|split()|경로 분리|
|splitext()|확장자 분리|

---

## 파일 정보

- getsize()
- getctime()
- getmtime()
- getatime()
- isfile()
- isdir()

---

# glob

파일 검색

```python
import glob
```

예

```python
glob.glob("*.py")
```

Iterator

```python
glob.iglob("*.py")
```

---

# os 모듈

```python
import os
```

주요 함수

|함수|설명|
|---|---|
|getcwd()|현재 디렉터리|
|chdir()|디렉터리 변경|
|listdir()|목록 조회|
|mkdir()|디렉터리 생성|
|makedirs()|재귀 생성|

---

## 환경 정보

- os.name
- os.environ
- os.getenv()
- os.getpid()
- os.system()

---

# sys 모듈

```python
import sys
```

주요 기능

- argv
- modules
- path
- prefix
- executable
- exit()
- getrefcount()
- getdefaultencoding()

---

# Copy

## 참조 복사

```python
a = [1,2,3]
b = a
```

같은 객체 참조

---

## 얕은 복사(Shallow Copy)

```python
import copy

b = copy.copy(a)
```

또는

```python
a[:]
```

특징

- 1단계만 복사
- 내부 객체는 공유

---

## 깊은 복사(Deep Copy)

```python
import copy

b = copy.deepcopy(a)
```

특징

- 모든 객체 재귀 복사
- 독립적인 객체 생성

---

# Weak Reference

```python
import weakref
```

특징

- 참조 횟수 증가 없음
- 메모리 누수 방지
- 객체가 제거되면 None 반환

생성

```python
ref = weakref.ref(obj)
```

---

# Thread

## 개념

|용어|설명|
|---|---|
|Process|독립 실행 프로그램|
|Thread|Process 내부 실행 단위|

---

## Thread 생성

```python
import threading
```

함수 기반

```python
threading.Thread(
    target=func,
    args=(arg,)
)
```

---

## 클래스 기반

```python
class MyThread(threading.Thread):

    def run(self):
        ...
```

---

## 실행

```python
th.start()
```

종료 대기

```python
th.join()
```

---

# Multi Thread

## 문제점

- Critical Section
- Race Condition
- Dead Lock
- Producer / Consumer

---

# Lock

```python
lock = threading.Lock()
```

획득

```python
lock.acquire()
```

반납

```python
lock.release()
```

---

# RLock

같은 Thread에서 여러 번 Lock 가능

```python
threading.RLock()
```

---

# Condition

생산자-소비자 문제 해결

주요 메서드

- wait()
- notify()

---

# Semaphore

동시에 실행 가능한 Thread 개수 제한

```python
threading.Semaphore(3)
```

메서드

- acquire()
- release()

---

# Network

## 기본 용어

|용어|설명|
|---|---|
|IP|장치 주소|
|Port|프로세스 번호|
|Protocol|통신 규칙|
|TCP|연결형|
|UDP|비연결형|
|Socket|통신 객체|

---

# socket

```python
import socket
```

서비스 포트

```python
socket.getservbyname(
    "http",
    "tcp"
)
```

---

# Socket 종류

## 주소 체계

- AF_INET
- AF_INET6

---

## 통신 방식

- SOCK_STREAM (TCP)
- SOCK_DGRAM (UDP)

---

# TCP 통신

## 서버

1. socket()
2. bind()
3. listen()
4. accept()
5. recv()
6. send()
7. close()

---

## 클라이언트

1. socket()
2. connect()
3. send()
4. recv()
5. close()

---

# UDP 통신

TCP와 달리 연결 과정이 없다.

송신

```python
sendto()
```

수신

```python
recvfrom()
```

---

# Socket 설정

Blocking

```python
setblocking(True)
```

Non-Blocking

```python
setblocking(False)
```

Timeout

```python
settimeout(5)
```

---

# Broadcast

동일 네트워크 전체에 전송

설정

```python
setsockopt(
    SOL_SOCKET,
    SO_BROADCAST,
    1
)
```

---

# 채팅 서버 구조

```text
Client
    │
    ▼
Socket
    │
    ▼
Thread
    │
    ▼
Server
```

---

# 핵심 암기

- `time` : Timestamp 처리
- `datetime` : 날짜/시간 객체
- `timedelta` : 시간 차이
- `Fraction` : 분수 계산
- `os.path` : 파일 경로
- `glob` : 파일 검색
- `os` : 운영체제 기능
- `sys` : Python 실행 환경
- `copy.copy()` : 얕은 복사
- `copy.deepcopy()` : 깊은 복사
- `weakref` : 약한 참조
- `Thread` : 병렬 작업
- `Lock` : 임계 영역 보호
- `Condition` : 생산자-소비자 제어
- `Semaphore` : 동시 실행 개수 제한
- `socket` : 네트워크 통신
- TCP : 연결형
- UDP : 비연결형

---

# 한 페이지 요약

```text
Python Module
│
├── Date & Time
│   ├── time
│   ├── datetime
│   ├── timedelta
│   └── Fraction
│
├── File System
│   ├── os.path
│   ├── glob
│   ├── os
│   └── sys
│
├── Memory
│   ├── copy
│   ├── deepcopy
│   └── weakref
│
├── Thread
│   ├── Lock
│   ├── RLock
│   ├── Condition
│   └── Semaphore
│
└── Network
    ├── Socket
    ├── TCP
    ├── UDP
    └── Broadcast
```