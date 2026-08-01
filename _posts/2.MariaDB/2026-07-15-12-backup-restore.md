---
title: 백업과 복원
description: MariaDB 데이터베이스 백업 및 복원 방법 정리
date: 2026-07-15
series: MariaDB
tags:
  - MariaDB
  - AutoEver SW School
---

## 1. 데이터베이스 백업 (Backup)

- **정의**: 시스템 장애, 데이터 유실, 서버 이전 등에 대비하여 데이터베이스의 복사본을 만드는 과정임.
- **도구**: MariaDB에서 기본 제공하는 `mysqldump` 유틸리티를 사용함.

### 1.1 전체 데이터베이스 백업

- 서버 내에 존재하는 모든 데이터베이스를 하나의 SQL 파일로 추출함.
- **문법**:

```bash
mysqldump -u[아이디] -p[패스워드] --all-databases > [백업파일명].sql
```

- **예제**:

```bash
mysqldump -uroot -p1234 --all-databases > all_backup_2024.sql
```

- **실행 결과**: 현재 디렉토리에 `all_backup_2024.sql` 파일이 생성되며, 내부에는 모든 DB의 스키마와 데이터가 포함됨.

### 1.2 특정 데이터베이스 백업

- 하나의 데이터베이스만 선택하여 백업함으로써 효율적인 관리가 가능함.
- **문법**:

```bash
mysqldump -u[아이디] -p[패스워드] [데이터베이스명] > [백업파일명].sql
```

- **예제**:

```bash
mysqldump -uroot -p1234 sample_db > sample_backup.sql
```

### 1.3 특정 테이블 백업

- 데이터베이스 내의 특정 테이블만 골라서 백업할 수 있음.
- **문법**:

```bash
mysqldump -u[아이디] -p[패스워드] [데이터베이스명] [테이블명] > [백업파일명].sql
```

- **예제**:

```bash
mysqldump -uroot -p1234 sample_db tStaff > tStaff_backup.sql
```

### 1.4 원격 서버 백업

- 로컬이 아닌 네트워크로 연결된 외부 서버의 데이터를 백업할 때 `-h` 옵션을 사용함.
- **문법**:

```bash
mysqldump -u[아이디] -p[패스워드] -h[ip주소] [데이터베이스명] > [백업파일명].sql
```

- **예제**:

```bash
mysqldump -uroot -p1234 -h211.183.2.253 sample_db > remote_backup.sql
```

---

## 2. 데이터베이스 복원 (Restore)

- **정의**: 백업된 `.sql` 파일을 실행하여 데이터베이스를 원래 상태로 되돌리는 과정임.
- **주의**: 백업 시에는 `mysqldump`를 쓰지만, 복원 시에는 `mysql` 명령어를 사용하며 꺽쇠 방향(`<`)이 반대임.

### 2.1 전체 복원

- 백업 파일에 포함된 모든 내용을 서버에 적용함.
- **문법**:

```bash
mysql -u[아이디] -p[패스워드] < [백업파일명].sql
```

- **예제**:

```bash
mysql -uroot -p1234 < all_backup_2024.sql
```

- **실행 결과**: SQL 파일에 기록된 모든 쿼리가 실행되며 DB와 데이터가 복구됨.

### 2.2 특정 데이터베이스 복구

- 백업 파일의 내용을 특정 데이터베이스에만 덮어씀.
- **문법**:

```bash
mysql -u[아이디] -p[패스워드] [데이터베이스명] < [백업파일명].sql
```

- **예제**:

```bash
mysql -uroot -p1234 sample_db < sample_backup.sql
```

---

> [!tip] **실무 보강**
> 
> - **백업 주기**: 정기적인 스케줄러(Windows 작업 스케줄러, Linux Crontab)를 통해 자동 백업 환경을 구축하는 것이 권장됨.
> - **보안**: 백업 파일(.sql)은 평문 텍스트이므로 외부에 유출되지 않도록 별도의 저장소에 암호화하여 보관해야 함.