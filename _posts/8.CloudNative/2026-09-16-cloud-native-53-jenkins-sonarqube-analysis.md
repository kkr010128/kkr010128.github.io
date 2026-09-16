---
title: Jenkins SonarQube 정적 분석과 Quality Gate
description: SonarQube를 Docker로 구성하고 Gradle 분석, Token Credential과 Jenkins Pipeline Quality Gate를 안전하게 연결한다
date: 2026-09-16
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Jenkins
---

[Jenkins 단위 테스트와 JaCoCo Code Coverage](/cloud-native-52-jenkins-unit-test-jacoco/)에서는 실행 결과와 Coverage로 Application 동작을 검증했다. 정적 분석은 Code를 실행하지 않고 잠재적인 Bug, Vulnerability, 중복과 유지보수 문제를 찾는다. 이 글에서는 SonarQube 분석을 Gradle과 Jenkins Pipeline에 연결한다.

## 1 ) 정적 분석의 역할

---

> **정적 Code 분석**은 Program을 실행하지 않고 Source Code와 Bytecode를 검사해 규칙 위반과 잠재적인 결함을 찾는 과정이다.

- **Code 품질 개선**: 복잡한 Code, 중복, 읽기 어려운 구조와 Coding Convention 위반을 찾는다.

- **Bug 사전 탐지**: Null 처리와 Resource 누수처럼 Runtime 장애로 이어질 수 있는 Pattern을 확인한다.

- **보안 강화**: Injection, 취약한 암호화와 입력값 검증 누락 같은 보안 문제를 탐지한다.

- **일관성 유지**: Team이 정한 Rule을 같은 기준으로 반복 적용한다.

대표적인 Java 정적 분석 도구에는 SonarQube, Checkstyle, SpotBugs, PMD와 FindSecBugs가 있다. 각 도구의 Rule과 탐지 범위가 다르므로 한 도구의 통과가 모든 결함의 부재를 의미하지는 않는다.

## 2 ) SonarQube와 Quality Gate

---

SonarQube는 분석 결과를 Server에 저장하고 Project별 Issue와 변화 추이를 제공한다. 지원 언어와 Rule은 SonarQube Edition과 Version, 설치한 Analyzer에 따라 달라진다.

| 항목 | 의미 |
|---|---|
| Bugs | 오동작으로 이어질 가능성이 있는 Code |
| Vulnerabilities | 공격자가 악용할 수 있는 보안 취약점 |
| Security Hotspots | 보안 관점의 Review가 필요한 민감한 Code |
| Code Smells | 유지보수성과 이해도를 낮추는 Code |
| Coverage | Test Report를 통해 계산한 Coverage |
| Duplications | 중복된 Code 비율과 Block |
| Lines | 분석한 Source Line 규모 |

> **Quality Gate**는 Coverage, 신규 Bug와 중복률 같은 조건을 묶은 통과 기준이다. 분석 결과가 기준을 만족하면 통과하고, 만족하지 못하면 실패 상태가 된다.

Quality Gate는 정적 분석 결과에 대한 자동 판정 기준이다. Application의 기능 Test와 Runtime 검증을 대체하지 않는다.

## 3 ) Docker로 학습용 SonarQube 실행

---

Jenkins와 SonarQube Container가 이름으로 통신하도록 사용자 정의 Network를 먼저 만든다.

```bash
docker network create ci-network
```

