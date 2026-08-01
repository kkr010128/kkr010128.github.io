---
title: DDL (테이블 관리)
description: 정규화, 테이블 생성/수정/삭제, 제약 조건, AUTO_INCREMENT 정리
date: 2026-07-13
series: MariaDB
tags:
  - MariaDB
  - AutoEver SW School
---

## 1. 관계형 데이터베이스 (RDBMS) 개요

- **정의**: 데이터베이스를 테이블(릴레이션)의 집합으로 설명하는 관리 시스템임.
- **역사**: 1970년 E.F. Codd에 의해 개발됨.
- **종류**:
    - 상용: Oracle, DB2, MS-SQL, SAP HANA 등.
    - 오픈 소스: MySQL, PostgreSQL, SQLite, MariaDB(MySQL의 포크) 등.

## 2. RDBMS 구성 용어

- **릴레이션(Relation)**: 정보 저장의 기본 형태인 2차원 구조의 테이블임. NoSQL에서는 Collection이라고도 부름.
    - **행(Row/Tuple)**: 하나의 개체를 나타냄.
    - **열(Column/Attribute/Field)**: 개체의 속성을 의미함.
- **도메인(Domain)**: 하나의 속성이 가질 수 있는 원자 값들의 집합임.
- **특징**: 튜플들은 모두 상이(Distinct)하며 순서가 없고, 속성 값은 분해할 수 없는 원자 값(Atomic value)이어야 함.

---

## 3. 키(Key)의 종류

|키 종류|설명|
|:--|:--|
|**후보키 (Candidate Key)**|유일성(Uniqueness)과 최소성(Minimality)을 만족하는 속성 집합임.|
|**기본키 (Primary Key)**|후보키 중 선정된 키로, 튜플을 유일하게 식별하며 테이블당 하나만 설정 가능함.|
|**대체키 (Alternate Key)**|기본키를 제외한 나머지 후보키들임.|
|**외래키 (Foreign Key)**|다른 테이블의 행을 식별할 수 있는 속성으로, 참조 테이블의 기본키 또는 유일키여야 함.|

---

## 4. 무결성 제약 조건 (Integrity Constraints)

- **개체 무결성 (Entity Integrity)**: 기본키는 NULL일 수 없고 중복될 수 없음.
- **참조 무결성 (Referential Integrity)**: 외래키 값은 참조하는 테이블에 존재하는 값이거나 NULL이어야 함.
- **도메인 무결성 (Domain Integrity)**: 속성 값은 지정된 타입, 범위, 기본값 등 도메인에 설정된 규칙을 따라야 함.

---

## 5. 데이터베이스 설계 및 모델링

### 5.1 설계 과정 및 생명주기

1. **요구 사항 분석**: 구축 범위를 정하는 과정임.
2. **개념적 설계**: 엔티티, 속성, 관계를 식별하여 ER 다이어그램을 도출함.
3. **논리적 설계**: DBMS에 맞는 테이블 구조로 변환하고 정규화를 수행함.
4. **물리적 설계**: 실제 저장 구조 및 인덱스 접근 경로를 도출함.

### 5.2 데이터 이상 현상 (Anomaly)

데이터 중복으로 인해 발생하는 문제들임.

- **삽입 이상**: 새 데이터를 넣기 위해 불필요한 데이터도 함께 삽입해야 함.
- **삭제 이상**: 한 데이터 삭제 시 꼭 필요한 다른 데이터까지 연쇄 삭제됨.
- **갱신 이상**: 일부 중복 데이터만 수정되어 데이터 불일치(모순)가 발생함.

### 5.3 정규화 (Normalization)

- **제 1 정규형(1NF)**: 모든 도메인이 원자 값으로 구성됨.
- **제 2 정규형(2NF)**: 1NF 만족 및 **부분 함수적 종속** 제거.
- **제 3 정규형(3NF)**: 2NF 만족 및 **이행적 함수 종속** 제거.
- **BCNF**: 모든 결정자가 후보키가 되도록 함.

---

## 6. DDL 실무 문법 및 예제

### 6.1 CHECK 제약 조건

