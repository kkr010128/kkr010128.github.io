---
title: TCL (트랜잭션)
description: 트랜잭션 개념, COMMIT, ROLLBACK, 격리 수준 정리
date: 2026-07-15
series: MariaDB
tags:
  - MariaDB
  - AutoEverSW
---

## 1) 트랜잭션(Transaction)
---
### 개요
하나의 논리적 작업 단위로, **모두 성공(COMMIT)** 하거나 **모두 실패(ROLLBACK)** 해야 함

### ACID

| 속성 | 설명 |
| ---- | ---- |
| **A**tomicity (원자성) | 전부 실행 또는 전부 취소 |
| **C**onsistency (일관성) | 실행 전후 데이터 무결성 유지 |
| **I**solation (격리성) | 동시 트랜잭션 간 간섭 방지 |
| **D**urability (지속성) | 성공한 트랜잭션은 영구 저장 |

## 2) TCL 명령어
---
```sql
START TRANSACTION;     -- 트랜잭션 시작
COMMIT;                -- 변경사항 영구 저장
ROLLBACK;              -- 변경사항 취소
SAVEPOINT 이름;        -- 중간 저장점
ROLLBACK TO 이름;      -- 저장점으로 복귀
```

## 3) 격리 수준
---

| 수준                   | 설명               | 문제점                 |
| -------------------- | ---------------- | ------------------- |
| **READ UNCOMMITTED** | 커밋 안 된 데이터 읽기 가능 | Dirty Read          |
| **READ COMMITTED**   | 커밋된 데이터만 읽기      | Non-Repeatable Read |
| **REPEATABLE READ**  | 같은 조회 결과 보장      | Phantom Read        |
| **SERIALIZABLE**     | 완벽한 격리           | 성능 저하               |

- `InnoDB`의 기본 격리 수준은 **REPEATABLE READ**