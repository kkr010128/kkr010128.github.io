---
title: Python 기초
description: Python 가상환경, 기본 문법 요약 정리
date: 2026-07-06
series: Python
tags:
  - Python
  - AutoEver SW School
---

## 가상환경 생성

```bash
# 가상환경 이름으로 디렉토리 생성
python -m venv ${dirName}

# Activate (Mac)
source ${dirName}/bin/activate

# Deactivate
deactivate
```

## Data
- Mutable Data (가변형, RDB)
- Immutable Data (불변형, 읽기 전용)
	- Literal (사용자 입력 데이터)
	- Constant (상수): 데이터를 저장하고 읽기 전용으로 사용

## Grammar
1. 라인 단위로 번역해 실행하므로 라인 종료 기호( ; ) 가 없음
2. 하나의 라인에 2개 이상의 명령어가 있는 경우 " ; "로 구분 필요
3. 블럭을 만들 때 들여쓰기 (4칸) 이용
4. 하위 레벨을 만들 때는 앞 레벨의 마지막에 " : "을 추가

## Constructions
1. Literal: 개발자가 직접 입력한 데이터
2. Variable: 데이터를 메모리에 저장하고 해당 메모리에 붙인 이름
3. Function: 한 번에 수행할 수 있는 코드를 모은 후 붙인 이름
4. Class & Instance(Object - 객체): 동일한 목적을 위해 모인 데이터와 함수의 모임
5. Class: 템플릿
6. Instance: Class를 기반으로 만들어진 객체
7. Module: 하나의 파일, 독립적으로 실행 가능한 코드의 모임
8. Package: 관련 있는 Module의 집합, 배포 단위
9. Comment: 코드에 대한 설명, 번역되지 않음

## Comment
- 단일 주석 → `# 내용`
- 다중 주석 → `""" 내용 """` or `''' 내용 '''`
	- 원래 다중 주석은 없음
	- 원래 여러 줄의 문자열 리터럴을 만드는 데 사용함
- 주석이 아닌 것 → `#!`
	- Unix(Linux)의 shebang(프로그램으로 실행)
	- Encoding 같은 것을 지정
## Document 출력
- `print(dir(데이터))`: 데이터가 사용할 수 있는 속성(데이터)와 함수 목록을 출력
- `help(이름)`: 함수의 도움말을 출력
## Reserved Words
- Python이 기능을 정해둔 명령어
- 다른 용도로 사용 불가(데이터를 가리키는 용도로 사용할 수 없음)
- Python에서 제공하는 Class들은 예약어가 아님
	- 기본적으로 모든 데이터의 자료형이 id이므로 이름을 가지고 모든 종류의 데이터를 가리킬 수 있다.
```python
import keyword
print(keyword.kwlist)
```