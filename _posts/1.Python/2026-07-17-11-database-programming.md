---
title: 데이터베이스 프로그래밍
description: Python DB API를 이용한 관계형 DB와 NoSQL 연동 개요 정리
date: 2026-07-17
series: Python
tags:
  - Python
  - AutoEver SW School
---

> Python DB API를 이용한 관계형 데이터베이스(MySQL, Oracle)와 NoSQL(MongoDB, Redis) 연동을 학습한다.

---

#Python #Database #MySQL #Oracle #MongoDB #Redis

## 학습 목표

- Python DB API
- MySQL 연동
- Oracle 연동
- CRUD
- Stored Procedure
- BLOB
- MongoDB
- Redis

---

# 데이터베이스(Database)

## 데이터베이스 종류

|구분|대표 DB|
|---|---|
|RDBMS|MySQL, Oracle, PostgreSQL, SQLite|
|NoSQL|MongoDB, Redis|

---

# Python DB API

Python에서 데이터베이스를 접근하기 위한 표준 API

지원 기능

- Database 연결
- SQL 실행
- Transaction
- Cursor
- Commit / Rollback

대표 흐름

```text
Connect
    │
    ▼
Cursor
    │
    ▼
Execute SQL
    │
    ▼
Commit / Rollback
    │
    ▼
Close
```

---

# ORM

Object Relational Mapping

객체와 데이터베이스를 연결하는 기술

대표 ORM

- Django ORM
- Peewee
- PonyORM

---

# MySQL

## 설치

```bash
pip install pymysql
```

---

## 연결

```python
import pymysql

conn = pymysql.connect(
    host="localhost",
    port=3306,
    user="user",
    passwd="password",
    db="database",
    charset="utf8"
)
```

---

## Cursor

```python
cursor = conn.cursor()
```

---

# SQL 실행

```python
cursor.execute(sql)
```

---

## Parameter Binding

```python
cursor.execute(
    "insert into usertbl values(%s,%s,%s)",
    values
)
```

장점

- SQL Injection 방지
- 코드 가독성 향상

---

# Transaction

반영

```python
conn.commit()
```

취소

```python
conn.rollback()
```

---

# CRUD

## INSERT

```python
cursor.execute(
    "insert into ..."
)
```

---

## UPDATE

```python
cursor.execute(
    "update ..."
)
```

---

## DELETE

```python
cursor.execute(
    "delete ..."
)
```

---

## SELECT

```python
cursor.execute(
    "select * from usertbl"
)
```

---

# 조회

## fetchone()

한 개 반환

```python
row = cursor.fetchone()
```

---

## fetchall()

전체 반환

```python
rows = cursor.fetchall()
```

---

# Stored Procedure

프로시저 실행

```python
cursor.callproc(
    "myproc",
    args
)
```

---

# BLOB

Binary Large Object

이미지

- 영상
- PDF
- Binary Data

저장 가능

---

## 저장

```python
with open(
    filename,
    "rb"
) as f:

    data = f.read()
```

↓

```python
cursor.execute(
    sql,
    (id,name,data)
)
```

---

## 읽기

```python
rows = cursor.fetchall()
```

↓

```python
open(
    filename,
    "wb"
)
```

---

# Oracle

## 설치

```bash
pip install cx_Oracle
```

---

## DSN

```python
dsn = cx_Oracle.makedsn(
    host,
    port,
    sid
)
```

---

## 연결

```python
conn = cx_Oracle.connect(
    user,
    password,
    dsn
)
```

---

# Oracle Parameter

MySQL

```python
%s
```

Oracle

```python
:1
:2
```

예

```python
cursor.execute(
    "insert into dept values(:1,:2,:3)",
    values
)
```

---

# Oracle CRUD

동일한 흐름

```text
Connect
    │
Cursor
    │
Execute
    │
Commit
    │
Close
```

---

# Oracle Procedure

실행

```python
cursor.callproc(
    "INSERT_DEPT",
    args
)
```

---

# Oracle BLOB

저장

```python
cursor.execute(
    sql,
    blob
)
```

---

읽기

```python
blob.read()
```

---

