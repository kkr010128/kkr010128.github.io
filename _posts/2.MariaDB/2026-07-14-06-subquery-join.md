---
title: 서브쿼리와 JOIN
description: MariaDB SET 연산, SubQuery, JOIN 종류 및 활용 정리
date: 2026-07-14
series: MariaDB
tags:
  - MariaDB
  - AutoEver SW School
---

## 1. SET 연산자 (SET OPERATOR)

- **정의**: 여러 개의 SELECT 문 결과를 하나로 결합하는 연산임.
	- 2개 이상의 테이블에서 데이터를 추출하는 방법
- **제약 사항**:
    - 두 개 이상의 SELECT 문의 <mark style="background: #CACFD9A6;">컬럼 개수와 데이터 타입이 순서대로 일치해야 함</mark>.
    - 컬럼 이름은 첫 번째 SELECT 문을 기준으로 출력됨.
    - `ORDER BY`는 문장의 마지막에 한 번만 기술 가능함.
    - BLOB, CLOB 등 대용량 컬럼에는 사용 불가능함.

|연산자|설명|특징|
|:--|:--|:--|
|**UNION**|합집합|중복된 행을 제거하고 정렬하여 결과를 반환함.|
|**UNION ALL**|합집합|중복을 포함한 모든 결과를 반환하며 속도가 빠름.|
|**INTERSECT**|교집합|양쪽 결과에 공통으로 존재하는 행만 반환함.|
|**EXCEPT**|차집합|첫 번째 결과에서 두 번째 결과를 제외함 (MariaDB/Oracle은 MINUS).|

### 1.1 예제 및 결과
- EMP 테이블에는 DEPTNO가 10, 20, 30이 존재하고, DEPT 테이블에는 DEPTNO가 10, 20 ,30 , 40이 존재
- 

```sql
-- UNION: 부서번호 합집합 (중복 제거)
SELECT DEPTNO FROM DEPT
UNION
SELECT DEPTNO FROM EMP;
-- 결과: 10, 20, 30, 40 순차 출력

-- UNION ALL: 부서번호 합집합 (중복 포함)
SELECT DEPTNO FROM DEPT
UNION ALL
SELECT DEPTNO FROM EMP;
-- 결과: DEPT의 10,20,30,40 뒤에 EMP의 모든 DEPTNO가 나열됨
```

---

## 2. 서브쿼리 (Sub Query)

- **정의**: 하나의 SQL 문장 안에 포함된 또 다른 SELECT 문임.
- **특징**: 반드시 괄호`()`로 감싸야 하며, 연산자의 오른쪽에 위치함.

### 2.1 단일 행 서브쿼리

- 결과가 오직 1개의 행인 경우임. `=`, `>`, `<` 등의 비교 연산자 사용함.
- **예제**: 인구수가 최대인 도시 이름 조회

```sql
SELECT name FROM tCity
WHERE popu = (SELECT MAX(popu) FROM tCity);
-- 결과: '서울'
```

### 2.2 다중 행 서브쿼리

- 결과가 2건 이상인 경우임. `IN`, `ANY`, `ALL`, `EXISTS` 연산자를 사용해야 함.

|연산자|설명|
|:--|:--|
|**IN**|서브쿼리 결과 중 하나라도 일치하면 참임.|
|**ANY / SOME**|서브쿼리 결과 중 하나 이상 조건을 만족하면 참임. (`> ANY`는 최소값보다 크면 참)|
|**ALL**|서브쿼리 결과 모든 값을 만족해야 참임. (`> ALL`은 최대값보다 크면 참)|
|**EXISTS**|서브쿼리 결과가 존재하기만 하면 참임.|

- **예제 (ALL)**: 30번 부서 최고 급여자보다 더 많이 받는 사원 조회

```sql
SELECT ENAME, SAL FROM EMP
WHERE SAL > ALL(SELECT SAL FROM EMP WHERE DEPTNO = 30);
```

---

## 3. 조인 (JOIN)

- **정의**: 두 개 이상의 테이블을 결합하여 데이터를 조회하는 방법임.

### 3.1 CROSS JOIN (카테시안 곱)

- 두 테이블의 모든 행을 무조건 결합함. 결과 행 수는 `테이블A 행수 * 테이블B 행수`임.

```sql
SELECT * FROM EMP, DEPT; -- 또는 EMP CROSS JOIN DEPT
```

### 3.2 EQUI JOIN (등가 조인)

- 두 테이블의 공통 컬럼 값이 정확히 일치하는 경우 연결함. 가장 많이 쓰임.
- **예제 (Oracle/Traditional)**:

```sql
SELECT E.ENAME, D.DNAME
FROM EMP E, DEPT D
WHERE E.DEPTNO = D.DEPTNO;
```

### 3.3 ANSI JOIN (표준 조인)

- `INNER JOIN`과 `ON` 절을 사용하여 조인 조건과 필터링 조건을 분리함.

```sql
-- ANSI INNER JOIN
SELECT E.ENAME, D.DNAME
FROM EMP E INNER JOIN DEPT D ON E.DEPTNO = D.DEPTNO
WHERE E.ENAME = 'MILLER';

-- USING 사용 (컬럼명이 같을 때)
SELECT ENAME, DNAME FROM EMP JOIN DEPT USING (DEPTNO);
```

### 3.4 OUTER JOIN (외부 조인)

- 조인 조건에 맞지 않는 데이터(한쪽에만 있는 데이터)도 포함하여 출력함.
- **LEFT OUTER JOIN**: 왼쪽 테이블의 모든 데이터 출력.
- **RIGHT OUTER JOIN**: 오른쪽 테이블의 모든 데이터 출력.

```sql
-- 부서 정보는 있으나 사원이 없는 40번 부서까지 출력
SELECT E.ENAME, D.DEPTNO, D.DNAME
FROM EMP E RIGHT OUTER JOIN DEPT D ON E.DEPTNO = D.DEPTNO;
```

### 3.5 SELF JOIN (자체 조인)

- 하나의 테이블을 별칭(Alias)을 이용해 두 개처럼 사용하여 조인함.
- **예제**: 사원의 이름과 매니저 이름을 함께 조회

```sql
SELECT CONCAT(E.ENAME, '의 매니저는 ', M.ENAME)
FROM EMP E, EMP M
WHERE E.MGR = M.EMPNO;
```

---

> [!tip] **실무 팁**
> 
> - **성능 최적화**: 서브쿼리보다 조인이 대용량 데이터 처리 시 성능상 유리한 경우가 많음. (옵티마이저가 조인을 더 잘 최적화함)
> - **EXISTS의 활용**: 데이터 존재 여부만 체크할 때는 `IN`보다 `EXISTS`가 속도가 훨씬 빠름.
> - **조인 순서**: 행 수가 적은 테이블(선행 테이블)을 먼저 읽도록 유도하는 것이 성능 최적화의 기본임.