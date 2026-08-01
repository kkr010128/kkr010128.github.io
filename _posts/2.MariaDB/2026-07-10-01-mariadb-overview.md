---
title: MariaDB 개요
description: 데이터베이스 개념, DBMS 종류, MariaDB 설치 및 기본 명령어 정리
date: 2026-07-10
series: MariaDB
tags:
  - MariaDB
  - AutoEver SW School
---

## 1. MariaDB 개요

- SQL에 기반을 둔 관계형 DBMS로 Open Source로 제공됨.
- 리눅스, 유닉스, 윈도우 등 거의 모든 운영체제에서 사용 가능함.
- 처리 속도가 빨라 대용량 데이터 처리에 용이하고 설치가 쉬움.
- **작업 단위**: 데이터베이스 > 테이블 순임.
- 데이터베이스는 사용자 상관없이 생성되며 권한을 부여해서 사용함. 하나의 DB를 여러 사용자가 공유 가능함.

## 2. 서버 설치 및 관리

### 2.1 Windows 설치

- **다운로드**: https://mariadb.org/download/.
- **설정 사항**:
    - root 비밀번호 설정 및 원격 접속 허용 여부 결정.
    - 기본 인코딩을 UTF8로 설정할 것을 권장함.
    - 서비스 이름(기본 MariaDB), 포트 번호(기본 3306), 버퍼 사이즈 등을 설정함.

### 2.2 Mac (Homebrew) 설치

- **brew 설치**:
    - Intel Chip: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`.
    - ARM Chip: `/bin/bash -c "$(curl -fsSL https://gist.githubusercontent.com/nrubin29/bea5aa83e8dfa91370fe83b62dad6dfa/raw/48f48f7fef21abb308e129a80b3214c2538fc611/homebrew_m1.sh )"`.
- **설치 및 확인**: `brew install mariadb` 수행 후 `mysql --version`으로 확인함.
- **서비스 제어**: `brew services [start | stop | restart] mariadb` 사용함.
- **접속 및 설정**: `sudo mysql -u root` 접속 후 `ALTER USER` 명령어로 비밀번호 설정함.
- **설정 파일 경로**: `/opt/homebrew/etc/my.cnf`.
- **삭제**: `brew uninstall mariadb` 후 `/usr/local/var/mysql`, `/usr/local/etc/my.cnf` 등 데이터 모두 삭제함.

### 2.3 Ubuntu Linux 설치

- 패키지 업데이트: `sudo apt update && sudo apt upgrade -y`.
- 설치: `sudo apt install mariadb-server mariadb-client -y`.
- 보안 설정: `sudo mysql_secure_installation`으로 root 비번 및 익명 사용자 정리함.
- 설정 파일: `/etc/mysql/mariadb.conf.d/50-server.cnf`.

### 2.4 Docker 설치

- 이미지 다운로드: `docker pull mariadb`.
- 컨테이너 생성: `docker run --name mariadb -d -p [외부포트]:3306 -e MYSQL_ROOT_PASSWORD=[비밀번호] mariadb`.

## 3. 외부 접속 및 권한 설정

### 3.1 설정 파일 수정

- Mac/Linux 직접 설치 시: 설정 파일 내 `bind-address = 127.0.0.1`을 `0.0.0.0`으로 수정함.
- Docker 설치 시: `docker exec -it [컨테이너명] bash` 접속 후 vim 설치하여 설정 파일(`50-server.cnf`) 수정함.

### 3.2 사용자 및 권한 관리

- **유저 생성**: `CREATE USER '계정'@'%' IDENTIFIED BY '비밀번호';` (`%`는 모든 IP 허용).
- **권한 부여**: `GRANT ALL PRIVILEGES ON *.* TO '계정'@'%';`.
- **적용**: `FLUSH PRIVILEGES;` 반드시 수행해야 함.

## 4. 데이터베이스 주요 명령어

- 존재하는 목록 보기: `SHOW DATABASES;`.
- 현재 DB 확인: `SELECT DATABASE();`.
- 생성/삭제: `CREATE DATABASE [이름];` / `DROP DATABASE [이름];`.
- 사용 설정: `USE [이름];`.
- 테이블 목록 보기: `SHOW TABLES;`.
- 테이블 구조 확인: `DESC [테이블명];`.

## 5. 실습용 샘플 데이터 (DDL/DML)

### 5.1 tCity (도시 정보)

```sql
CREATE TABLE tCity (
    name CHAR(10) PRIMARY KEY, area INT NULL, popu INT NULL,
    metro CHAR(1) NOT NULL, region CHAR(6) NOT NULL
);
INSERT INTO tCity VALUES ('서울',605,974,'y','경기'), ('부산',765,342,'y','경상'), ('오산',42,21,'n','경기');
SELECT * FROM tCity;
```

### 5.2 tStaff (직원 정보)

```sql
CREATE TABLE tStaff (
    name CHAR(15) PRIMARY KEY, depart CHAR(10) NOT NULL, gender CHAR(3) NOT NULL,
    joindate DATE NOT NULL, grade CHAR(10) NOT NULL, salary INT NOT NULL, score DECIMAL(5,2) NULL
);
INSERT INTO tStaff VALUES ('김유신','총무부','남','2000-02-03','이사',420,88.8);
SELECT * FROM tStaff;
```

### 5.3 DEPT & EMP (부서 및 사원 - 외래키 포함)

```sql
CREATE TABLE DEPT (
    DEPTNO INT(2) PRIMARY KEY, DNAME VARCHAR(14), LOC VARCHAR(13)
);
CREATE TABLE EMP (
    EMPNO INT(4) PRIMARY KEY, ENAME VARCHAR(10), JOB VARCHAR(9), MGR INT(4),
    HIREDATE DATE, SAL FLOAT(7,2), COMM FLOAT(7,2), DEPTNO INT(2),
    CONSTRAINT FK_DEPTNO FOREIGN KEY(DEPTNO) REFERENCES DEPT(DEPTNO)
);
```

### 5.4 쇼핑몰 샘플 (usertbl & buytbl)

- `buytbl` 생성 시 `ON DELETE CASCADE` 설정을 통해 사용자 삭제 시 구매 기록도 자동 삭제되도록 구현함.
- `auto_increment` 속성으로 기본키 자동 증가 기능을 사용함.

### 5.5 대용량 데이터 처리

- 외부 SQL 파일 실행: `SOURCE employees.sql` 명령을 통해 대량의 샘플 데이터를 한 번에 입력 가능함.

---

**추가 팁 (자료 보강)**:

- MariaDB 접속 시 `-p` 옵션 뒤에 비밀번호를 바로 붙여 쓰거나(예: `-p1234`), 엔터를 치고 입력하는 것이 보안상 안전함.
- SQL문은 대소문자를 구분하지 않으나 관례상 예약어는 대문자, 식별자는 소문자로 작성하여 가독성을 높임.
- 외부 접속이 안 될 경우 OS 방화벽에서 3306 포트가 열려 있는지 확인이 필요함.

![[1.MariaDB(드래그함).pdf]]