# MongoDB

## 설치

```bash
pip install pymongo
```

---

## 연결

```python
from pymongo import MongoClient

conn = MongoClient(
    "127.0.0.1"
)
```

---

## Database

```python
db = conn.mymongo
```

---

## Collection

```python
collection = db.users
```

---

# Document

JSON 형태

```json
{
    "name":"Kim",
    "age":20
}
```

---

# Insert

## insert_one()

```python
collection.insert_one(doc)
```

---

## insert_many()

```python
collection.insert_many(data)
```

---

# Search

## find_one()

```python
collection.find_one()
```

---

## find()

```python
collection.find()
```

---

## 조건 검색

```python
collection.find(
    {
        "age":{
            "$gte":30
        }
    }
)
```

---

## 정렬

```python
.sort("age")
```

---

# Update

## update_one()

```python
collection.update_one(
    condition,
    update
)
```

---

## update_many()

```python
collection.update_many(
    condition,
    update
)
```

---

# Delete

## delete_one()

```python
collection.delete_one(
    condition
)
```

---

## delete_many()

```python
collection.delete_many(
    condition
)
```

---

# Redis

## 설치

```bash
pip install redis
```

---

## 연결

```python
import redis

conn = redis.StrictRedis(
    host="localhost",
    port=6379
)
```

---

# 문자열(String)

저장

```python
conn.set(
    "name",
    "adam"
)
```

조회

```python
conn.get("name")
```

---

# TTL

만료 시간

```python
conn.expire(
    "name",
    30
)
```

조회

```python
conn.ttl(
    "name"
)
```

---

# List

오른쪽 삽입

```python
rpush()
```

왼쪽 삽입

```python
lpush()
```

삭제

```python
lpop()
```

조회

```python
lrange()
```

---

# Hash

저장

```python
hset()
```

조회

```python
hget()

hgetall()
```

---

# Set

저장

```python
sadd()
```

조회

```python
smembers()
```

집합 연산

```python
sunion()

sinter()
```

---

# Sorted Set

저장

```python
zadd()
```

조회

```python
zrange()
```

내림차순

```python
desc=True
```

---

# RDBMS vs NoSQL

|항목|RDBMS|NoSQL|
|---|---|---|
|구조|Table|Document / Key-Value|
|대표|MySQL, Oracle|MongoDB, Redis|
|Schema|고정|유연|
|SQL|사용|사용 안 함(제품별 상이)|

---

# DB API 흐름

```text
Connect
    │
    ▼
Cursor
    │
    ▼
Execute
    │
    ├── INSERT
    ├── UPDATE
    ├── DELETE
    └── SELECT
    │
    ▼
Commit / Rollback
    │
    ▼
Close
```

---

# 핵심 암기

- Python DB API : 표준 DB 인터페이스
- `cursor()` : SQL 실행 객체
- `execute()` : SQL 실행
- `commit()` : 반영
- `rollback()` : 취소
- `fetchone()` : 1개 조회
- `fetchall()` : 전체 조회
- `callproc()` : 프로시저 실행
- BLOB : 바이너리 데이터 저장
- MongoDB : Document Database
- `insert_one()` : 1개 저장
- `find()` : 조회
- `update_many()` : 여러 개 수정
- `delete_many()` : 여러 개 삭제
- Redis : In-Memory Database
- `set()` / `get()` : 문자열
- `hset()` : Hash
- `sadd()` : Set
- `zadd()` : Sorted Set
- `expire()` : TTL 설정

---

# 한 페이지 요약

```text
Database Programming
│
├── Python DB API
│   ├── Connect
│   ├── Cursor
│   ├── Execute
│   ├── Commit
│   └── Close
│
├── MySQL
│   ├── CRUD
│   ├── Procedure
│   └── BLOB
│
├── Oracle
│   ├── CRUD
│   ├── Procedure
│   └── BLOB
│
├── MongoDB
│   ├── Collection
│   ├── Document
│   ├── CRUD
│   └── Query
│
└── Redis
    ├── String
    ├── List
    ├── Hash
    ├── Set
    ├── Sorted Set
    └── TTL
```