---
title: MariaDB Python 연동
description: Python에서 pyMySQL을 이용한 MariaDB 연결, CRUD, Stored Procedure 사용 정리
date: 2026-07-17
series: MariaDB
tags:
  - MariaDB
  - AutoEver SW School
---

## 1. Python DB API 개요

- **정의**: 파이썬에서 데이터베이스에 접속하기 위한 표준 인터페이스임.
- **특징**: 표준 API를 따르기 때문에 여러 종류의 DB 모듈이 동일한 방식으로 작동함.
- **주요 기능**: DB 연결, SQL 실행, 연결 해제 등 기본적인 작업을 정의함.
- **데이터 엑세스 방식**:
    - **Python DB API**: 표준 API를 통한 직접 접근 방식임.
    - **ORM (Object Relational Mapping)**: 객체와 관계형 DB 테이블을 매핑하여 사용하는 기술임 (예: Django ORM, SQLAlchemy).

## 2. 연동 모듈 설치 및 접속

### 2.1 MariaDB 연동 모듈 설치

- **명령어**:

```python
pip install pyMySQL
```

### 2.2 데이터베이스 접속 (Connection)

- **문법**: `pymysql.connect()`를 사용해 연결 객체를 생성함.
- **예제**:

```python
import pymysql

# 데이터베이스 연결 설정
con = pymysql.connect(
    host='localhost',
    port=3306,
    user='root',
    passwd='비밀번호',
    db='sample',
    charset='utf8mb4'
)
print(con)
con.close() # 작업 후 반드시 닫아야 함
```

---

## 3. DML 수행 (삽입, 수정, 삭제)

### 3.1 기본 원칙

- 연결 객체의 `cursor()` 메서드로 SQL 실행 객체를 생성함.
- `execute()` 메서드로 SQL을 실행하며, 매개변수는 튜플로 전달하는 것이 권장됨.
- 변경 사항을 반영하려면 반드시 `commit()`을 호출해야 함 (취소는 `rollback()`).

### 3.2 데이터 삽입 (INSERT) 예제

```python
import sys, pymysql

try:
    con = pymysql.connect(host='localhost', port=3306, user='root', password='비밀번호', database='sample', charset='utf8mb4')
    cursor = con.cursor()

    # 방식 1: 직접 쿼리 작성
    cursor.execute("insert into usertbl values('ljy', '이진연', 1970, '서울', '01012345678', '1970-10-31')")

    # 방식 2: 매개변수 사용 (권장)
    # sql = "insert into usertbl values(%s, %s, %s, %s, %s, %s)"
    # data = ('sohye', '김소혜', 1999, '서울', '01012121212', '1999-7-19')
    # cursor.execute(sql, data)

    con.commit()
    print("삽입 성공") # 실행 결과 출력
except:
    print('exception:', sys.exc_info())
finally:
    con.close()
```

### 3.3 데이터 수정 및 삭제 예제

```sql
# 수정 (UPDATE)
cursor.execute("update usertbl set name='이지연' where name = '이진연'")

# 삭제 (DELETE)
cursor.execute("delete from usertbl where name = '구하라'")
con.commit()
print("수정/삭제 성공")
```

---

## 4. 데이터 조회 (SELECT)

- **fetchall()**: 모든 데이터를 튜플들의 튜플(이중 구조)로 반환함.
- **fetchone()**: 결과 중 첫 번째 행 1개만 튜플로 반환함.

### 4.1 조회 예제

```python
cursor.execute("select * from usertbl")

# fetchone() 사용 시
data = cursor.fetchone()
print(data) # 한 행 출력

# fetchall() 사용 시
rows = cursor.fetchall()
for row in rows:
    print(row) # 전체 행을 순차적으로 출력
```

---

## 5. 고급 기능 연동

### 5.1 스토어드 프로시저 호출

- **문법**: `cursor.callproc('프로시저이름', args=(매개변수))` 형식을 사용함.
- **예제**:

```python
cursor.callproc('myproc', args=('momo', '모모', 1996, '교토', '01098765432', '1996-11-9'))
con.commit()
```

### 5.2 BLOB(바이너리 데이터) 처리

- 이미지 등 이진 데이터를 DB에 저장하거나 읽어올 때 사용함.
- **저장**: 파일을 `rb`(read binary) 모드로 열어 데이터를 읽은 후 `execute`로 전달함.
- **읽기**: DB 결과를 가져와 `wb`(write binary) 모드로 파일에 기록함.

---

## 6. ORM (SQLAlchemy) 활용

### 6.1 SQLAlchemy 개요

- 파이썬에서 가장 널리 사용되는 ORM 라이브러리임.
- 애플리케이션 시스템에 간섭하지 않고 객체 지향적인 프로그래밍을 가능하게 함.

### 6.2 기본 설정 및 실습

```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. 연결 URL 및 엔진 생성
DB_URL = "mysql+pymysql://root:비밀번호@localhost:3306/sample?charset=utf8mb4"
engine = create_engine(DB_URL, echo=True)

# 2. 세션 및 기본 클래스 설정
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 3. 모델 정의
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True)

# 4. 테이블 생성 및 데이터 작업
Base.metadata.create_all(bind=engine)
db = SessionLocal()

# 데이터 추가(C)
new_user = User(name="홍길동", email="hong@example.com")
db.add(new_user)
db.commit()

# 데이터 조회(R)
user = db.query(User).filter(User.name == "홍길동").first()
print(f"조회된 사용자: {user.name} ({user.email})")
db.close()
```