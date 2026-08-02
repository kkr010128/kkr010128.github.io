---
title: 모듈과 패키지
description: Python 모듈, 패키지, collections, itertools 등 내장 모듈 정리
date: 2026-07-09
series: Python
tags:
  - Python
  - AutoEverSW
---

## 1) Module (모듈)
---
- 하나의 **파일** (.py)
- 독립적으로 실행 가능한 코드의 모임
- `import 모듈이름` 으로 사용

### 모듈 생성과 사용
```python
# mymodule.py
def hello():
    print("Hello")

# 사용
import mymodule
mymodule.hello()
```

## 2) Package (패키지)
---
- 관련 있는 Module의 **집합**
- **배포 단위**
- 디렉토리 구조로 관리

```text
mypackage/
    __init__.py
    module1.py
    module2.py
```

## 3) 표준 라이브러리
---

| 모듈 | 설명 |
| ---- | ---- |
| `os` | 운영체제 인터페이스 |
| `sys` | 시스템 관련 기능 |
| `datetime` | 날짜/시간 처리 |
| `math` | 수학 함수 |
| `random` | 난수 생성 |
| `json` | JSON 데이터 처리 |
| `re` | 정규 표현식 |
| `collections` | 추가 자료구조 (deque, Counter 등) |
| `itertools` | 효율적인 반복 도구 |
| `functools` | 고차 함수 도구 (reduce, lru_cache 등) |