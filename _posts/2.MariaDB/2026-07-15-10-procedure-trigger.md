---
title: 프로시저와 트리거
description: MariaDB Stored Procedure, Trigger, 프로그래밍 기능 정리
date: 2026-07-15
series: MariaDB
tags:
  - MariaDB
  - AutoEverSW
---

## 1) Stored Procedure
---
### 개요
- 데이터베이스에 저장된 **프로그래밍 로직**
- SQL 문을 함수처럼 실행 가능

### 생성
```sql
DELIMITER $$
CREATE PROCEDURE 프로시저명(IN param INT)
BEGIN
    SELECT * FROM 테이블 WHERE 컬럼 = param;
END$$
DELIMITER ;
```

### 호출
```sql
CALL 프로시저명(값);
```

### 삭제
```sql
DROP PROCEDURE 프로시저명;
```

## 2) Trigger
---
### 개요
특정 테이블에 INSERT/UPDATE/DELETE 발생 시 **자동 실행**

```sql
CREATE TRIGGER 트리거명
{BEFORE | AFTER} {INSERT | UPDATE | DELETE} ON 테이블명
FOR EACH ROW
BEGIN
    -- 실행 코드
END;
```