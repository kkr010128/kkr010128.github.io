---
title: Jenkins 단위 테스트와 JaCoCo Code Coverage
description: Spring Boot 단위·Web 계층 Test를 구성하고 Jenkins Pipeline에서 JUnit 결과와 JaCoCo Coverage 기준을 검증한다
date: 2026-09-16
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Jenkins
---

[Jenkins Pipeline과 Jenkinsfile 기반 배포](/cloud-native-51-jenkins-pipeline-jenkinsfile/)에서는 Checkout부터 Build와 배포까지의 실행 흐름을 Code로 정의했다. 이 글에서는 배포 전에 Application 동작을 검증하는 단위 Test와 Web 계층 Test를 작성하고, Jenkins에서 Test 결과와 JaCoCo Code Coverage를 확인한다.

## 1 ) 단위 Test의 목적

---

> **단위 Test(Unit Test)**는 Method나 Class처럼 독립적으로 검증할 수 있는 작은 단위가 의도한 결과를 반환하는지 확인하는 Test이다.

단위 Test는 변경으로 발생한 문제를 빠르게 찾고, Refactoring 이후 기존 동작이 유지되는지 반복해서 검증한다. 각 Test Case는 실행 순서나 다른 Test의 상태에 의존하지 않아야 한다. Database, 외부 API처럼 독립시키기 어려운 협력 객체는 Mock Object로 대체할 수 있다.

- **문제 위치 확인**: 작은 단위마다 실패 여부를 확인하므로 결함이 발생한 범위를 좁히기 쉽다.

- **회귀 방지**: 기존 Test를 다시 실행해 수정한 Code가 이전 기능을 깨뜨리지 않았는지 확인한다.

- **통합 위험 감소**: 단위별 불확실성을 줄인 뒤 Component를 연결하므로 통합 Test의 원인을 구분하기 쉽다.

- **변경 비용 감소**: 자동화된 검증 결과를 바탕으로 Refactoring과 기능 변경을 반복할 수 있다.

Test Code가 존재한다는 사실만으로 정확성이 보장되지는 않는다. 경계값, 예외 조건과 실제 요구 사항을 검증하는 Assertion이 있어야 한다.

## 2 ) Spring Boot Test 범위 구분

---

Spring Boot Application에서는 검증할 범위에 따라 Test Context를 다르게 구성한다.

| 범위 | 대표 구성 | 검증 대상 | 외부 의존성 처리 |
|---|---|---|---|
| 순수 단위 Test | JUnit으로 객체 직접 생성 | Method의 입력과 반환값 | 필요하면 Mock 사용 |
| Web 계층 Test | `MockMvc`, `@WebMvcTest` 또는 `@SpringBootTest` | HTTP Method, URL, Status와 Body | Service를 Mock하거나 Test Context 사용 |
| Repository 계층 Test | `@DataJpaTest` | Entity Mapping과 Query | H2 같은 Test Database 또는 Test Container 사용 |

한 Test가 많은 계층을 동시에 기동할수록 실제 구성에 가까워지지만 실행 시간이 늘고 실패 원인도 넓어진다. 계산처럼 외부 의존성이 없는 Logic은 순수 단위 Test로, HTTP Mapping은 Web 계층 Test로 분리한다.

Repository Test가 필요한 Project는 Spring Data JPA와 운영 Database Driver 외에 H2를 Test Runtime Dependency로 둘 수 있다. `@DataJpaTest`는 JPA Component에 필요한 범위만 기동하고 Test가 끝날 때 Transaction을 Rollback한다. H2를 사용하면 외부 Database 없이 빠르게 Mapping과 Query를 확인할 수 있지만, 운영 Database와 SQL Dialect·Constraint 동작이 다를 수 있으므로 실제 Database를 사용한 통합 Test를 별도로 구성한다.

## 3 ) Calculator Service와 Controller

---

`Calculator`는 두 정수의 합을 반환한다.

```java
import org.springframework.stereotype.Service;

@Service
public class Calculator {
    public int sum(int a, int b) {
        return a + b;
    }
}
```

`CalculatorController`는 Root와 상태 확인 Endpoint를 제공한다. HTTP Method를 명확히 하기 위해 `@GetMapping`을 사용한다.

```java
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class CalculatorController {
    private final Calculator calculator;

    public CalculatorController(Calculator calculator) {
        this.calculator = calculator;
    }

    @GetMapping("/")
    public String index() {
        return "OK";
    }

    @GetMapping("/health")
    public String health() {
        return "OK";
    }
}
```