- **설명**: 컬럼에 저장될 값의 범위를 제한하여 데이터 유효성을 검사함.
- **문법**: `컬럼명 자료형 CHECK (조건)`
- **예제**:

```
CREATE TABLE tCheckTest(
    gender CHAR(3) NULL CHECK(gender = '남' OR gender = '여'),
    grade INT NULL CHECK (grade >= 1 AND grade <= 3),
    origin CHAR(3) NULL CHECK(origin IN ('동','서','남','북')),
    name CHAR(10) NULL CHECK(name LIKE '김%')
);
-- 실행 결과: '김좌진'은 삽입 가능하나 '청산리'는 김씨가 아니므로 에러 발생함.
```

### 6.2 UNIQUE 제약 조건

- **설명**: 필드 값의 중복을 방지함. 기본키와 달리 NULL을 허용함.
- **예제**:

```sql
CREATE TABLE tCityUnique (
    name CHAR(10) PRIMARY KEY,
    area INT NULL,
    popu INT NULL,
    CONSTRAINT Unique_tCity_area_popu UNIQUE(area, popu) -- 복합 유니크 설정.
);
```

### 6.3 PRIMARY KEY (기본키)

- **설명**: 행을 고유하게 식별함. NOT NULL 속성을 내포함.
- **예제 (복합키)**:

```sql
CREATE TABLE tCityCompoKey(
    name CHAR(10) NOT NULL,
    region CHAR(6) NOT NULL,
    area INT NULL,
    CONSTRAINT PK_tCity_name_region PRIMARY KEY (name, region) -- 두 컬럼 조합으로 PK 생성.
);
```

### 6.4 FOREIGN KEY (외래키)

- **설명**: 테이블 간 참조 관계를 정의함. `ON DELETE CASCADE` 등을 통해 부모 데이터 삭제 시 자식 데이터의 처리 방식을 결정함.
- **예제**:

```sql
CREATE TABLE tProject(
    projectID INT PRIMARY KEY,
    employee CHAR(10) NOT NULL,
    project VARCHAR(30) NOT NULL,
    CONSTRAINT FK_emp FOREIGN KEY(employee)
    REFERENCES tEmployee(name) ON DELETE CASCADE ON UPDATE CASCADE -- 부모 변경 시 연쇄 반영.
);
```

### 6.5 DEFAULT & AUTO_INCREMENT

- **DEFAULT**: 값을 명시하지 않을 때 자동 입력될 값을 지정함.
- **AUTO_INCREMENT**: 정수형 PK에 대해 자동으로 1씩 증가하는 번호를 부여함.
- **예제**:

```sql
CREATE TABLE tSale (
    saleno INT AUTO_INCREMENT PRIMARY KEY,
    customer NCHAR(10),
    product NCHAR(30) DEFAULT '지팡이'
);
-- 실행 결과: INSERT 시 product를 생략하면 '지팡이'가 자동 입력됨.
```

---

> [!tip] **실무 최적화 팁**
> 
> - **테이블 압축**: `CREATE TABLE` 시 `ROW_FORMAT=COMPRESSED`를 추가하면 용량은 절감되나 작업 시간이 길어질 수 있음.
> - **반정규화**: 빈번한 Join으로 인한 성능 저하 시, 시스템 성능 향상을 위해 의도적으로 중복을 허용하는 반정규화(Denormalization)를 고려할 수 있음.

