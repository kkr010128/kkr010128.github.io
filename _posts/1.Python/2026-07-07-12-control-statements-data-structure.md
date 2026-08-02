---
title: 제어문과 자료구조
description: Python 메모리 구조, 제어문, 자료구조 심화 정리
date: 2026-07-07
series: Python
tags:
  - Python
  - AutoEverSW
---

## 1) 메모리 구조
---
### Stack
- 함수 호출 시 생성되는 **지역 변수** 저장
- 함수 종료 시 자동 소멸
- LIFO (Last In First Out) 구조

### Heap
- **객체(인스턴스)** 저장
- 개발자가 직접 메모리 관리 (Python은 GC가 자동 관리)
- 참조가 없어지면 Garbage Collector가 정리

## 2) is와 ==
---

| 연산자  | 비교 대상               | 오버라이딩 |
| ---- | ------------------- | ----- |
| `==` | 데이터 값 비교 (`__eq__`) | 가능    |
| `is` | **id**(메모리 주소) 비교   | 불가능   |

```python
a = [1, 2, 3]
b = [1, 2, 3]
print(a == b)  # True (값이 같음)
print(a is b)  # False (다른 객체)
```

## 3) Mutable vs Immutable
---

| 구분                 | 종류                             | 특징                       |
| ------------------ | ------------------------------ | ------------------------ |
| **Mutable** (가변)   | `list`, `dict`, `set`          | 생성 후 내용 변경 가능            |
| **Immutable** (불변) | `int`, `float`, `str`, `tuple` | 생성 후 변경 불가, 변경 시 새 객체 생성 |

## 4) 얕은 복사 vs 깊은 복사
---
```python
import copy

original = [[1, 2], [3, 4]]

shallow = copy.copy(original)       # 얕은 복사 (내부 객체는 공유)
deep = copy.deepcopy(original)      # 깊은 복사 (완전히 독립)
```