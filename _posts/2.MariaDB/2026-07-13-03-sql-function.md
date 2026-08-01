---
title: SQL 함수
description: MariaDB 문자, 수치, 날짜, NULL 관련 함수 및 윈도우 함수 정리
date: 2026-07-13
series: MariaDB
tags:
  - MariaDB
  - AutoEver SW School
---

## 1. 함수(Function) 개요

- **정의**: 입력 데이터를 이용해 연산을 수행한 후 출력 값을 만들어 내는 객체임.
- **구성**: 함수에 입력하는 데이터를 **매개변수(Argument, Parameter)**라 하고, 출력되는 데이터를 **반환 데이터(Return Data)**라고 함.
- **분류**:
    - **Scala 함수**: 값 하나를 계산하여 반환함.
    - **Group 함수**: 여러 개의 값으로부터 통계 값을 계산함.
- **기능별 분류**: 문자, 날짜/시간, 수치, 제어 흐름, 집계, 정보, 암호 함수 등으로 나뉨.

---

## 2. 문자열 함수 (String Functions)

| 함수명               | 설명 및 문법                         | 예제                                      | 실행 결과           |
| :---------------- | :------------------------------ | :-------------------------------------- | :-------------- |
| **LENGTH**        | 문자열의 바이트 수를 반환함                 | `SELECT LENGTH('abc');`                 | `3`             |
| **CONCAT**        | 여러 문자열을 하나로 결합함                 | `SELECT CONCAT('Hello', ' ', 'World');` | `'Hello World'` |
| **FORMAT**        | 숫자를 소수점 자릿수까지 표시하고 1000단위 콤마 삽입 | `SELECT FORMAT(1234567, 0);`            | `'1,234,567'`   |
| **INSTR**         | 기준 문자열에서 부분 문자열의 시작 위치를 찾음      | `SELECT INSTR('foobarbar', 'bar');`     | `4`             |
| **LEFT / RIGHT**  | 문자열을 왼쪽/오른쪽에서 길이만큼 자름           | `SELECT LEFT('ABCDEFG', 3);`            | `'ABC'`         |
| **UPPER / LOWER** | 대문자 또는 소문자로 변환함                 | `SELECT UPPER('mariadb');`              | `'MARIADB'`     |
| **LPAD / RPAD**   | 지정한 길이만큼 특정 문자로 채움              | `SELECT LPAD('hi', 5, '?');`            | `'---hi'`       |
| **TRIM**          | 좌우 공백 또는 특정 문자를 제거함             | `SELECT TRIM(' hello ');`               | `'hello'`       |
| **REPLACE**       | 문자열 내 특정 내용을 다른 내용으로 치환함        | `SELECT REPLACE('Apple', 'p', 'P');`    | `'APPle'`       |
| **SUBSTRING**     | 시작 위치부터 길이만큼 문자열을 추출함           | `SELECT SUBSTRING('2024-05-01', 6, 2);` | `'05'`          |

### 2.1 문자열 실습 예제

- **데이터 결합**: `SELECT CONCAT(name, birthyear) FROM usertbl;` -> '이름1990' 형태로 출력됨.
- **날짜 부분 추출**: `SELECT SUBSTRING(HIREDATE, 1, 4) 년도, SUBSTRING(HIREDATE, 6, 2) 달 FROM EMP;` -> 입사 년도와 월을 분리하여 조회함.

---

## 3. 수치 함수 (Numeric Functions)

- **ABS(숫자)**: 절대값을 반환함.
- **CEILING / FLOOR / ROUND**: 각각 올림, 내림, 반올림을 수행함.
    - `SELECT ROUND(123.456, 2);` -> `123.46` (소수점 둘째 자리까지 반올림).
- TRUNCATE: qjflsms gkatn
	- 자릿 수와 함께 사용하는데 자릿수를 설정할 때는 음수이면 소수점 앞 자릿수를 의미하고 양수이면 소숫점 자릿수
- **MOD(n, m)**: 나머지를 구함.
    - 예: `SELECT * FROM EMP WHERE MOD(EMPNO, 2) = 1;` -> 사원번호가 홀수인 사원만 조회함.
