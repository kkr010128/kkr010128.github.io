---
title: MariaDB Python 연동
description: Python에서 pyMySQL을 이용한 MariaDB 연결, CRUD, Stored Procedure 사용 정리
date: 2026-07-17
series: MariaDB
tags:
  - MariaDB
  - AutoEverSW
---

## 1) Python DB API 개요
---
- Python에서 DB에 접속하기 위한 **표준 인터페이스**
- 표준 API를 따르므로 여러 DB 모듈이 동일한 방식으로 동작

## 2) MariaDB 연동 모듈 설치
---
```python
pip install pymysql
```

## 3) 데이터베이스 접속
---
```python
import pymysql

config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '1234',
    'database': 'mydb',
    'charset': 'utf8'
}

conn = pymysql.connect(**config)
cursor = conn.cursor()
```

## 4) CRUD
---
### 조회 (SELECT)
```python
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()
for row in rows:
    print(row)
```

### 삽입 (INSERT)
```python
cursor.execute("INSERT INTO users(name, age) VALUES (%s, %s)", ("Kim", 25))
conn.commit()  # DML은 반드시 COMMIT
```

### 수정 (UPDATE)
```python
cursor.execute("UPDATE users SET age = %s WHERE name = %s", (30, "Kim"))
conn.commit()
```

### 삭제 (DELETE)
```python
cursor.execute("DELETE FROM users WHERE name = %s", ("Kim",))
conn.commit()
```

## 5) 연결 종료
---
```python
cursor.close()
conn.close()
```

## 6) with 구문 (자동 close)
---
```python
with pymysql.connect(**config) as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        result = cursor.fetchall()
```