```sql
select COUNT(COMM) from EMP;

SELECT COUNT(*)
FROM EMP;

SELECT COUNT(distinct DEPTNO)
FROM EMP;

-- 연습문제
-- tStaff 테이블에서 score가 80 이상인 직원은 몇 명인지 확인
SELECT COUNT(name) FROM tStaff WHERE (score >= 80);

-- tStaff 테이블에서 score가 없는 직원은 몇 명?
SELECT COUNT(*) FROM tStaff WHERE score IS NULL;

SELECT COUNT(*), SUM(salary)
FROM tStaff
WHERE score < 100;

-- EMP 테이블에서 DEPTNO 별 SAL의 평균 조회
SELECT ROUND(AVG(SAL)) as "평균"
FROM EMP
GROUP BY DEPTNO;

-- 되도록이면 그룹화 한 항목을 같이 조회
SELECT DEPTNO, ROUND(AVG(SAL)) AS "평균 급여"
FROM EMP
GROUP BY DEPTNO;

-- GROUP BY 이후에 집계 함수가 만들어지므로 WHERE 절에 집계 함수를 사용하면 에러
SELECT DEPTNO, ROUND(AVG(SAL)) AS "평균 급여"
FROM EMP
WHERE ROUND(AVG(SAL)) > 2000
GROUP BY DEPTNO;

-- MariaDB에서는 GOURP BY 절에서 묶은 속성 이외의 속성을 조회하면 첫 번째 데이터가 조회됨
SELECT DEPTNO, ENAME, ROUND(AVG(SAL)) AS "평균 급여"
FROM EMP
GROUP BY DEPTNO;



-- GROUP BY 다음에 나오는 출력할 그룹의 조건을 지정하는 절 → HAVING
-- 집계함수에 대한 조건은 이 절에 작성

-- EMP 테이블에서  DEPTNO 별로 SAL의 평균을 조회하는데 평균이 2000이 넘는 경우만 조회
SELECT DEPTNO, ROUND(AVG(SAL)) AS "평균 급여"
FROM EMP
GROUP BY DEPTNO
HAVING ROUND(AVG(SAL)) > 2000;

-- 연습문제
-- EMP 테이블에서 JOB 별로 최대 급여와 최소 급여(SAL)를 조회
SELECT JOB, MAX(SAL) as "최대 급여", MIN(SAL) as "최소 급여"
FROM EMP
GROUP BY JOB;

-- EMP 테이블에서 JOB 별 인원이 4명 이상인 데이터를 조회하는데 JOB과 인원수를 조회
SELECT JOB, COUNT(*) as "인원수"
FROM EMP
GROUP BY JOB
HAVING COUNT(*) >= 4;


-- # 윈도우 함수
-- 행과 행 사이의 관계를 쉽게 정의하기 위한 함수
-- 이 함수를 이용하면 복잡한 SQL을 쉽게 활용할 수 있음
	-- OVER 절이 포함된 함수
	-- 집계 함수와 비 집계 함수(CUME_DIST, DENSE_RANK, FIRST_VALUE 등)를 이용
	
	
-- 순위 함수
-- 함수 이름() OVER([PARTITION BY 그룹화할 항목 이름]) ORDER BY 정렬할 컬럼 이름이나 연산식

-- usertbl 테이블에서 name과 birthyear와 birthyear가 작은 것부터 순위를 매겨 같이 출력(중복없이 출력)
SELECT name, birthyear, ROW_NUMBER() over(ORDER BY birthyear ASC) '순위'
FROM usertbl;

-- birthyear가 같은 경우 name으로 오름차순으로 순위 설정
SELECT name, birthyear, ROW_NUMBER() over(ORDER BY birthyear ASC, name ASC) '순위'
FROM usertbl;

-- birthyear가 같은 경우 addr 별로 그룹화 해서 name으로 오름차순으로 순위 설정
SELECT name, birthyear, ROW_NUMBER() over(ORDER BY addr ASC, name ASC) '순위'
FROM usertbl;


-- 첫 번째 행과의 차이를 출력
SELECT name, birthyear, birthyear - (FIRST_VALUE(birthyear) OVER(ORDER BY birthyear)) AS "나이 차이"
FROM usertbl;

-- 이전 행과의 차이를 출력
SELECT name, birthyear, birthyear - (LAG(birthyear, 1) OVER(ORDER BY birthyear)) AS "나이 차이"
FROM usertbl;


-- WITH ROLLUP
-- GROUP BY 절의 마지막에 작성, 이 명령어가 포함되면 그룹별 합계와 총 합계를 출력

-- order_d 테이블에서 goodscd 별 qty의 합계를 조회
SELECT goodscd, SUM(qty)
FROM order_d
GROUP BY goodscd WITH ROLLUP;


-- DDL(Data Definition Language)
	-- 개체 무결성: 기본키는 NULL일 수 없다
	-- 참조 무결성: 외래키는 참조할 수 없는 값을 가질 수 없다. NULL을 가지는 것은 가능
	-- 함수적 종속: 어떤 속성 또는 속성의 집합이 다른 속성의 값을 하나로 결정할 때를 말함
		-- 완전 함수적 종속: 기본키가 두 개 이상의 속성으로 구성된 경우 두 개 전체를 알아야만 하나의 값을 알게 되는 경우
		-- 부분 함수적 종속: 기본키가 2개 이상의 속성으로 구성된 경우 1개 속성의 값만 알아도 하나의 값을 알게되는 경우
		-- 이행적 함수적 종속: A → B, B → C일 때, A → C를 만족하는 경우
		
	-- 데이터 중복으로 생기는 이상현상
	-- 1. 삽입 이상 → 삽입하고자 하는 데이터를 삽입하지 못하는 현상
	-- 2. 삭제 이상 → 데이터를 삭제할 때 필요한 정보도 같이 삭제되는 현상
	-- 3. 변경 이상 → 변경하고자 하는 것은 하나인데 여러번 변경해야 하는 현상




```


