---
title: 데이터베이스 프로그래밍
description: Python DB API를 이용한 관계형 DB와 NoSQL 연동 개요 정리
date: 2026-07-17
series: Python
tags:
  - Python
  - AutoEverSW
---

## 1) Python DB API 개요
---
- Python에서 DB를 액세스하기 위한 표준 API
- DB 연결, 쿼리 수행, 연결 해제 등 기본 기능 정의
- ORM(Object Relational Mapping): RDBMS Table과 Object 매핑, 쿼리 대신 메서드 호출로 DB 사용

### DB 접속에 필요한 정보
- URL, Port, DB Name, 계정, 비밀번호

## 2) MariaDB 연동
---
```python
import pymysql

conn = pymysql.connect(host="localhost", user="root", password="1234", db="mydb")
cursor = conn.cursor()

cursor.execute("SELECT * FROM users")
result = cursor.fetchall()

conn.close()
```

## 3) MongoDB 연동
---
```python
from pymongo import MongoClient

conn = MongoClient("127.0.0.1")
db = conn.mydb
users = db.users

users.insert_one({"name": "kim"})
result = users.find()
```

## 4) Redis 연동
---
```python
import redis

con = redis.StrictRedis(host="127.0.0.1", port=6379)
con.set("key", "value")
print(con.get("key"))
```