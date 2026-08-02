---
title: MariaDB 개요
description: 데이터베이스 개념, DBMS 종류, MariaDB 설치 및 기본 명령어 정리
date: 2026-07-10
series: MariaDB
tags:
  - MariaDB
  - AutoEverSW
---

## 1) 데이터베이스 개요
---
### 데이터와 정보
- **데이터(Data)**: 관찰이나 측정을 통해 얻은 값
- **정보(Information)**: 데이터를 가공하여 의미 있게 만든 결과

### 효율적인 데이터 관리를 위한 조건
- 중복 최소화, 일관성 유지, 무결성 보장, 보안, 검색 효율

## 2) DBMS
---
### 조건
- 실시간 접근성, 지속적인 변화, 동시 공유, 내용 참조

### 종류

| 구분 | 설명 | 대표 |
| ---- | ---- | ---- |
| **RDBMS** | 관계형, 테이블 기반 | MariaDB, MySQL, Oracle |
| **NoSQL** | 비관계형, 유연한 스키마 | MongoDB, Redis |

## 3) MariaDB 설치
---
### 설치
```sql
sudo apt install mariadb-server
sudo mysql_secure_installation
```

### 외부 접속 허용
```sql
bind-address = 0.0.0.0  # /etc/mysql/mariadb.conf.d/50-server.cnf
```

### 유저 생성
```sql
CREATE USER 'user'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON *.* TO 'user'@'%';
FLUSH PRIVILEGES;
```

## 4) 데이터베이스 관련 명령
---
```sql
SHOW DATABASES;
CREATE DATABASE dbname;
USE dbname;
DROP DATABASE dbname;
```

## 5) 주석
---
```sql
-- 한 줄 주석
# 한 줄 주석
/* 여러 줄 주석 */
```