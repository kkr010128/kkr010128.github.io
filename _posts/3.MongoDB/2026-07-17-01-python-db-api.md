---
title: Python DB API
description: Python에서 pymongo를 이용한 MongoDB 연결 및 CRUD 연동 정리
date: 2026-07-17
series: Python
tags:
  - Python
  - AutoEverSW
---

## 1) 개요
---
- Python에서 DB에 접근하기 위한 표준 API
- DB 연결, 쿼리 수행, 연결 해제 등 기본 기능 정의
- 표준 API를 활용한 ORM(Object Relational Mapping)
    → RDBMS의 Table과 Object 매핑
    → SQL 대신 객체 메서드 호출로 DB 사용

### DB 접속에 필요한 정보
- URL, Port (기본 포트 사용 시 생략 가능), DB Name, 계정, 비밀번호

## 2) MongoDB 연동
---
### 패키지 설치
```python
pip install pymongo
```

### 과정
1. 패키지 설치 (`pymongo`)
2. 데이터베이스 연결: `변수 = pymongo.MongoClient("URL", 포트)`
3. 데이터베이스 생성 또는 연결: `db = 변수.데이터베이스이름`
4. 컬렉션 연결: `컬렉션 = db.컬렉션이름`
5. 데이터베이스 작업 수행 (CRUD)
6. 연결 해제: `변수.close()`

## 3) 데이터 삽입
---
```python
from pymongo import MongoClient

try:
    conn = MongoClient('127.0.0.1')
    db = conn.mydb
    users = db.users

    users.insert_one({'empno': '10001', 'name': 'kim'})
    users.insert_many([
        {'empno': '10002', 'name': 'lee'},
        {'empno': '10003', 'name': 'park'}
    ])
    print("데이터 삽입 성공")

except Exception as e:
    print(e)
else:
    conn.close()
```

## 4) 데이터 조회
---
```python
from pymongo import MongoClient

try:
    conn = MongoClient('127.0.0.1')
    db = conn.mydb
    users = db.users

    # find: 전체 조회 (cursor 반환 → for로 변환 필요)
    results = users.find().sort({'name': -1})
    for result in results:
        print(result['name'])

except Exception as e:
    print(e)
else:
    conn.close()
```

- `find()` → 전체 데이터, 커서(cursor) 반환
- `find_one()` → 하나의 데이터, dict 반환

## 5) 데이터 수정
---
```python
users.update_one({'empno': '10001'}, {'$set': {'name': 'new_name'}})
users.update_many({'dept': 'sales'}, {'$set': {'dept': 'marketing'}})
```

## 6) 데이터 삭제
---
```python
users.delete_one({'empno': '10001'})
users.delete_many({'dept': 'old'})
```

## 7) with 구문 (Auto Close)
---
```python
from pymongo import MongoClient

with MongoClient('127.0.0.1') as conn:
    db = conn.mydb
    users = db.users

    users.insert_one({'name': 'test'})
    # with 블록 종료 시 자동 close
```