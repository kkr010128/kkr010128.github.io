---
title: GROUP BY와 집계
description: MariaDB GROUP BY, HAVING, 집계 함수, 윈도우 함수 정리
date: 2026-07-13
series: MariaDB
tags:
  - MariaDB
  - AutoEverSW
---

## 1) 집계 함수
---

| 함수          | 설명  |
| ----------- | --- |
| `COUNT(컬럼)` | 행 수 |
| `SUM(컬럼)`   | 합계  |
| `AVG(컬럼)`   | 평균  |
| `MAX(컬럼)`   | 최대값 |
| `MIN(컬럼)`   | 최소값 |

## 2) GROUP BY
---
특정 컬럼 기준으로 그룹화하여 집계

```sql
SELECT department, AVG(salary)
FROM employees
GROUP BY department;
```

## 3) HAVING
---
GROUP BY의 결과에 조건 적용 (WHERE는 그룹화 전, HAVING은 후)

```sql
SELECT department, AVG(salary) AS avg_sal
FROM employees
GROUP BY department
HAVING avg_sal >= 50000;
```

## 4) 윈도우 함수
---
### ROW_NUMBER / RANK / DENSE_RANK
```sql
SELECT name, salary,
    ROW_NUMBER() OVER (ORDER BY salary DESC) AS row_num,
    RANK() OVER (ORDER BY salary DESC) AS rank,
    DENSE_RANK() OVER (ORDER BY salary DESC) AS dense_rank
FROM employees;
```

### PARTITION BY
```sql
SELECT department, name, salary,
    ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) AS dept_rank
FROM employees;
```