---
title: 성능 최적화
description: MariaDB 인덱스, 실행 계획, 성능 튜닝 기초 정리
date: 2026-07-15
series: MariaDB
tags:
  - MariaDB
  - AutoEverSW
---

## 1) 인덱스 (INDEX)
---
### 개요
- 데이터 검색 속도를 향상시키는 **색인** 구조
- 책 뒷부분의 **찾아보기**와 같은 개념

### 종류

| 인덱스 | 설명 |
| ------ | ---- |
| **PRIMARY KEY** | 자동 생성, 중복 불가, NULL 불가 |
| **UNIQUE INDEX** | 중복 불가 |
| **NORMAL INDEX** | 일반 인덱스, 중복 허용 |
| **FULLTEXT INDEX** | 전문 검색용 |
| **COMPOSITE INDEX** | 여러 컬럼 조합 |

### 생성
```sql
CREATE INDEX 인덱스명 ON 테이블(컬럼);
CREATE UNIQUE INDEX 인덱스명 ON 테이블(컬럼);
```

### 주의사항
- 인덱스는 **읽기 성능 향상** but **쓰기 성능 저하** (INSERT/UPDATE/DELETE 시 인덱스 재구성 필요)

## 2) 실행 계획
---
```sql
EXPLAIN SELECT * FROM 테이블 WHERE 조건;
```

## 3) 인덱스 사용 팁
---
- `WHERE` 절에 자주 사용되는 컬럼에 인덱스 생성
- `JOIN`에 사용되는 컬럼에 인덱스 생성
- `ORDER BY`에 사용되는 컬럼에 인덱스 고려
- 데이터 중복도가 높은 컬럼은 인덱스 효과가 낮음
- 과도한 인덱스는 오히려 성능 저하