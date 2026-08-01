---
title: 객체지향 프로그래밍
description: Python의 클래스, 상속, 프로퍼티, 연산자 오버로딩, 추상 클래스, 코루틴 정리
date: 2026-07-08
series: Python
tags:
  - Python
  - AutoEver SW School
---

> Python의 객체지향 프로그래밍(OOP), 클래스, 상속, 객체 모델 및 모듈 시스템을 학습한다.

---

#Python #OOP #Class #Inheritance #Module

## 학습 목표

- 객체지향 프로그래밍 이해
- Class와 Instance
- 생성자와 소멸자
- Property
- 연산자 오버로딩
- 상속
- Iterator / Generator
- Module과 Package

---

# 객체지향 프로그래밍(OOP)

## 객체지향의 4대 특징

### 캡슐화(Encapsulation)

- 데이터와 기능을 하나로 묶음
- 내부 구현 은닉
- 정보 은닉(Information Hiding)

---

### 상속(Inheritance)

- 기존 클래스 재사용
- 코드 중복 제거
- 기능 확장

---

### 다형성(Polymorphism)

같은 메서드 호출이라도 객체에 따라 다른 동작 수행

대표 방법

- Method Overriding

---

### 동적 바인딩(Dynamic Binding)

실행 시점(Runtime)에 호출할 메서드가 결정된다.

---

# 객체지향 용어

|용어|설명|
|---|---|
|Object|객체|
|Class|객체 설계도|
|Instance|클래스로 생성한 객체|
|Attribute|속성(데이터)|
|Method|클래스 내부 함수|
|Constructor|생성자|

---

# Class

## 기본 구조

```python
class Student:

    def __init__(self):
        self.name = "Adam"

    def study(self):
        print("Study")
```

---

## 객체 생성

```python
student = Student()
```

---

## 멤버 접근

```python
student.name
student.study()
```

---

# self

현재 객체 자신을 의미한다.

모든 인스턴스 메서드의 첫 번째 매개변수

```python
def study(self):
```

---

# 생성자(Constructor)

객체 생성 시 자동 실행

```python
class Student:

    def __init__(self, name):
        self.name = name
```

생성

```python
Student("Adam")
```

---

# 소멸자(Destructor)

객체가 제거될 때 실행

```python
def __del__(self):
    ...
```

주로

- 파일 종료
- 네트워크 종료
- 자원 해제

---

# Attribute

## Class Attribute

모든 객체가 공유

```python
class Student:

    school = "Python"
```

접근

```python
Student.school
```

---

## Instance Attribute

객체마다 별도 저장

```python
self.name
```

---

# Getter / Setter

객체 데이터를 직접 수정하지 않고 메서드를 이용

```python
def getName(self):
    return self.name

def setName(self, name):
    self.name = name
```

---

# Property

Getter/Setter를 변수처럼 사용

```python
@property
def name(self):
    return self.__name
```

Setter

```python
@name.setter
def name(self, value):
    self.__name = value
```

사용

```python
student.name = "Adam"

print(student.name)
```

---

# private 멤버

이름 앞에 `__`

```python
self.__name
```

외부 접근 제한

---

# Static Method

객체 생성 없이 호출

```python
@staticmethod
def func():
    ...
```

호출

```python
Student.func()
```

특징

- self 없음
- 객체 상태 사용 불가

---

# Class Method

```python
@classmethod
def func(cls):
```

특징

- cls 사용
- 클래스 정보 접근 가능

---

# __slots__

생성 가능한 Attribute 제한

```python
class Student:

    __slots__ = ["name","score"]
```

장점

- 메모리 절약
- Attribute 추가 방지

---

# is 와 ==

## ==

값 비교

```python
a == b
```

---

## is

객체 주소(id) 비교

```python
a is b
```

---

# 특수 메서드(Magic Method)

대표 메서드

