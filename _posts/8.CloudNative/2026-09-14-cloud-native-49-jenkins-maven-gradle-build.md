---
title: Jenkins Maven·Gradle Build와 Email 알림
description: Spring Boot Project를 Maven과 Gradle로 Build하고 Jenkins Freestyle Job에서 Test, Package, Poll SCM과 Email 알림을 구성한다
date: 2026-09-14
updated_at: 2026-09-15
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Jenkins
---

[Jenkins Freestyle Job과 Credentials](/cloud-native-48-jenkins-freestyle-credentials/)에서 Job의 SCM, Trigger, Build Step과 Credential을 정리했다. 이번에는 Java Project의 Dependency, Compile, Test와 Package 과정을 Maven과 Gradle에 맡기고 Jenkins가 같은 명령을 반복 실행하도록 구성한다.

## 1 ) Java Build Tool이 담당하는 과정

---

Java Application을 배포 가능한 결과물로 만들려면 다음 작업이 필요하다.

1. 외부 Artifact Repository에서 Third-party Library와 Plugin을 내려받는다.

2. Dependency를 Compile과 Test Classpath에 연결한다.

3. Application Source와 Test Source를 Compile한다.

4. Unit Test를 실행하고 Report를 만든다.

5. 실행 가능한 JAR 또는 WAR로 Package한다.

6. 필요한 경우 Artifact Repository에 결과물을 배포한다.

Ant, Maven과 Gradle은 이 과정을 자동화하는 Java Build Tool이다. Jenkins는 Build Tool을 대체하지 않는다. Jenkins가 Build를 시작하고 환경과 결과를 관리하며, 실제 Compile과 Test는 Project에 정의된 Maven Goal이나 Gradle Task가 수행한다.

| 도구 | 핵심 설정 | 실행 단위 | 특징 |
|---|---|---|---|
| Ant | `build.xml` | Target | 실행 절차를 명시적으로 구성 |
| Maven | `pom.xml` | Lifecycle Phase와 Goal | Convention과 표준 Directory 중심 |
| Gradle | `build.gradle` 또는 `build.gradle.kts` | Task | Task Graph와 DSL 기반 구성 |

## 2 ) Maven Lifecycle과 결과 Directory

---

Maven은 Lifecycle의 Phase를 순서대로 실행한다. 뒤 Phase를 요청하면 앞 Phase도 함께 실행된다.

| Phase | 주요 동작 | 대표 결과 |
|---|---|---|
| `clean` | 이전 Build 결과 제거 | `target` 정리 |
| `compile` | `src/main/java` Source Compile | `target/classes` |
| `test-compile` | `src/test/java` Test Source Compile | `target/test-classes` |
| `test` | Surefire Plugin으로 JUnit·TestNG Test 실행 | `target/surefire-reports` |
| `package` | Packaging 설정에 따라 JAR 또는 WAR 생성 | `target/*.jar`, `target/*.war` |
| `install` | Local Maven Repository에 Artifact 설치 | `~/.m2/repository` |
| `deploy` | Remote Artifact Repository에 배포 | 원격 Repository Artifact |

`mvn clean package`는 이전 결과를 지운 뒤 `package`까지 필요한 Compile과 Test Phase를 순서대로 실행한다. 따라서 `mvn clean compile package`처럼 `compile`을 별도로 넣을 필요가 없다.

