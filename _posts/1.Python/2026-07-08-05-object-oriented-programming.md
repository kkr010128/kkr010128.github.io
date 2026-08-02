---
title: 객체지향 프로그래밍
description: Python의 클래스, 상속, 프로퍼티, 연산자 오버로딩, 추상 클래스, 코루틴 정리
date: 2026-07-08
series: Python
tags:
  - Python
  - AutoEverSW
---

## 1) OOP 개요
---
### 객체지향의 4대 특징

| 특징 | 설명 |
| ---- | ---- |
| **캡슐화(Encapsulation)** | 데이터와 기능을 하나로 묶고 내부 구현 은닉 |
| **상속(Inheritance)** | 하위 클래스가 상위 클래스의 모든 것을 물려받음 |
| **다형성(Polymorphism)** | 동일한 메시지에 대해 다르게 반응 |
| **추상화(Abstraction)** | 공통 특징을 추출하여 상위 개념 정의 |

## 2) Class와 Instance
---
### 클래스 선언
```python
class 이름:
    데이터 선언
    def 메서드(self):
        실행문
```

### 인스턴스 생성
```python
s = Student()           # 인스턴스 생성
s.display()             # 인스턴스 메서드 호출
Student.display(s)      # 언바운드 호출 (클래스가 직접 호출)
```

### Method
- 인스턴스 메서드의 첫 번째 매개변수는 **self** (인스턴스 자신)

## 3) Attribute (속성)
---
### Class Attribute vs Instance Attribute

| 구분 | 특징 |
| ---- | ---- |
| **Class Attribute** | 클래스 안에 1개만 생성, 모든 인스턴스가 공유 |
| **Instance Attribute** | 각 인스턴스가 별도 소유, `self.속성명`으로 생성 |

### Accessor (Getter / Setter)
```python
class Student:
    def getNum(self):
        return self.num
    def setNum(self, num):
        self.num = num
```

## 4) 생성자와 소멸자
---
### `__init__` (생성자)
인스턴스 생성 시 자동 호출, 속성 초기화에 사용

```python
class Student:
    def __init__(self, num=0, name="noname"):
        self.num = num
        self.name = name
```

### `__del__` (소멸자)
인스턴스 소멸 시 호출, 외부 연결 해제에 사용

### Garbage Collection
- **참조 카운트(Reference Count)** 방식
- 참조 시 +1, 참조 해제 시 -1
- 0이 되면 GC가 메모리 정리 (우선순위 낮음)

```python
s1 = Student()  # count: 1
s2 = s1         # count: 2
del s1           # count: 1 (소멸 안 됨)
```

## 5) Static / Class Method
---
```python
class MyClass:
    @staticmethod
    def static_method():    # self 없음, 클래스로 직접 호출
        pass
    
    @classmethod
    def class_method(cls):  # 첫 매개변수는 cls (클래스 자신)
        pass
```

## 6) Private 멤버
---
- 이름 앞에 `__`를 붙이면 private
- 클래스 외부에서 직접 접근 불가

```python
class Student:
    def __init__(self, name, age):
        self.name = name        # public
        self.__age = age        # private
```

## 7) Property
---
Getter/Setter를 변수처럼 호출

```python
class Student:
    @property
    def name(self):
        return self.__name
    
    @name.setter
    def name(self, name):
        self.__name = name

s = Student()
s.name = "adam"   # setter 호출
print(s.name)     # getter 호출
```

## 8) 연산자 오버로딩
---
연산자의 기능을 변경 (예: `+`는 숫자 연산이지만 str에서는 문자열 결합)

```python
class Student:
    def __add__(self, other):     # + 연산자
        return self.name + other.name
    def __eq__(self, other):      # == 연산자
        return len(self.name) == len(other.name)
    def __str__(self):            # print() 시 출력
        return self.name
```

## 9) 상속(Inheritance)
---
### 기본
```python
class Person:
    def method(self):
        print("상위 클래스")

class Student(Person):     # Person 상속
    def method(self):
        super().method()   # 상위 클래스 메서드 호출
        print("하위 클래스")
```

**목적**: 코드 중복 제거, 기능 확장/추가

### Method Overriding
상위 클래스의 메서드를 하위 클래스에서 **재정의**
- 기능 확장이 목적 → 일반적으로 `super()`로 상위 메서드 호출

### 다중 상속
```python
class SubClass(Super1, Super2):
    pass
```
- 동일한 메서드가 여러 상위 클래스에 있으면 왼쪽부터 탐색

## 10) 추상 클래스
---
인스턴스를 만들 수 없는 클래스, 상속을 통해서만 사용

```python
import abc

class Starcraft(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def attack(self):
        pass

class Terran(Starcraft):
    def attack(self):
        print("테란 공격")
```

**목적**: 다형성(Polymorphism) 구현, Template Method Pattern

## 11) Coroutine
---
- **협력 루틴(Cooperative Routine)**
- 함수는 호출되면 종료 후 반환되지만, 코루틴은 종료되지 않고 중단/재개 가능
- 서로 대등한 관계로 특정 시점에 상대방 코드 실행