- **RAND()**: 0 이상 1 미만의 임의의 실수를 반환함.
- **POW(x, y) / SQRT(x)**: 거듭제곱 및 제곱근을 구함.
- **LEAST / GREATEST**: 나열된 값 중 최소값 또는 최대값을 반환함.

---

## 4. 날짜 및 시간 함수 (Date & Time Functions)

- **현재 시각 조회**:
    - 'YYYY-MM-DD' 리턴.
	    - `CURRENT_DATE()`
	- 'HH:MM:SS' 리턴.
	    - `CURRENT_TIME()`, `CURTIME()`, `LOCALTIME()`
    - 현재 날짜와 시간을 모두 리턴함
	    - `NOW()`
		- `LOCALTIME()`
	    - `LOCLTIMESTAMP()`
	    - `SYSDATE()`
	    - `CURRENT_TIMESTAMP()`
- **날짜 연산**:
    - `ADDDATE(날짜, INTERVAL 정수 단위)`: 날짜를 더함.
        - `SELECT ADDDATE('2025-01-01', INTERVAL 31 DAY);` -> `'2025-02-01'`.
    - `DATEDIFF(날짜1, 날짜2)`: 두 날짜 사이의 일수 차이를 구함.
    - `TIMESTAMPDIFF(단위, 날짜1, 날짜2)`: 연, 월, 시간 등 지정 단위로 차이를 구함.
        - `SELECT TIMESTAMPDIFF(MONTH, '1985-05-05', '2025-01-01');` -> 월 단위 차이 리턴.

---

## 5. 제어 흐름 및 NULL 함수

### 5.1 제어 흐름 함수

- **IF(조건, 참일때, 거짓일때)**: 조건에 따른 2중 분기.
    - `SELECT IF(100 > 200, '참', '거짓');` -> `'거짓'`.
- **CASE WHEN**: 다중 분기 처리에 사용됨.

```sql
SELECT CASE 10 WHEN 1 THEN '일' WHEN 10 THEN '십' ELSE '모름' END; -- 결과: '십'
```

### 5.2 NULL 관련 함수
- NULL은 아직 알려지지 않은 값
- NULL과의 연산은 무조건 NULL
- **IFNULL(값1, 값2)**: 값1이 NULL이면 값2를, 아니면 값1을 리턴함 (Oracle의 NVL과 유사).
- **COALESCE(인자1, 2, ...)**: 인자들 중 첫 번째로 NULL이 아닌 값을 반환함.
- **NVL2(인자1, 인자2, 인자3)**: 인자1이 NULL이 아니면 인자2를, NULL이면 인자3을 리턴함.

---

## 6. 시스템 정보 및 타입 변환

### 6.1 시스템 정보 함수

- **USER()**: 현재 접속 중인 사용자 이름을 반환함.
- **DATABASE()**: 현재 사용 중인 데이터베이스 이름을 반환함.
- **VERSION()**: MariaDB의 버전을 반환함.
- **JSON_OBJECT**: 데이터를 JSON 형식으로 변환함.
    - `SELECT JSON_OBJECT('name', '김철수', 'age', 30);` -> `{"name": "김철수", "age": 30}`.

### 6.2 타입 변환 (Explicit Conversion)

- **CAST(데이터 AS 데이터유형)**: 데이터를 지정한 유형으로 강제 변환함.
    - `SELECT CAST('1' AS SIGNED);` -> 숫자 1로 변환.
- **CONVERT(데이터, 데이터유형)**: CAST와 유사하게 작동함.
- **주의**: MySQL/MariaDB에서 CAST 시 `VARCHAR`로는 형 변환이 불가능하며 `CHAR`를 사용해야 함.

---

**실무 팁**:

- 날짜 검색 시 `HIREDATE LIKE '1981%'` 보다 `SUBSTRING(HIREDATE, 1, 4) = '1981'` 형식이 더 명확할 때가 있음.
- 숫자로 된 문자열을 산술 연산(`+`)에 사용하면 MariaDB가 자동으로 숫자로 변환하여 계산함(묵시적 형 변환).


## 흐름 순서
SELECT → FROM → WHERE →  GROUP BY → HAVING → ORDER BY • • • 
## 실습
---
```sql
select ENAME as '이름', substring(hiredate, 1, 10) as '입사년도' from EMP;
```