생성자 주입을 사용하면 운영 Code와 Test Code에서 필요한 의존성을 명시적으로 전달할 수 있다.

## 4 ) Calculator 단위 Test

---

외부 의존성이 없는 `Calculator`는 Spring Context를 기동하지 않고 직접 생성한다.

```java
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class CalculatorTest {
    private final Calculator calculator = new Calculator();

    @Test
    void sumReturnsAdditionResult() {
        assertEquals(5, calculator.sum(2, 3));
    }
}
```

`assertEquals(expected, actual)`은 기대값 `5`와 실제 반환값을 비교한다. Test 이름은 검증하는 동작과 기대 결과가 드러나도록 작성한다.

## 5 ) MockMvc로 Health Endpoint 검증

---

`MockMvc`는 실제 Network Port를 열지 않고 Spring MVC 요청과 응답을 검증한다. 다음 Test는 Application Context를 기동한 뒤 `GET /health`의 Status와 Body를 확인한다.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultHandlers.print;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.MOCK)
@AutoConfigureMockMvc
class ControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @Test
    void healthReturnsOk() throws Exception {
        mockMvc.perform(get("/health"))
                .andExpect(status().isOk())
                .andExpect(content().string("OK"))
                .andDo(print());
    }
}
```

| 검증 | 의미 |
|---|---|
| `get("/health")` | Controller의 `@GetMapping("/health")`와 같은 HTTP Method와 경로로 요청 |
| `status().isOk()` | HTTP Status가 `200 OK`인지 확인 |
| `content().string("OK")` | 응답 Body가 `OK`인지 확인 |
| `andDo(print())` | 요청과 응답을 Test Log에 출력 |

위 Import 경로는 Spring Boot 3.x 기준이다. Spring Boot 4에서는 `AutoConfigureMockMvc`가 `org.springframework.boot.webmvc.test.autoconfigure` Package로 이동했다. Project의 Spring Boot Version에 맞는 [API 문서](https://docs.spring.io/spring-boot/4.0/api/java/org/springframework/boot/webmvc/test/autoconfigure/package-summary.html)를 확인해야 한다.

## 6 ) Gradle Test 실행과 결과 확인

---

Project Root에서 Gradle Wrapper로 Test를 실행한다.

```bash
./gradlew test
```

`test` Task는 필요한 Main·Test Source Compile을 Task Graph에 포함하므로 `compileJava`를 먼저 실행할 필요가 없다. 실패한 Test가 있으면 Gradle Process가 0이 아닌 종료 Code를 반환하고 Jenkins Stage도 실패한다.

주요 결과는 다음 위치에 생성된다.

| 결과 | 기본 경로 |
|---|---|
| HTML Test Report | `build/reports/tests/test/index.html` |
| JUnit XML | `build/test-results/test/*.xml` |

`gradlew`의 실행 권한은 Repository에 한 번 반영한다.

```bash
chmod +x gradlew
git add gradlew
git commit -m "chore: make Gradle wrapper executable"
```

Pipeline을 실행할 때마다 `chmod`로 작업 환경을 변경하는 것보다 실행 권한을 Version 관리하는 편이 재현 가능하다.

## 7 ) Jenkins Pipeline에서 Test 실행

---

다음 Pipeline은 Source를 Checkout하고 Test를 실행한 뒤 Jenkins에 JUnit 결과를 게시한다.

```groovy
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Unit Test') {
            steps {
                sh './gradlew clean test'
            }
        }
    }

    post {
        always {
            junit testResults: 'build/test-results/test/*.xml',
                  allowEmptyResults: false
        }
    }
}
```

`post { always { ... } }`에 Report 게시를 두면 Test Stage가 실패해도 생성된 XML을 Jenkins가 읽는다. Jenkins Build 화면에서는 전체 Test 수, 실패한 Test와 이전 Build 대비 추이를 확인할 수 있다.

## 8 ) Code Coverage의 의미

---

> **Code Coverage**는 Test를 실행했을 때 Program의 Code 요소가 실제로 실행된 비율을 나타내는 지표이다.

Coverage는 Test가 닿지 않은 Code를 찾는 데 사용한다. Coverage가 높아도 Assertion이 부정확하거나 요구 사항이 누락되면 결함은 남을 수 있다.

| 지표 | 확인 내용 |
|---|---|
| Line Coverage | 실행된 Source Line의 비율 |
| Branch Coverage | 조건문과 분기에서 실행된 경로의 비율 |
| Method Coverage | 한 번 이상 실행된 Method의 비율 |
| Class Coverage | 한 번 이상 실행된 Class의 비율 |
| Instruction Coverage | Java Bytecode Instruction 중 실행된 비율 |
| Complexity | 분기 구조를 바탕으로 계산한 순환 복잡도와 누락된 Test Case의 규모 |

Branch Coverage가 높으려면 `if`의 참과 거짓처럼 가능한 분기 결과를 각각 실행해야 한다. Line Coverage가 100%여도 한 줄에 포함된 모든 조건 조합을 검증했다고 단정할 수 없다.

## 9 ) JaCoCo Report와 Coverage 기준 구성

---

`build.gradle`의 `plugins` Block에 JaCoCo Plugin을 추가한다.

```groovy
plugins {
    id 'java'
    id 'jacoco'
}
```

Report 생성과 Coverage 기준 검증을 다음처럼 연결한다.

```groovy
test {
    finalizedBy jacocoTestReport
}

jacocoTestReport {
    dependsOn test

    reports {
        html.required = true
        xml.required = true
        csv.required = false
    }
}

jacocoTestCoverageVerification {
    dependsOn test

    violationRules {
        rule {
            limit {
                minimum = 0.20
            }
        }
    }
}

check.dependsOn jacocoTestCoverageVerification
```

| 설정 | 역할 |
|---|---|
| `test.finalizedBy` | Test 종료 후 HTML·XML Report 생성 |
| `jacocoTestReport.dependsOn test` | Report를 직접 실행해도 먼저 Test 수행 |
| `minimum = 0.20` | 선택한 Counter의 최소 Coverage를 20%로 설정한 학습용 예시 |
| `check.dependsOn` | `check` Lifecycle에 Coverage 기준 검증 포함 |

Gradle의 JaCoCo Plugin은 기본적으로 `jacocoTestReport`와 `test`를 자동 연결하지 않으며, Coverage Verification도 `check`에 자동 포함하지 않는다. 필요한 Task 관계를 명시해야 한다. 자세한 설정은 [Gradle JaCoCo Plugin 문서](https://docs.gradle.org/current/userguide/jacoco_plugin.html)에서 확인할 수 있다.

다음 명령은 Test, Report 생성과 기준 검증을 한 번에 수행한다.

```bash
./gradlew clean test jacocoTestReport jacocoTestCoverageVerification
```

HTML Report는 `build/reports/jacoco/test/html/index.html`에서 확인한다. Coverage가 설정한 최소값보다 낮으면 `jacocoTestCoverageVerification`이 실패하고 Jenkins Pipeline도 중단된다.

## 10 ) Coverage 목표 설정

---

Coverage 100%는 요구 사항을 모두 구현했거나 결함이 없다는 뜻이 아니다. 잘못된 구현을 그대로 기대값으로 사용하거나 중요한 예외 Case를 누락해도 실행 비율은 높게 나올 수 있다.

[Google Testing Blog의 Coverage 지침](https://testing.googleblog.com/2020/08/code-coverage-best-practices.html)은 60%를 수용 가능한 수준, 75%를 권장할 만한 수준, 90%를 모범적인 수준으로 제시하지만 보편적인 합격 기준은 아니다. Code의 Business 영향, 변경 빈도, 복잡도와 유지 기간에 따라 Team이 기준을 정해야 한다.

Coverage를 운영할 때는 다음 순서로 접근한다.

1. 핵심 Method가 Test에서 한 번 이상 실행되는지 확인한다.

2. 변경된 Code와 장애 영향이 큰 Code의 Line Coverage를 우선 높인다.

3. 조건문과 예외 처리의 Branch Coverage를 확인한다.

4. 수치만 높이는 Test 대신 요구 사항과 실패 조건을 검증하는 Assertion을 추가한다.

> **최종 정리**
> - 순수 Logic은 Spring Context 없이 빠른 단위 Test로 검증한다.
>
> - Controller Test는 실제 Mapping과 같은 HTTP Method, URL, Status와 Body를 검증한다.
>
> - Gradle `test` Task가 Compile을 포함하므로 Pipeline에 중복 Compile Stage를 둘 필요가 없다.
>
> - JaCoCo Task 관계와 합격 기준은 Project에서 명시적으로 구성한다.
>
> - Coverage는 미검증 영역을 찾는 지표이며 Software 정확성 자체를 증명하지 않는다.

다음 글인 [Jenkins SonarQube 정적 분석과 Quality Gate](/cloud-native-53-jenkins-sonarqube-analysis/)에서는 Test를 실행하지 않고 Code의 Bug, Vulnerability와 Code Smell을 분석하고 Jenkins Pipeline에 결과를 연결한다.