[SonarQube Docker 설치 문서](https://docs.sonarsource.com/sonarqube-server/latest/server-installation/from-docker-image/starting-sonarqube-container/)와 Image Registry에서 사용할 Community Build Tag를 확인한 뒤 실행한다.

```bash
SONARQUBE_IMAGE='sonarqube:<verified-community-tag>'

docker run -d \
  --name sonarqube \
  --network ci-network \
  -p 9000:9000 \
  "$SONARQUBE_IMAGE"
```

`http://localhost:9000`에 접속한다. 초기 계정은 `admin`, 비밀번호도 `admin`이며 첫 Login 직후 변경해야 한다.

이 구성은 구조를 익히는 학습용이다. `--rm`을 사용하거나 Volume 없이 Container를 제거하면 분석 이력과 설정을 잃을 수 있다. 운영 환경에서는 외부 Database와 Persistent Volume을 구성해야 하며, 내장 H2 Database는 Test와 Trial 용도로만 사용한다. 지원 Database와 Version은 [Database 설치 문서](https://docs.sonarsource.com/sonarqube-server/server-installation/installing-the-database)에서 확인한다.

## 4 ) 분석 Token 생성과 보관

---

SonarQube에서 계정 Menu의 **My Account → Security**로 이동해 Token 이름, 종류와 만료일을 지정하고 생성한다. Token 값은 생성 직후 한 번만 확인할 수 있으므로 Password Manager 또는 Jenkins Credential에 저장한다.

다음 위치에는 실제 Token을 기록하지 않는다.

- Git으로 관리하는 `build.gradle`과 `Jenkinsfile`

- Blog, Screenshot과 공유 문서

- Shell History에 남는 명령행 Argument

이미 노출된 Token은 문자열을 가리는 것만으로 안전해지지 않는다. SonarQube에서 폐기한 뒤 새 Token을 발급해야 한다.

## 5 ) Gradle Project에 SonarQube 적용

---

`build.gradle`의 `plugins` Block에 SonarQube Plugin을 추가한다.

```groovy
plugins {
    id 'java'
    id 'org.sonarqube' version '7.2.3.7755'
}
```

`7.2.3.7755`는 이 Project에서 사용하는 예시 Version이다. 새 Project에서는 [Gradle Plugin Portal](https://plugins.gradle.org/plugin/org.sonarqube)에서 현재 Version과 Gradle·JDK 호환성을 확인한다.

Application Build와 Test를 먼저 수행한다.

```bash
./gradlew clean build
```

Token은 `SONAR_TOKEN` 환경 변수로 전달하고, Server URL만 System Property로 지정한다.

```bash
export SONAR_TOKEN='<SONARQUBE_TOKEN>'
./gradlew sonar -Dsonar.host.url=http://localhost:9000
unset SONAR_TOKEN
```

`sonar.login`과 `sonar.password`는 Deprecated되었으며 `sonar.token` 또는 `SONAR_TOKEN`으로 대체되었다. Token을 명령행이나 Project File에 직접 기록하지 않는 방법은 [SonarScanner 분석 Parameter 문서](https://docs.sonarsource.com/sonarqube-server/analyzing-source-code/analysis-parameters/parameters-not-settable-in-ui)에서 확인할 수 있다.

분석이 완료되면 SonarQube Project 화면에서 Issue, Coverage, 중복과 Quality Gate 결과를 확인한다. Scanner 요구 사항과 분석 Task는 [SonarScanner for Gradle 문서](https://docs.sonarsource.com/sonarqube-server/analyzing-source-code/scanners/sonarscanner-for-gradle)에서 Version별로 확인한다.

## 6 ) Jenkins와 SonarQube 통신 구조

---

Jenkins와 SonarQube가 각각 Container에서 실행되면 Jenkins Container의 `localhost`는 Jenkins 자신을 가리킨다. 두 Container를 같은 사용자 정의 Network에 연결하고 SonarQube Container 이름을 DNS 주소로 사용한다.

```bash
docker network connect ci-network jenkins
```

앞 절의 명령으로 SonarQube를 실행했다면 `sonarqube`는 이미 `ci-network`에 연결되어 있다. 기존 Jenkins Container만 같은 Network에 추가한다.

Jenkins에서 사용할 URL은 다음과 같다.

```text
http://sonarqube:9000
```

기본 `bridge` Network에서 조회한 Container IP는 재생성할 때 바뀔 수 있다. Pipeline에 고정 IP를 넣지 않고 사용자 정의 Network의 Container 이름을 사용한다.

| 통신 주체 | 사용 주소 | 이유 |
|---|---|---|
| Host Browser | `http://localhost:9000` | Host에 공개한 Port로 접근 |
| Jenkins Container | `http://sonarqube:9000` | 같은 Docker Network의 DNS 이름으로 접근 |
| SonarQube Container 자신 | `http://localhost:9000` | 자기 Network Namespace 안의 Process에 접근 |

## 7 ) Jenkins SonarQube 설정

---

Jenkins에서 다음 순서로 설정한다.

1. **Manage Jenkins → Plugins**에서 **SonarQube Scanner for Jenkins** Plugin을 설치한다.

2. **Manage Jenkins → Credentials**에서 SonarQube Token을 **Secret text**로 저장한다. 예시 Credential ID는 `sonarqube-token`이다.

3. **Manage Jenkins → System → SonarQube servers**에 Server를 추가한다.

4. Name을 `SonarQube-Server`, Server URL을 `http://sonarqube:9000`, Authentication Token을 `sonarqube-token`으로 설정한다.

Plugin과 Server 설정 절차는 [Jenkins용 SonarQube 설정 문서](https://docs.sonarsource.com/sonarqube-server/analyzing-source-code/ci-integration/jenkins-integration/global-setup)에서 확인할 수 있다.

`withSonarQubeEnv('SonarQube-Server')`는 Jenkins에 등록한 Server URL과 Token을 분석 Step의 환경에 주입한다. Token을 Pipeline 전역 `environment`에 두지 않으므로 노출 범위를 분석 Stage로 제한할 수 있다.

## 8 ) Test와 SonarQube 분석 Pipeline

---

다음 Jenkinsfile은 Test를 통과한 Source만 SonarQube로 분석한다.

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
                sh './gradlew clean test jacocoTestReport'
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube-Server') {
                    sh './gradlew sonar'
                }
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

| Stage | Jenkins Agent에서 수행하는 작업 | 외부 연결 |
|---|---|---|
| Checkout | Repository Source와 Jenkinsfile 확보 | Git Server |
| Unit Test | JUnit 실행과 JaCoCo XML·HTML 생성 | Gradle Dependency Repository |
| SonarQube Analysis | Source와 Coverage Report 분석 요청 | `SonarQube-Server` |

`compileJava`는 `test` Task가 필요에 따라 실행하므로 별도 Stage로 중복하지 않는다. `withSonarQubeEnv`를 사용할 때는 Jenkins System 설정의 이름과 문자열이 정확히 일치해야 한다.

## 9 ) Quality Gate로 Pipeline 중단

---

SonarQube가 Jenkins에 분석 완료 결과를 돌려주도록 Webhook을 구성하면 Pipeline에서 Quality Gate를 기다릴 수 있다.

SonarQube의 Project 또는 Global Webhook URL을 다음 형식으로 설정한다.

```text
http://<jenkins-host>/sonarqube-webhook/
```

마지막 `/`도 URL에 포함한다. Analysis Stage 뒤에 다음 Stage를 추가한다.

```groovy
stage('Quality Gate') {
    steps {
        timeout(time: 10, unit: 'MINUTES') {
            waitForQualityGate abortPipeline: true
        }
    }
}
```

`waitForQualityGate`는 Webhook 결과를 기다리고, `abortPipeline: true`는 Gate 실패 시 Pipeline을 중단한다. 무기한 대기를 막기 위해 `timeout`을 함께 둔다. Jenkins Extension의 Pipeline 사용 방법은 [SonarQube Jenkins Extension 문서](https://docs.sonarsource.com/sonarqube-server/analyzing-source-code/scanners/jenkins-extension-sonarqube)에서 확인할 수 있다.

> **최종 정리**
> - 정적 분석은 Test 실행 여부와 별개로 Bug, Vulnerability와 유지보수 문제를 찾는다.
>
> - 학습용 Container와 운영용 SonarQube의 Database·Volume 구성을 구분한다.
>
> - Token은 Jenkins Secret Text로 저장하고 분석 Stage에서만 주입한다.
>
> - Container 간 통신에는 바뀔 수 있는 고정 IP 대신 사용자 정의 Network의 DNS 이름을 사용한다.
>
> - SonarQube Analysis와 Quality Gate를 연결하면 기준을 만족하지 못한 Code의 후속 배포를 중단할 수 있다.
