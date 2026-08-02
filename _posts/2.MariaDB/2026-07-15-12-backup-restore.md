---
title: 백업과 복원
description: MariaDB 데이터베이스 백업 및 복원 방법 정리
date: 2026-07-15
series: MariaDB
tags:
  - MariaDB
  - AutoEverSW
---

## 1) 백업 (Backup)
---
```bash
# 전체 데이터베이스 백업
mysqldump -u 사용자 -p 데이터베이스명 > 백업파일.sql

# 모든 데이터베이스 백업
mysqldump -u 사용자 -p --all-databases > 전체백업.sql

# 특정 테이블만 백업
mysqldump -u 사용자 -p 데이터베이스명 테이블명 > 테이블백업.sql
```

## 2) 복원 (Restore)
---
```bash
mysql -u 사용자 -p 데이터베이스명 < 백업파일.sql
```

복원 전에 데이터베이스가 존재해야 함
```sql
CREATE DATABASE dbname;
```