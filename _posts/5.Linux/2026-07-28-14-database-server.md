---
title: 데이터베이스 서버
description: Linux에서 MariaDB 설치 및 설정 정리
date: 2026-07-28
series: Linux
tags:
  - Linux
  - AutoEverSW
---

## 1) MariaDB
---

### 개요
- MariaDB는 MySQL의 대체제로 개발된 관계형 데이터베이스 관리 시스템

### 설치

```sh
# 패키지 설치
sudo apt install -y mariadb-server

# 서비스 시작
sudo systemctl start mariadb

# 부팅 시 자동 시작
sudo systemctl enable mariadb

# 서비스 확인
sudo systemctl status mariadb
```

### 사용

```sh
# MariaDB 접속
sudo mysql
```

### 관리자 계정 변경

```sh
# 관리자 비밀번호 변경
sudo mysqladmin -u root password '비밀번호'

# 관리자로 접속
sudo mysql -u root -p
```

### 외부 접속 허용

#### 계정 생성 및 권한 부여

```sql
CREATE USER '계정이름'@'접속위치 또는 %' IDENTIFIED BY '비밀번호';
GRANT ALL PRIVILEGES ON 데이터베이스.테이블 TO '계정'@'접속위치';
FLUSH PRIVILEGES;
```

```sh
# 계정을 이용해서 접속
sudo mysql -u 계정 -p
```

#### 바인딩 설정 변경

```sh
sudo nano /etc/mysql/mariadb.conf.d/50-server.cnf
```

- `bind-address` 설정
    - `0.0.0.0`: 모든 곳에서 접속 가능
    - `127.0.0.1`: 로컬 컴퓨터에서만 접속 가능
    - 특정 IP: 해당 컴퓨터에서만 접속 가능
- 설정 파일은 시스템이 시작할 때 한 번만 읽음 → **서비스 재시작 필요**

```sh
sudo systemctl restart mariadb
```

#### 방화벽 허용

```sh
sudo ufw allow 3306/tcp
```

#### 클라이언트에서 접속

```sh
# mysql 클라이언트 설치
sudo apt install -y mysql-client

# 원격 접속
mysql -h <원격서버IP> -P <포트번호> -u 사용자이름 -p
```