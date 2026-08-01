---
title: GROUP BY와 집계
description: MariaDB GROUP BY, HAVING, 집계 함수, 윈도우 함수 정리
date: 2026-07-13
series: MariaDB
tags:
  - MariaDB
  - AutoEver SW School
---

## 1. 집계 함수 (Aggregate Functions)

- **정의**: 여러 행의 데이터를 입력받아 하나의 요약된 결과(합계, 평균 등)를 반환하는 함수임.
- **특징**: `WHERE` 절에서는 집계 함수를 직접 사용할 수 없음(실행 순서 때문임). NULL 값은 계산에서 제외됨.

|함수명|설명|예제|결과(예시)|
|:--|:--|:--|:--|
|**SUM**|지정한 열의 합계를 구함|`sql SELECT SUM(popu) FROM tCity;`|`1571`|
|**AVG**|지정한 열의 평균을 구함|`sql SELECT AVG(salary) FROM tStaff;`|`336.5`|
|**COUNT**|행의 개수를 구함|`sql SELECT COUNT(*) FROM tCity;`|`8`|
|**MAX**|최댓값을 구함|`sql SELECT MAX(area) FROM tCity;`|`1819`|
|**MIN**|최솟값을 구함|`sql SELECT MIN(area) FROM tCity;`|`42`|

### 1.1 COUNT 함수의 차이

- `COUNT(*)`: NULL을 포함한 모든 행의 개수를 센다.
- `COUNT(컬럼명)`: 해당 컬럼이 NULL인 행을 제외하고 개수를 센다.
- **예제**: `sql SELECT COUNT(score) FROM tStaff;` (성과급 점수가 있는 직원 수만 출력됨)

---

## 2. GROUP BY (데이터 그룹화)

- **목적**: 특정 컬럼을 기준으로 데이터를 그룹으로 묶어 집계 결과를 보고자 할 때 사용함.
- **규칙**: `SELECT` 절에 집계 함수가 아닌 컬럼이 온다면, 그 컬럼은 반드시 `GROUP BY` 절에 명시되어야 함.
- WHERE 절에서는 GROUP BY 를 수행할 수 없음
- GROUP BY를 수행한 후 집계 함수를 조회하는 경우 특별한 경우가 아니면 그룹화 한 항목을 같이 출력함
- GROUP BY를 수행한 경우 SELECT 절에는 그룹화 한 항목과 집계 함수만 출력하는 것이 일반적임
- 그룹화 한 항목이 아닌 컬럼을 조회하는 경우
	- ORACLE: 에러
	- MySQL,Maria DB: 그룹화 한 항목 중 첫 번째 데이터를 조회

### 2.1 기본 사용법

- **문법**:

```sql
SELECT 컬럼명, 집계함수(컬럼명)
FROM 테이블명
GROUP BY 컬럼명;
```

- **실습**: 지역별 인구수 합계 조회

```sql
SELECT region, SUM(popu)
FROM tCity
GROUP BY region;
```

- **결과**: '경기', '경상' 등 지역별로 그룹화되어 인구 합계가 출력됨.

---

## 3. HAVING (그룹 필터링)

- **정의**: `GROUP BY`로 그룹화된 결과에 조건을 걸 때 사용함.
- **차이점**: `WHERE`는 그룹화 전 개별 행에 대한 조건이고, `HAVING`은 그룹화 후의 결과 세트에 대한 조건임.

### 3.1 사용 예제

- **연습**: 평균 면적이 500 이상인 지역만 조회

```sql
SELECT region, AVG(area)
FROM tCity
GROUP BY region
HAVING AVG(area) >= 500;
```

- **설명**: 먼저 지역별로 묶고 평균을 낸 뒤, 그 평균이 500이 넘는 그룹만 남김.

---

## 4. 실무 보강 및 복합 쿼리

### 4.1 SQL 실행 순서 재확인

1. `FROM`: 테이블 참조
2. `WHERE`: 행 필터링
3. `GROUP BY`: 그룹화
4. `HAVING`: 그룹 필터링
5. `SELECT`: 컬럼 선택 및 집계 계산
6. `ORDER BY`: 결과 정렬

### 4.2 중복 제거 후 집계 (DISTINCT)

- 집계 함수 내부에서 `DISTINCT`를 사용하여 중복을 제외하고 계산할 수 있음.
- **예제**: 직원이 속한 부서의 종류가 몇 개인지 조회

```sql
SELECT COUNT(DISTINCT depart) FROM tStaff;
```

### 4.3 ROLLUP (중계 합계)

- 그룹별 소계와 전체 합계를 한 번에 구할 때 사용함. (MariaDB/MySQL 문법)
- **예제**:

```
SELECT region, SUM(popu)
FROM tCity
GROUP BY region WITH ROLLUP;
```

- **결과**: 각 지역별 합계 마지막 행에 전체 총합이 추가로 표시됨.

---

**추가 팁**:

- 집계 함수는 `NULL`을 0으로 처리하지 않고 무시함. 만약 `NULL`을 0으로 포함하여 평균을 내고 싶다면 `IFNULL(score, 0)`을 먼저 적용한 뒤 `AVG`를 써야 함.
- `COUNT(*)`는 성능 최적화가 잘 되어 있어 테이블의 전체 행수를 구할 때 가장 권장됨.