이전 정리에 누락되었던 **해시 분할, 범위 분할, 분산 데이터베이스** 등 상세 내용을 포함하여 **5.DDL.pdf**의 모든 내용을 빠짐없이 재구성한 Obsidian 최적화 파일임.

---

# 05_DDL.md

## 1. 관계형 데이터베이스 (RDBMS) 기초

- **정의**: 1970년 Codd에 의해 제안됨. 데이터를 테이블(릴레이션)의 집합으로 표현함.
- **용어 정리**:
    - **속성 값(Attribute Value)**: 각 속성이 가지는 데이터 값으로, 더 이상 분해할 수 없는 **원자 값**만 허용함.
    - **도메인(Domain)**: 하나의 속성이 가질 수 있는 모든 원자 값들의 집합임.
- **무결성 제약 조건**:
    - **개체 무결성**: 기본키(PK)는 NULL일 수 없고 중복될 수 없음.
    - **참조 무결성**: 외래키(FK) 값은 참조하는 테이블에 존재하거나 NULL이어야 함.
    - **도메인 무결성**: 속성 값은 정의된 데이터 타입 및 범위(도메인) 규칙을 지켜야 함.

## 2. 데이터 모델링 및 3계층 스키마

- **추상화(Abstraction)**: 복잡한 내부 구조(엔진 작동 원리 등)를 은폐하고 사용자에게 필요한 추상적인 뷰만 제공하는 것임.
- **3계층 스키마 구조**:
    1. **내부 스키마(Internal)**: 물리적 저장 구조 및 접근 경로 기술.
    2. **개념 스키마(Conceptual)**: 전체 DB 구조(엔티티, 관계, 제약조건) 기술. 고수준 데이터 모델로 표현됨.
    3. **외부 스키마(External)**: 개별 사용자나 개발자가 필요로 하는 DB 부분 기술.
- **데이터 독립성**:
    - **논리적 독립성**: 응용 프로그램을 바꾸지 않고 개념 스키마(데이터 타입 추가 등)를 변경할 수 있는 능력임.
    - **물리적 독립성**: 외부/개념 스키마에 영향을 주지 않고 내부 스키마(인덱스 추가 등)를 변경할 수 있는 능력임.

## 3. 이상 현상(Anomaly) 및 함수적 종속

- **이상 현상**: 데이터 중복으로 인해 발생함.
    - **삽입 이상**: 새 데이터를 넣기 위해 원치 않는 데이터도 강제로 삽입해야 함.
    - **삭제 이상**: 특정 데이터 삭제 시 연쇄적으로 필요한 정보까지 손실됨.
    - **갱신 이상**: 중복 데이터 중 일부만 수정되어 데이터 불일치가 발생함.
- **함수적 종속성**:
    - **완전 함수적 종속**: 기본키의 모든 속성을 알아야 다른 속성을 식별할 수 있는 경우임.
    - **부분 함수적 종속**: 기본키가 복합키일 때, 그중 일부 속성에만 종속되는 경우임.
    - **이행적 함수 종속**: X→Y, Y→Z 관계에서 X→Z가 성립하는 경우임 (예: 회원번호→생년월일→나이).

## 4. 정규화 (Normalization) 단계

