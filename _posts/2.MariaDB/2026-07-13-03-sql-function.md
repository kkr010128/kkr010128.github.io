---
title: SQL 함수
description: MariaDB 문자, 수치, 날짜, NULL 관련 함수 및 윈도우 함수 정리
date: 2026-07-13
series: MariaDB
tags:
  - MariaDB
  - AutoEverSW
---

## 1) 문자 함수
---

| 함수                                        | 설명       |
| ----------------------------------------- | -------- |
| `CONCAT(a, b)`                            | 문자열 결합   |
| `LENGTH(str)`                             | 문자열 길이   |
| `SUBSTRING(str, pos, len)`                | 부분 문자열   |
| `REPLACE(str, old, new)`                  | 문자열 치환   |
| `UPPER(str)` / `LOWER(str)`               | 대/소문자 변환 |
| `TRIM(str)`                               | 공백 제거    |
| `LPAD(str, n, pad)` / `RPAD(str, n, pad)` | 자리수 채움   |

## 2) 수치 함수
---

| 함수                     | 설명      |
| ---------------------- | ------- |
| `ABS(n)`               | 절대값     |
| `ROUND(n, d)`          | 반올림     |
| `CEIL(n)` / `FLOOR(n)` | 올림 / 내림 |
| `MOD(a, b)`            | 나머지     |
| `POWER(a, b)`          | 거듭제곱    |

## 3) 날짜 함수
---

| 함수                               | 설명       |
| -------------------------------- | -------- |
| `NOW()`                          | 현재 날짜+시간 |
| `CURDATE()`                      | 현재 날짜    |
| `YEAR(date)` / `MONTH(date)`     | 연도/월 추출  |
| `DATE_ADD(date, INTERVAL n DAY)` | 날짜 더하기   |
| `DATEDIFF(a, b)`                 | 날짜 차이    |
| `DATE_FORMAT(date, fmt)`         | 날짜 포맷    |

## 4) NULL 관련 함수
---
```sql
IFNULL(컬럼, 대체값)       -- NULL이면 대체값 반환
COALESCE(값1, 값2, ...)    -- 첫 번째 NULL 아닌 값 반환
NULLIF(값1, 값2)           -- 두 값 같으면 NULL
```

## 5) 윈도우 함수
---
```sql
ROW_NUMBER() OVER (ORDER BY 컬럼)    -- 순번
RANK() OVER (ORDER BY 컬럼)          -- 순위 (공동 순위 있음)
DENSE_RANK() OVER (ORDER BY 컬럼)    -- 순위 (공동 순위 건너뜀 없음)
```