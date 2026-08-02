---
title: DDL (테이블 관리)
description: 정규화, 테이블 생성/수정/삭제, 제약 조건, AUTO_INCREMENT 정리
date: 2026-07-13
series: MariaDB
tags:
  - MariaDB
  - AutoEverSW
---

## 1) 무결성 제약 조건
---

| 제약 조건         | 설명                      |
| ------------- | ----------------------- |
| `NOT NULL`    | NULL 허용 안 함             |
| `UNIQUE`      | 중복 불가                   |
| `PRIMARY KEY` | NOT NULL + UNIQUE (기본키) |
| `FOREIGN KEY` | 외래키 (참조 무결성)            |
| `CHECK`       | 조건 검사                   |

## 2) 이상 현상과 정규화
---
### 이상 현상 (Anomaly)

| 종류 | 설명 |
| ---- | ---- |
| **삽입 이상** | 불필요한 데이터도 함께 삽입해야 함 |
| **갱신 이상** | 중복 데이터 중 일부만 수정되어 불일치 발생 |
| **삭제 이상** | 필요 데이터까지 함께 삭제됨 |

### 정규화 (Normalization)
데이터 중복을 최소화하고 무결성을 유지하기 위한 테이블 분해 과정

## 3) 테이블 생성
---
```sql
CREATE TABLE 테이블명 (
    컬럼명 자료형 제약조건,
    컬럼명 자료형 제약조건,
    PRIMARY KEY (컬럼)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 4) 테이블 수정
---
```sql
ALTER TABLE 테이블명 ADD 컬럼명 자료형;          -- 컬럼 추가
ALTER TABLE 테이블명 MODIFY 컬럼명 새자료형;      -- 컬럼 수정
ALTER TABLE 테이블명 DROP COLUMN 컬럼명;          -- 컬럼 삭제
ALTER TABLE 테이블명 RENAME 새이름;               -- 테이블명 변경
```

## 5) 테이블 삭제
---
```sql
DROP TABLE 테이블명;           -- 테이블 완전 삭제
TRUNCATE TABLE 테이블명;       -- 데이터만 삭제 (구조 유지)
```

## 6) 제약 조건 (CONSTRAINT)
---
```sql
-- 기본키
ALTER TABLE 테이블명 ADD CONSTRAINT PK PRIMARY KEY (컬럼);

-- 외래키
ALTER TABLE 테이블명 ADD CONSTRAINT FK_이름
FOREIGN KEY (컬럼) REFERENCES 참조테이블(참조컬럼);

-- UNIQUE
ALTER TABLE 테이블명 ADD CONSTRAINT UQ_이름 UNIQUE (컬럼);
```

## 7) AUTO_INCREMENT
---
자동 증가 숫자, PRIMARY KEY에 주로 사용
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100)
);
```

### 특징
- `AUTO_INCREMENT` 컬럼에 NULL 입력 시 자동으로 증가된 값 저장
- 삭제된 번호는 재사용되지 않음
- `ENGINE=InnoDB` 권장 (트랜잭션 지원)