1. **제1정규형(1NF)**: 모든 도메인이 원자 값으로 구성됨. 다가 속성을 분리함.
2. **제2정규형(2NF)**: 1NF를 만족하고, **부분 함수적 종속을 제거**함.
3. **제3정규형(3NF)**: 2NF를 만족하고, **이행적 함수 종속을 제거**함.
4. **BCNF**: 모든 결정자가 후보키가 되도록 함.
5. **제4정규형(4NF)**: 다가 종속(MVD) 관계를 제거함.
6. **제5정규형(5NF)**: 조인 종속성을 제거하여 무손실 분해를 달성함.

## 5. 반정규화 및 파티셔닝 (누락 내용 보강)

### 5.1 반정규화 (De-normalization)

- **목적**: 빈번한 조인으로 인한 성능 저하 방지 및 조회 성능 최적화.
- **기법**: 테이블 추가(중복/통계/이력/부분), 테이블 병합(1:1, 1:M, 슈퍼/서브타입), 컬럼/관계 중복 등.

### 5.2 테이블 분할 및 파티셔닝 (Partitioning)

- **분할 방식**:
    - **수직 분할**: 컬럼 단위로 분리하여 디스크 I/O 분산.
    - **수평 분할(Sharding)**: 로우 단위로 쪼개어 접근 효율성 증대.
- **파티셔닝 기준(Partitioning Criteria)**:
    - **범위 분할 (Range)**: 월 단위 요금 정보 등 날짜/숫자 범위를 기준으로 분할함. 관리 및 삭제(DROP PARTITION)가 용이함.
    - **목록 분할 (List)**: 지점 코드, 국가명 등 핵심 코드 값 리스트를 기준으로 분할함.
    - **해시 분할 (Hash)**: 해시 알고리즘에 의해 자동 분할됨. 데이터가 골고루 분산되지만, 삭제 기능 등 세부 제어가 어려움.
    - **합성 분할 (Composite)**: 범위 분할 후 해시 분할을 추가하는 등 여러 기술을 결합함.

## 6. 분산 데이터베이스 (누락 내용 보강)

- **정의**: 물리적으로 분산된 데이터를 하나의 가상 시스템으로 사용함.
- **투명성(Transparency)**:
    - **분할 투명성**: 릴레이션이 분할되어 여러 사이트에 저장됨을 몰라도 됨.
    - **위치 투명성**: 데이터 저장 장소를 명시할 필요 없음.
    - **중복 투명성**: 여러 곳에 중복 저장되어 있는지 알 필요 없음.
    - **지역 사상/장애/병행 투명성** 등 보장.
- **적용 기법**:
    - **테이블 복제(Replication)**: 부분 복제(지사별 데이터)와 광역 복제(전체 데이터 동일 공유)로 나뉨.
    - **테이블 요약(Summarization)**: 분석 요약(동일 구조 통합), 통합 요약(다른 내용 통합).

## 7. 실무 DDL 명령어 및 제약조건

### 7.1 CHECK 및 AUTO_INCREMENT

- **CHECK**: 값의 범위를 제한함.

```
CREATE TABLE tCheckTest(
    gender CHAR(3) NULL CHECK(gender = '남' OR gender = '여'),
    grade INT NULL CHECK (grade >= 1 AND grade <= 3),
    name CHAR(10) NULL CHECK(name LIKE '김%')
);
```

- **AUTO_INCREMENT**: 자동 증가 번호.

```
CREATE TABLE tSale (
    saleno INT AUTO_INCREMENT PRIMARY KEY,
    customer NCHAR(10)
);
-- 시작 값 변경
ALTER TABLE tSale AUTO_INCREMENT = 100;
```

### 7.2 참조 무결성 옵션

- **ON DELETE CASCADE**: 부모 삭제 시 자식도 자동 삭제됨.
- **ON UPDATE CASCADE**: 부모 변경 시 자식도 자동 변경됨.

### 7.3 테이블 압축 및 주석

- **압축 생성**: `CREATE TABLE ... ROW_FORMAT=COMPRESSED;` (용량 절감, 시간 증가).
- **주석**: `COMMENT ON TABLE 테이블명 IS '주석내용';`.

![[autoever_0713.spf]]