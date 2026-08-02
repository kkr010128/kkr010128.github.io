---
title: MongoDB 개요
description: MongoDB 특징, RDBMS와 용어 비교, 설치 및 서버 실행 정리
date: 2026-07-15
series: MongoDB
tags:
  - MongoDB
  - AutoEverSW
---

## 개요
---
### 1. 특징
- 크로스 플랫폼 도큐먼트 지향 NoSQL 데이터베이스 시스템
- 스키마 생성 없이 데이터 저장 가능
- 내부적으로 C++ 동작
- 저장 프로시저 대신에 자바스크립트 함수와 유사한 형태의 함수를 만들어서 사용 
- 가장 큰 작업의 단위는 Collection이며, 하나의 파일에 저장됨
- JSON 문자열을 BSON으로 변환해 저장
- JavaSCript Object Notation 표현
	- { } : 객체 → {"name": "adam", "age": 34}
	- [  ] : 배열 → [{"name": "adam", "age": 34}, {"name": "smith", "age": 40} ,,, ]
- 복제(replica)와 샤딩을 이용해 수비고 빠른 분산 컴퓨팅 환경 구성
	- 샤딩: 데이터를 여러 조각으로 분할하여 저장
	- 샤드: 데이터를 수평 분할한 조각
	- 애플리케이션은 어떤 샤드에 데이터가 저장돼있는지 알 필요가 없음
### 2. 적절한 서비스
- 스키마가 자주 변경되는 환경
- 비정형 데이터 저장
	- 반정형 데이터: XML, JSON, YAML처럼 문차열이지만 해석하기에 따라 정형의 형태를 만들 수 있는 것
	- 비정형 데이터: 모양이 일정하지 않은 데이터로 문자열, 음성 등
- 분산 컴퓨팅 환경
### 3 . RDBMS와 용어 비교
- Database → Database
- Table → Collection
- Row(Tuple) → Document
- Column → Field
- Index → Index(데이터를 빠르게 접근하기 위한 포인터)
- Join → Embedding & Linking
- 조회 결과를 Table의 구조 → Cursor 리턴(데이터를 순차적으로 접근하기 위한 포인터: Iterator)
### 4. 설치
- `SERVER`: https://www.mongodb.com/try/download/community
	  ```bash
		$ brew install mongodb-atlas
		$ atlas setup
	  ```
- `CLIENT`:
	- Mongo SHell 을 다운로드 받아 사용
	- Compass를 다운받아 사용
- 실행
	- mongod라는 실행 파일을 실행
	- 서비스로 등록된 경우는 서비스를 실행
	- mongod는 인수 없이 실행하면 /data/db를 데이터 디렉토리로 사용
	- 데이터를 저장할 디렉토리를 지정할 거면 미리 만들어두고 쓰기 권한을 부여해야 함
	- 기본 포트는 27017
	- 시작하면 서버의 버전과 시스템 정보를 출력하고 클라이언트의 접속으로 대기함
- 외부 접속 허용
	- 설정 파일 이용: mongod.conf 파일이나 mongod.cfg에서 수정
		- net:
			- port: 27017
			- bindIp: 127.0.0.1을 0.0.0.0으로 수정
- 서버에 접속
	- Mongo Shell에서 접속
	- mongo: 로컬의 MongoDB에 젒고
	- 외부 서버에 접속: mongo 호스트이름:포트번호/데이터베이스이름
	- 이미 접속된 상태에서 접속
	- 
## docker installation

```bash
# MongoDB 이미지 가져오기
docker pull mongodb/mongodb-community-server:latest

# 이미지를 컨테이너로 실행
docker run --name mongodb -p 27017:27017 -d mongodb/mongodb-community-server:latest

# Container 실행 확인
docker container ls

# Container Shell 접근
docker exec -it mongodb mongosh
docker exec -it mongodb bash

# mongosh를 사용하여 MongoDB 배포서버에 연결
mongosh --port 27017

# 배포서버 유효성 검사
db.runCommand({hello: 1})
```


## mongosh
1. 현재 사용 중인 데이터베이스 확인 →  `db`
2. Database 생성 → `create database ${name};`
3. Connect Database → `use ${databaseName};` 존재하지 않으면 새로 생성함
4. 현재 만들어진 Database 확인 → `show dbs`

# Collection
---
- RDBMS에서의 Table과 유사한 개념

- Documents의 모음

- 비정규화된 데이터가 저장됨

- 동적 스키마를 가지지만 실제로는 같은 종류의 데이터를 하나의 Collection에 저장

- MongoDB에서는 Join 연산을 지원하지 않음
	- 하나의 Collection에 최대한 많은 양의 데이터를 저장하는 것을 권장하지만,
		- 너무 많은 데이터를 저장할 경우
			- 디스크 읽기 operation이 많이 필요,
			- 메모리의 캐시 효율이 떨어짐
		→ 여러 개의 Collections를 만들어 나눠 저장하기를 권장

- 다단계 Collection 생성가능
	- blog.posts와 blog.authors형태로 생성 가능

1. 컬렉션 생성 → `db.createCollection("${name}"`
2. 데이터베이스에 존재하는 컬렉션 확인 → `db.getCollectionNames)_`
3. 제거 → `db.Collection${name}.drop()`
	- 데이터를 삽입할 때 컬렉션이 없으면 컬렉션을 만들어줌
4. 크기를 미리 설정해 크기를 초과하면 자동으로 가장 오래된 데이터를 삭제하는 Collection
	- Capped Collection
	- `db.createCollection(${name}, {capped:true, size:<${size}>})`

- 데이터 1개 삽입: `db.cappedCollection.insertOne({"X":1})`
- 데이터 조회: `db.cappedCollection.find()`