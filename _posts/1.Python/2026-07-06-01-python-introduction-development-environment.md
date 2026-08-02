---
title: Python 소개 및 개발 환경
description: Python의 특징, 인터프리터/컴파일러 개념, IDE 종류, 가상환경 설정까지 정리
date: 2026-07-06
series: Python
tags:
  - Python
  - AutoEverSW
---

## 1) 데이터 처리 개요
---
- **데이터 과학(Data Science)**
	→ 데이터를 수집, 정제, 저장, 분석하여 의미 있는 정보를 추출하는 학문
- **빅데이터(Big Data)**
	→ 기존 시스템으로 처리하기 어려운 매우 크거나 빠르게 생성되는 데이터
- **데이터 분석(Data Analysis)**
	→ 알고리즘과 수학적 기법으로 패턴 발견, 문제 해결, 인사이트 도출

### 데이터 활용 과정
```text
데이터 수집 → 정제(Cleansing) → 저장 → 분석 → 정보(Insight) 도출
```

### 컴퓨터를 이용한 데이터 분석의 장점
- 대용량 데이터 처리 가능
- 반복 작업 자동화
- 사람의 편향 감소
- 분석 속도 향상

## 2) 프로그래밍 기초
---
### 프로그래밍 언어
- 사람의 생각을 컴퓨터가 이해할 수 있도록 표현하는 언어

### 컴파일러 vs 인터프리터

| | 컴파일러 | 인터프리터 |
|--|---------|-----------|
| 방식 | 소스코드 전체를 기계어로 변환 후 실행 | 한 줄씩 해석하며 즉시 실행 |
| 실행 속도 | 빠름 | 상대적으로 느림 |
| 개발 속도 | 컴파일 과정 필요 | 빠름, 디버깅 쉬움 |
| 대표 언어 | C, C++ | Python |

## 3) Python 개요
---
### Python이란?
- 1991년 **Guido van Rossum**이 개발
- **인터프리터 언어** → 한 줄씩 해석 실행
- **객체지향 언어** → 모든 것이 객체
- **동적 타이핑 언어** → 자료형을 자동 결정
- **들여쓰기**로 블록 표현
- 플랫폼 독립적 (Windows, Linux, macOS, Unix)
- 풍부한 라이브러리 생태계

### Python의 장점
- 배우기 쉽고 문법이 간결하며 가독성이 높음
- 데이터 분석, AI/ML 분야의 표준 언어
- 웹 개발, 자동화, 크롤링, 서버 개발 등 다양한 분야에 활용

### Python 구현체

| 구현체 | 특징 |
| ----- | ---- |
| **CPython** | 가장 일반적인 구현체 |
| PyPy | 실행 속도 향상 |
| Jython | JVM 기반 |
| IronPython | .NET 기반 |
| Stackless Python | C Stack 사용 최소화 |

## 4) 개발 환경
---
### IDE(통합 개발 환경)
- 코드 작성, 실행, 디버깅, 프로젝트 관리를 하나의 프로그램에서 제공
- 대표 기능: 자동완성, 문법 검사, 디버깅

| 도구 | 특징 |
| --- | ---- |
| **PyCharm** | Python 전용 IDE, IntelliJ 기반, 강력한 코드 분석 |
| **VS Code** | 범용 IDE, 가볍고 확장성 뛰어남, Python Extension 필요 |
| **Jupyter Notebook** | 브라우저 기반, 코드+문서 함께 작성, 데이터 분석에 적합 |
| **Spyder** | 과학 계산용, 변수 확인 가능 |
| **Google Colab** | 설치 불필요, 클라우드 실행, GPU 지원 |
| IDLE | Python 기본 IDE |

### Python 설치
- 공식 사이트: https://www.python.org/downloads/
- **Windows**: 설치 시 `Add Python to PATH` 반드시 체크
- **Linux**: `sudo apt-get install python3-tk` (Ubuntu)

### 확인
```bash
python --version
python3 --version
```

### Anaconda
- Python + Jupyter Notebook + Spyder + 과학 계산 라이브러리를 한 번에 포함한 배포판

## 5) 가상환경(Virtual Environment)
---
### 필요한 이유
- 프로젝트마다 Python 버전과 라이브러리 버전이 다를 수 있음
- 가상환경은 프로젝트별 **독립 환경**을 제공

### 생성 및 관리
```bash
# 생성
python -m venv myenv

# 활성화 (Mac/Linux)
source myenv/bin/activate

# 활성화 (Windows)
myenv\Scripts\activate

# 비활성화
deactivate
```

### PyCharm에서 설정
```text
File → Settings → Python Interpreter → 프로젝트별 Interpreter 선택
```

## 6) Python 기본 문법 요약
---
### 핵심 규칙
- 라인 단위로 번역 실행 → 라인 종료 기호(`;`) 불필요
- 하나의 라인에 여러 명령어는 `;`로 구분
- **들여쓰기(4칸 권장)** 로 블록 생성
- 하위 레벨 생성 시 상위 레벨 끝에 `:` 추가

### 구성 요소

| 요소 | 설명 |
| ---- | ---- |
| **Literal** | 개발자가 직접 입력한 데이터 |
| **Variable** | 데이터를 메모리에 저장한 이름 |
| **Function** | 실행 코드를 모아 이름을 붙인 것 |
| **Class & Instance** | 데이터+함수의 모임 (템플릿/객체) |
| **Module** | 하나의 파일, 독립 실행 가능한 코드 모임 |
| **Package** | 관련 Module의 집합, 배포 단위 |
| **Comment** | 코드 설명, 번역되지 않음 |

### 주석
- 한 줄: `# 내용`
- 여러 줄: `""" 내용 """` 또는 `''' 내용 '''` (문자열 리터럴 활용)
- `#!`: 주석이 아닌 shebang(실행 프로그램 지정)

### 도움말
- `print(dir(데이터))` → 사용 가능한 속성과 함수 목록 출력
- `help(이름)` → 함수의 도움말 출력

### 예약어(Reserved Words)
- Python이 기능을 정해둔 명령어로, 변수명 등 다른 용도로 사용 불가
- 확인: `import keyword` → `print(keyword.kwlist)`
- *하지만* Python이 제공하는 클래스들은 예약어가 아님