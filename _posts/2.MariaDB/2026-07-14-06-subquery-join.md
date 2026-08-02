---
title: 서브쿼리와 JOIN
description: MariaDB SET 연산, SubQuery, JOIN 종류 및 활용 정리
date: 2026-07-14
series: MariaDB
tags:
  - MariaDB
  - AutoEverSW
---

## 1) SET 연산
---

| 연산자                | 설명          |
| ------------------ | ----------- |
| `UNION`            | 합집합 (중복 제거) |
| `UNION ALL`        | 합집합 (중복 포함) |
| `INTERSECT`        | 교집합         |
| `EXCEPT` / `MINUS` | 차집합         |

```sql
SELECT name FROM table1
UNION
SELECT name FROM table2;
```

## 2) SubQuery
---
### 개요
- 쿼리 안에 포함된 또 다른 쿼리
- `WHERE`, `FROM`, `SELECT` 절에 사용 가능

### 종류

| 구분 | 설명 |
| ---- | ---- |
| **단일 행 서브쿼리** | 결과가 1개 (`=`, `>`, `<` 등 사용) |
| **다중 행 서브쿼리** | 결과가 여러 개 (`IN`, `ANY`, `ALL` 사용) |
| **상관 서브쿼리** | 외부 쿼리의 컬럼 참조 (`EXISTS`) |

```sql
-- 단일 행
SELECT * FROM employees WHERE salary > (SELECT AVG(salary) FROM employees);

-- 다중 행
SELECT * FROM employees WHERE department_id IN (SELECT id FROM departments WHERE location = 'Seoul');

-- 상관
SELECT * FROM employees e WHERE EXISTS (SELECT 1 FROM departments d WHERE d.id = e.dept_id);
```

## 3) JOIN
---
### INNER JOIN (내부 조인)
```sql
SELECT * FROM A INNER JOIN B ON A.key = B.key;
SELECT * FROM A, B WHERE A.key = B.key;       -- 오라클 방식
```

### OUTER JOIN (외부 조인)
```sql
LEFT JOIN    -- 왼쪽 테이블 기준 매칭
RIGHT JOIN   -- 오른쪽 테이블 기준 매칭
```

### SELF JOIN (자체 조인)
```sql
SELECT e1.name AS employee, e2.name AS manager
FROM employees e1 LEFT JOIN employees e2 ON e1.manager_id = e2.id;
```

### CROSS JOIN (교차 조인)
```sql
SELECT * FROM A CROSS JOIN B;  -- 모든 조합 (카테시안 곱)
```