Maven은 [Maven Central](https://central.sonatype.com/) 같은 Repository에서 Project Dependency뿐 아니라 Build Plugin의 Dependency도 해결한다. Network가 제한된 Jenkins Agent에서는 Proxy, 사내 Mirror와 Local Cache 정책을 별도로 설정해야 한다.

## 3 ) Maven Spring Calculator Project

---

Spring Initializr에서 Maven Project를 만들고 Spring Web과 Spring Boot DevTools Dependency를 선택한다. WAR가 필요하면 Packaging을 `war`로 설정하고, 단독 실행 JAR가 목적이면 기본 `jar`를 사용한다.

`src/main/java/<package>/Calculator.java`를 작성한다.

```java
import org.springframework.stereotype.Service;

@Service
public class Calculator {
    public int addition(int num1, int num2) {
        return num1 + num2;
    }

    public int subtraction(int num1, int num2) {
        return num1 - num2;
    }

    public int multiplication(int num1, int num2) {
        return num1 * num2;
    }
}
```

`src/main/java/<package>/CalculatorController.java`는 HTTP 요청을 Service에 전달한다.

```java
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class CalculatorController {
    private final Calculator calculator;

    public CalculatorController(Calculator calculator) {
        this.calculator = calculator;
    }

    @RequestMapping("/")
    public String index() {
        return "health check";
    }

    @RequestMapping("/add")
    public String add(@RequestParam("num1") int num1,
                      @RequestParam("num2") int num2) {
        return String.valueOf(calculator.addition(num1, num2));
    }

    @RequestMapping("/sub")
    public String sub(@RequestParam("num1") int num1,
                      @RequestParam("num2") int num2) {
        return String.valueOf(calculator.subtraction(num1, num2));
    }

    @RequestMapping("/mul")
    public String mul(@RequestParam("num1") int num1,
                      @RequestParam("num2") int num2) {
        return String.valueOf(calculator.multiplication(num1, num2));
    }
}
```

TestNG를 사용하려면 `pom.xml`의 `dependencies`에 Test Scope Dependency를 추가한다.

```xml
<dependency>
    <groupId>org.testng</groupId>
    <artifactId>testng</artifactId>
    <version>7.11.0</version>
    <scope>test</scope>
</dependency>
```

Test Source는 Maven 표준 경로인 `src/test/java/<package>/TestAdditionFunctionality.java`에 둔다.

```java
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;

public class TestAdditionFunctionality {
    private Calculator calculator;
    private int result;

    @BeforeClass
    public void init() {
        calculator = new Calculator();
    }

    @BeforeMethod
    public void resetResult() {
        result = 0;
    }

    @Test(priority = 1)
    public void testAdditionWithPositiveNumbers() {
        result = calculator.addition(10, 20);
        Assert.assertEquals(result, 30, "positive number");
    }

    @AfterClass
    public void tearDown() {
        calculator = null;
    }
}
```

`@BeforeClass`는 Class의 Test 전에 한 번 실행하고, `@BeforeMethod`는 각 Test Method 전에 실행한다. `@AfterClass`는 Class의 Test가 끝난 뒤 정리한다. Group 단위 준비가 필요한 Test에는 `@BeforeGroups`를 추가할 수 있지만 Group을 사용하지 않는 예제에는 불필요하다.

`src/main/resources/application.properties`에서 실행 Port를 지정한다.

```properties
server.port=80
```

Port `80`은 Linux에서 일반 사용자 Process가 바로 Binding하지 못할 수 있고 기존 Web Server와 충돌할 수도 있다. Local 검증에서는 기본 `8080` 또는 사용하지 않는 일반 Port를 선택해도 된다.

Local에서 먼저 Test와 Package를 확인한다.

```bash
./mvnw clean package
find target -maxdepth 2 -type f
```

Maven Wrapper가 없다면 설치된 Maven으로 `mvn clean package`를 실행한다. Test 실패 시 명령이 0이 아닌 종료 Code를 반환하고 Package 단계도 실패한다.

검증된 Project를 Remote Repository에 Push한다.

```bash
git add .
git commit -m "Add Maven calculator project"
git push
```

## 4 ) Jenkins Maven Build 구성

---

Maven Project 유형을 사용하려면 Maven Integration Plugin을 설치한다. Freestyle Job에서 Shell로 Maven Wrapper를 실행하는 방식이라면 Maven Project 유형 없이도 구성할 수 있다.

### Jenkins Tool로 Maven 사용

1. **Manage Jenkins → Plugins**에서 Git과 Maven Integration Plugin을 확인한다.

2. **Manage Jenkins → Tools**에서 JDK와 Maven Installation을 추가한다.

3. 새 Maven Job을 만들고 **Source Code Management → Git**에 Repository URL과 Branch를 입력한다.

4. Private Repository라면 읽기 권한을 가진 Credential을 선택한다.

5. Maven Goal에 다음 값을 입력한다.

```text
clean package
```

6. 저장 후 **Build Now**를 실행한다.

`mvn: command not found` 또는 Maven Installation을 찾을 수 없다는 오류가 발생하면 **Manage Jenkins → Tools**에서 Maven 이름과 자동 설치 설정을 확인한다. Job이 참조한 Tool 이름과 설정 이름도 일치해야 한다.

### Maven Wrapper 사용

Project에 `mvnw`와 `.mvn/wrapper`가 Commit되어 있다면 Freestyle Job의 **Execute shell**에서 다음과 같이 실행할 수 있다.

```bash
chmod +x ./mvnw
./mvnw clean package
```

Wrapper를 사용하면 Project가 요구하는 Maven Version을 Source와 함께 관리할 수 있다. 다만 JDK는 Agent에 별도로 준비해야 하고 Wrapper가 처음 Maven Distribution을 받을 수 있도록 Network 접근이 필요하다.

Build가 끝나면 다음을 확인한다.

- Console Output에서 Dependency Download, Compile과 Test 결과

- Workspace의 `target/classes`와 `target/test-classes`

- `target/surefire-reports`의 Test Report

- `target`에 생성된 JAR 또는 WAR

Jenkins Container에서 직접 확인해야 한다면 다음 명령을 사용한다.

```bash
docker exec -it jenkins bash
cd /var/jenkins_home/workspace/<job-name>
find target -maxdepth 2 -type f
```

단순히 File이 존재하는지만 확인하지 않고 해당 Build Number와 연결해 Artifact를 보관한다. Freestyle Job의 **Post-build Actions → Archive the artifacts**에 다음 Pattern을 지정할 수 있다.

```text
target/*.jar, target/*.war
```

## 5 ) Poll SCM으로 변경 감지

---

Jenkins가 외부 Webhook을 받을 수 없는 환경에서는 **Build Triggers → Poll SCM**을 사용해 Repository 변경을 확인한다.

```text
H/5 * * * *
```

`H/5`는 Jenkins가 Job별 시작 시점을 분산하면서 약 5분 간격으로 확인하도록 한다. Polling할 때마다 Build하는 것이 아니라 SCM Revision이 바뀐 경우에 Build를 시작한다. 설정 후 Commit을 Push하고 다음을 확인한다.

1. Polling Log에서 변경 Commit을 감지했는가

2. 새 Build Number가 생성됐는가

3. Console Output에 새 Commit ID가 표시되는가

4. Test와 Package가 성공했는가

## 6 ) Email 알림

---

Jenkins는 Build 결과를 Email로 알릴 수 있다. Gmail이나 Naver 같은 외부 SMTP Server를 사용할 때는 일반 계정 Password 대신 서비스가 제공하는 App Password를 사용한다.

**Manage Jenkins → System**의 Email Notification 또는 Extended E-mail Notification 영역에 SMTP Host, Port, TLS와 발신 계정을 설정한다. 항목 이름은 설치한 Plugin과 Jenkins Version에 따라 달라질 수 있다.

| 항목 | 역할 |
|---|---|
| SMTP Server | Email을 전달할 Server 주소 |
| SMTP Port | TLS 방식에 맞는 연결 Port |
| Authentication | 발신 계정과 App Password |
| Use SSL/TLS | SMTP Server가 요구하는 암호화 방식 |
| Reply-To Address | 수신자가 회신할 주소 |

가능하면 SMTP 인증 값을 Jenkins Credential로 관리하고 접근 권한을 제한한다. App Password를 Job Script, Repository나 문서에 직접 적지 않는다.

Freestyle Job의 **Post-build Actions**에서 Email Notification을 추가하고 수신 주소를 입력한다. Test Email을 보내 Server 설정을 먼저 확인한 뒤 성공, 실패 또는 불안정 상태 중 어떤 경우에 알릴지 정한다. Email 전송 실패와 Application Build 실패는 원인이 다르므로 Console Log의 Build Step과 Post-build Action을 구분해서 확인한다.

## 7 ) Gradle Spring Calculator Project

---

Spring Initializr에서 Gradle Project를 만들고 Spring Boot DevTools, Lombok과 Spring Web Dependency를 선택한다.

`src/main/java/<package>/Calculator.java`를 작성한다.

```java
import org.springframework.stereotype.Service;

@Service
public class Calculator {
    public int sum(int a, int b) {
        return a + b;
    }
}
```

`src/main/java/<package>/CalculatorController.java`를 작성한다.

```java
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
public class CalculatorController {
    private final Calculator calculator;

    @RequestMapping("/")
    public String health() {
        return "healthy";
    }

    @RequestMapping("/sum")
    public String sum(@RequestParam("a") Integer a,
                      @RequestParam("b") Integer b) {
        return String.valueOf(calculator.sum(a, b));
    }
}
```

`src/main/resources/application.properties`에 Port를 지정한다.

```properties
server.port=9000
```

Gradle Wrapper를 사용해 목적별 Task를 실행한다.

| 명령 | 역할 |
|---|---|
| `./gradlew compileJava` | Main Java Source Compile |
| `./gradlew build` | Compile, Test와 Package를 포함한 Build |
| `./gradlew jar` | Java Plugin의 일반 JAR 생성 |
| `./gradlew bootRun` | Spring Boot Application 실행 |

Application을 실행해 Endpoint를 확인한다.

```bash
./gradlew bootRun
curl "http://localhost:9000/sum?a=10&b=20"
```

예상 응답은 `30`이다. 검증 후 Project File과 Gradle Wrapper를 GitHub에 Push한다.

## 8 ) Jenkins Gradle Build 구성

---

Freestyle Job을 만들고 Git Repository와 Branch를 연결한다. Linux Agent에서 Windows가 생성한 Repository를 Checkout하면 `gradlew`의 실행 권한이 Git에 기록되지 않았을 수 있다. **Execute shell**에서 권한을 확인한 뒤 Build한다.

```bash
chmod +x ./gradlew
./gradlew clean build
```

`build` Task가 `compileJava`를 포함하므로 두 명령을 연속으로 실행할 필요가 없다. `clean`은 이전 `build` Directory를 지워 남은 결과가 새 Build에 섞이지 않게 한다.

반복해서 `chmod`하지 않으려면 개발 환경에서 실행 Bit를 Git Index에 기록해 Commit한다.

```bash
git update-index --chmod=+x gradlew
git commit -m "Make Gradle wrapper executable"
git push
```

Build 후 다음을 확인한다.

- Console Output의 JDK와 Gradle Version

- Test 실행 결과와 실패한 Test 이름

- `build/classes`의 Compile 결과

- `build/reports/tests`의 Test Report

- `build/libs`의 JAR

JAR를 Jenkins Build에 보관하려면 **Archive the artifacts** Pattern을 지정한다.

```text
build/libs/*.jar
```

## 9 ) Gradle Java Toolchain 오류 해결

---

Gradle Build가 다음과 같이 요구하는 Java Version을 찾지 못해 실패할 수 있다.

```text
Cannot find a Java installation matching this task's requirements
```

Gradle Java Toolchain은 Compile과 Test에 사용할 JDK Version을 Project 설정으로 고정하는 기능이다. Jenkins Agent에 해당 JDK가 이미 설치되어 있다면 Gradle이 설치 경로를 감지하도록 Agent 환경을 먼저 확인한다.

```bash
java --version
./gradlew --version
```

Application의 `build.gradle`에 다음과 같은 Toolchain 설정이 있다면 `languageVersion`과 Agent의 JDK Version이 일치하는지 확인한다.

```groovy
java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(21)
    }
}
```

JDK 자동 Provisioning이 필요한 환경에서는 `settings.gradle`에 Foojay Toolchain Resolver Plugin을 구성할 수 있다.

```groovy
plugins {
    id 'org.gradle.toolchains.foojay-resolver-convention' version '0.10.0'
}
```

이 Plugin은 Project가 요구하는 JDK를 Gradle이 찾거나 내려받을 수 있도록 Toolchain Repository를 연결한다. 위 `0.10.0`은 해당 Project에 적용한 Version이다. 작성 시점의 [Gradle Plugin Portal](https://plugins.gradle.org/plugin/org.gradle.toolchains.foojay-resolver-convention)에는 `1.0.0`이 최신 Version으로 표시되며 Plugin 실행에 Java 17 이상이 필요하다. Version을 무조건 바꾸지 않고 Project의 Gradle·JDK 조건을 확인한 뒤 고정한다. Network가 제한된 Jenkins Agent에서는 자동 Download 대신 관리자가 설치한 JDK 경로와 사내 Repository를 사용한다.

오류에 Gradle Version 조건이 함께 표시되면 Wrapper Version도 확인한다.

```bash
./gradlew --version
grep distributionUrl gradle/wrapper/gradle-wrapper.properties
```

현재 Wrapper가 실행 가능한 상태라면 다음 명령으로 Project가 요구하는 Version으로 갱신한다.

```bash
./gradlew wrapper --gradle-version 8.14
git add gradle/wrapper gradlew gradlew.bat
git commit -m "Update Gradle wrapper"
```

Wrapper 자체가 시작되지 않는다면 `gradle-wrapper.properties`의 `distributionUrl`을 임의로 바꾸기 전에 별도로 설치된 Gradle로 Wrapper를 재생성하거나, 검증된 Project Template의 Wrapper File 전체를 사용한다. `gradle-wrapper.jar`, Script와 Properties를 함께 Commit해야 Local과 Jenkins가 같은 Gradle Version을 사용한다.

문제를 해결한 뒤 Jenkins에서 다음 항목을 다시 확인한다.

1. `./gradlew --version`에 표시된 JVM과 Gradle Version이 Project 조건을 만족하는가

2. Toolchain을 자동으로 받는다면 Agent에서 Download 대상에 접근할 수 있는가

3. `./gradlew clean build`가 Test와 `bootJar`까지 완료하는가

4. `build/libs`에 배포할 JAR가 생성됐는가

> **최종 정리**
> - Jenkins는 실행을 조정하고 Maven과 Gradle은 Dependency 해결, Compile, Test와 Package를 수행한다.
>
> - Maven의 `package`는 앞선 Compile과 Test Phase를 포함하므로 `clean package`로 충분하다.
>
> - Maven과 Gradle 표준 Directory에서 Test Report와 JAR·WAR 결과를 확인하고 Build Number에 연결해 Artifact로 보관한다.
>
> - Poll SCM은 약 5분마다 변경을 확인하고 변경된 Revision이 있을 때 Build를 시작한다.
>
> - SMTP App Password는 Credential로 관리하고 Email 전송 결과와 Build 결과를 분리해 진단한다.
>
> - Gradle Java Toolchain 오류는 Agent JDK, Project의 `languageVersion`, Wrapper Version과 Toolchain Repository를 순서대로 확인한다.
