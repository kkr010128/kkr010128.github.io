---
title: 프로시저와 트리거
description: MariaDB Stored Procedure, Trigger, 프로그래밍 기능 정리
date: 2026-07-15
series: MariaDB
tags:
  - MariaDB
  - AutoEver SW School
---

1. 스토어드 프로시저 (Stored Procedure)

- **정의**: 관계형 데이터베이스에서 절차적 프로그래밍(변수, 조건문, 반복문 등)을 가능하게 하는 객체임.
- **사용 목적**: 성능 향상, 유지 및 관리의 간소화, 모듈화 프로그래밍, 보안 강화 등이 있음.

### 1.1 기본 문법 및 호출

- **구조**: MariaDB의 기본 종료 문자인 세미콜론(`;`)과의 충돌을 피하기 위해 `DELIMITER`를 사용하여 일시적으로 종료 문자를 변경함. 

```sql
-- 선언
DELIMITER $$
CREATE PROCEDURE 프로시저이름()
BEGIN
    -- SQL 및 로직 작성
END $$
DELIMITER ;

-- 호출
CALL 프로시저이름();
```

---

## 2. 제어 흐름 문법

### 2.1 IF ~ ELSE (조건문)

- 조건에 따라 로직을 분기하며, 처리할 문장이 여러 개일 경우 `BEGIN ~ END`로 묶음.
- **예제**: 특정 사원의 입사일로부터 5년 경과 여부 확인.

```sql
DELIMITER //
CREATE PROCEDURE ifProc()
BEGIN
    DECLARE hireDATE DATE; -- 입사일 저장 변수
    DECLARE days INT;      -- 근무 일수

    SELECT HIREDATE INTO hireDate FROM EMP WHERE EMPNO = 7369;
    SET days = DATEDIFF(CURRENT_DATE(), hireDATE);

    IF (days/365) >= 5 THEN
        SELECT '입사한지 5년이 지났습니다.' AS 결과;
    ELSE
        SELECT '입사한지 아직 5년이 되지 않았습니다.' AS 결과;
    END IF;
END //
DELIMITER ;

-- 실행 결과
CALL ifProc(); -- '입사한지 5년이 지났습니다.' (데이터에 따라 다름)
```

### 2.2 CASE ~ WHEN (다중 분기)

- 여러 조건 중 일치하는 하나를 수행함.
- **예제**: 점수에 따른 학점 계산.

```sql
DELIMITER //
CREATE PROCEDURE caseProc()
BEGIN
    DECLARE point INT DEFAULT 77;
    DECLARE credit CHAR(1);

    CASE
        WHEN point >= 90 THEN SET credit = 'A';
        WHEN point >= 80 THEN SET credit = 'B';
        WHEN point >= 70 THEN SET credit = 'C';
        ELSE SET credit = 'F';
    END CASE;
    SELECT CONCAT('점수: ', point, ', 학점: ', credit) AS 성적;
END //
DELIMITER ;

-- 실행 결과
CALL caseProc(); -- '점수: 77, 학점: C'
```

### 2.3 WHILE (반복문)

- 조건이 참인 동안 명령문을 반복 수행함.
- **ITERATE**: 지정한 레이블로 이동(자바의 `continue`와 유사).
- **LEAVE**: 반복문을 즉시 종료(자바의 `break`와 유사).
- **예제**: 1~100까지 합을 구하다가 7의 배수는 건너뛰고 합계가 1000을 넘으면 중단.

```sql
DELIMITER //
CREATE PROCEDURE whileProc()
BEGIN
    DECLARE i INT DEFAULT 1;
    DECLARE hap INT DEFAULT 0;

    myWhile: WHILE (i <= 100) DO
        IF (i % 7 = 0) THEN
            SET i = i + 1;
            ITERATE myWhile; -- 7의 배수는 더하지 않고 다시 위로
        END IF;
        SET hap = hap + i;
        IF (hap > 1000) THEN
            LEAVE myWhile; -- 합계가 1000 초과 시 반복 종료
        END IF;
        SET i = i + 1;
    END WHILE;
    SELECT hap;
END //
DELIMITER ;

-- 실행 결과
CALL whileProc(); -- 1029 (조건에 따른 합계 결과)
```

---

## 3. 오류 처리 (Error Handling)

- 프로시저 실행 중 발생하는 에러에 대해 `DECLARE HANDLER`를 사용하여 대응함.
- **액션**: `CONTINUE`(계속 수행) 또는 `EXIT`(종료) 중 선택함.
- **예제**: 존재하지 않는 테이블 조회 시 커스텀 메시지 출력.

```sql
DECLARE CONTINUE HANDLER FOR 1146
    SELECT '테이블이 존재하지 않습니다.' AS '오류 메시지';
```

---

## 4. 동적 SQL (Dynamic SQL)

- SQL문을 미리 준비(`PREPARE`)해 두었다가 필요할 때 실행(`EXECUTE`)하고 해제(`DEALLOCATE`)함.
- **예제**: 매개변수를 받는 동적 쿼리.

```sql
PREPARE paramQuery FROM 'SELECT * FROM EMP WHERE empno = ?';
SET @empno = 7788;
EXECUTE paramQuery USING @empno; -- 사원번호 7788 데이터 조회됨
DEALLOCATE PREPARE paramQuery;
```

---

## 5. 트리거 (TRIGGER)

- 테이블에 `INSERT`, `UPDATE`, `DELETE` 사건이 발생할 때 자동으로 실행되는 프로그래밍 블록임.
- **제한**: 트랜잭션 제어 문장(`COMMIT`, `ROLLBACK`)을 직접 사용할 수 없음.

### 5.1 트리거의 OLD와 NEW

- **INSERT**: `NEW`만 존재 (새로 삽입된 값).
- **UPDATE**: `OLD`(수정 전)와 `NEW`(수정 후) 모두 존재.
- **DELETE**: `OLD`만 존재 (삭제된 원래 값).

### 5.2 실무 활용 예제

- **급여 수정 제한**: 현재 값보다 적게 수정하거나 10% 이상 높게 수정하는 것을 차단함.

```sql
DELIMITER //
CREATE TRIGGER emp_sal_chk
BEFORE UPDATE ON EMP
FOR EACH ROW
BEGIN
    -- 수정 전 급여보다 낮거나, 1.1배를 초과할 경우 에러 발생시킴
    IF (NEW.sal < OLD.sal OR NEW.sal > OLD.sal * 1.1) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '급여 수정 범위가 잘못되었습니다.';
    END IF;
END //
DELIMITER ;

-- 실행 결과
UPDATE EMP SET SAL = SAL * 1.2; -- '급여 수정 범위가 잘못되었습니다.' 에러 출력됨
```

---

> [!tip] **보강 내용**
> 
> - **SIGNAL SQLSTATE**: 트리거 내부에서 의도적으로 사용자 정의 오류를 발생시켜 DML 작업을 중단시킬 때 사용함.
> - **IN/OUT 파라미터**: 프로시저 생성 시 `(IN 변수명 타입)`으로 입력값을 받거나 `(OUT 변수명 타입)`으로 결과값을 외부로 내보낼 수 있음.