|메서드|의미|
|---|---|
|`__init__`|생성자|
|`__del__`|소멸자|
|`__str__`|문자열 출력|
|`__repr__`|객체 표현|
|`__eq__`|==|
|`__hash__`|hash|
|`__call__`|객체 호출|
|`__getitem__`|인덱싱|
|`__setitem__`|인덱스 저장|

---

# Operator Overloading

연산자 기능 재정의

예

```python
def __add__(self, other):
```

+

---

```python
def __eq__(self, other):
```

==

---

```python
def __str__(self):
```

print()

---

```python
def __getitem__(self, key):
```

[]

---

# Singleton Pattern

객체를 하나만 생성

```python
def __new__(cls):
```

사용

---

# Inheritance

## 상속

```python
class Person:
    ...

class Student(Person):
    ...
```

장점

- 코드 재사용
- 기능 확장

---

## super()

부모 클래스 호출

```python
super().__init__()
```

---

## Method Overriding

부모 메서드 재정의

```python
class Student(Person):

    def greeting(self):
        super().greeting()
```

---

## 다중 상속

```python
class Child(A, B):
```

메서드 탐색

```python
Class.mro()
```

---

# Abstract Class

추상 클래스

```python
from abc import ABCMeta
```

추상 메서드

```python
@abstractmethod
```

특징

- 객체 생성 불가
- 반드시 Override

---

# Delegation

없는 메서드 호출 시 위임

```python
def __getattr__(self, name):
```

---

# Iterator

순차 접근 객체

필수 메서드

```python
__iter__()

__next__()
```

반복 종료

```python
StopIteration
```

---

# enumerate()

인덱스와 데이터 반환

```python
for idx, value in enumerate(data):
```

---

# Generator

yield를 사용하는 Iterator

```python
def gen():

    yield 1
    yield 2
```

장점

- Lazy Evaluation
- 메모리 절약

---

# Coroutine

Generator 기반

```python
send()
```

사용

```python
yield
```

값 송수신 가능

---

# Module

하나의 Python 파일

가져오기

```python
import math
```

---

## import

```python
import math
```

---

```python
from math import sin
```

---

```python
import math as m
```

---

# Package

여러 Module을 묶은 디렉터리

구성

```text
mypackage/

    __init__.py

    module.py
```

---

# pip

설치

```bash
pip install package
```

업데이트

```bash
pip install --upgrade package
```

삭제

```bash
pip uninstall package
```

목록

```bash
pip list
```

---

# matplotlib

그래프 작성

```python
import matplotlib.pyplot as plt
```

---

# folium

지도 시각화

```python
import folium
```

---

# 핵심 암기

- Class = 객체 설계도
- Instance = 객체
- self = 현재 객체
- `__init__()` = 생성자
- `__del__()` = 소멸자
- Class Attribute = 공유 변수
- Instance Attribute = 객체별 변수
- `@staticmethod` = 정적 메서드
- `@classmethod` = 클래스 메서드
- `@property` = Getter / Setter
- `super()` = 부모 클래스 호출
- Inheritance = 상속
- Overriding = 재정의
- `__str__()` = 문자열 출력
- `__eq__()` = 비교
- `__getitem__()` = 인덱싱
- Iterator = `__iter__`, `__next__`
- Generator = `yield`
- Coroutine = `send()`
- Module = Python 파일
- Package = Module 묶음

---

# 한 페이지 요약

```text
OOP
│
├── Class
│   ├── Attribute
│   ├── Method
│   ├── self
│   ├── Constructor
│   └── Destructor
│
├── Getter / Setter
├── Property
├── Static Method
├── Class Method
│
├── Operator Overloading
├── Magic Method
│
├── Inheritance
│   ├── super()
│   ├── Overriding
│   ├── Multiple Inheritance
│   └── Abstract Class
│
├── Iterator
├── Generator
├── Coroutine
│
└── Module
    ├── Package
    ├── pip
    ├── matplotlib
    └── folium
```

