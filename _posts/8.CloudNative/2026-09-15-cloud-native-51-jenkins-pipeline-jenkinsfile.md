---
title: Jenkins Pipeline과 Jenkinsfile 기반 배포
description: Jenkins Pipeline의 Declarative·Scripted 문법을 구분하고 Jenkinsfile로 Checkout, Gradle Build, Docker Image Push와 SSH 배포를 연결한다
date: 2026-09-15
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Jenkins
---

[Jenkins Freestyle Trigger와 SSH·Docker 배포](/cloud-native-50-jenkins-freestyle-deployment/)에서는 UI에 Build Step과 Post-build Action을 구성했다. Pipeline은 같은 흐름을 Code로 정의해 Source와 함께 Version 관리한다. 이 글에서는 Pipeline 문법을 구분하고 Checkout, Build, Image Push와 SSH 배포가 어느 실행 환경에서 이어지는지 정리한다.

## 1 ) Freestyle Job 연결과 Pipeline

---

Freestyle Job도 **Build other projects**와 **Build after other projects are built**를 사용해 여러 Job을 연결할 수 있다. 예를 들어 `Ready → Build → Deploy`로 구성하면 각 Job의 책임과 권한을 분리할 수 있다.

| Job | 주요 작업 | 다음 Job 실행 조건 |
|---|---|---|
| Ready | Source와 실행 환경 준비 | 성공 시 Build 시작 |
| Build | Compile, Test와 Package | 성공 시 Deploy 시작 |
| Deploy | Artifact 또는 Image 배포 | Pipeline 종료 |

Delivery Pipeline Plugin을 설치하면 **Dashboard → New View → Delivery Pipeline View**에서 Upstream과 Downstream Job의 실행 상태를 한 흐름으로 볼 수 있다. 다만 Job 설정이 Jenkins UI 여러 곳에 분산되므로 변경 이력과 Review가 어렵다.

Pipeline은 Stage와 Step을 `Jenkinsfile`에 정의한다.

- **Stage**는 Checkout, Build, Test와 Deploy처럼 사용자가 구분해서 볼 실행 구간이다.

- **Step**은 `sh`, `git`, `echo`와 같이 Stage 안에서 실제로 실행하는 작업이다.

- **Agent**는 Pipeline 전체 또는 특정 Stage를 실행할 Jenkins Node와 Executor를 선택한다.

- **Post**는 성공, 실패 또는 결과와 관계없이 수행할 후처리를 정의한다.

Pipeline은 Job 구성을 Source와 함께 Review하고, 같은 정의로 다시 실행하며, Stage별 결과와 Log를 추적할 수 있다는 장점이 있다.

## 2 ) Declarative와 Scripted Pipeline 구분

---

Jenkins Pipeline은 Declarative와 Scripted 두 방식으로 작성할 수 있다.

| 구분 | 최상위 구조 | 특징 | 적합한 경우 |
|---|---|---|---|
| Declarative Pipeline | `pipeline {}` | 정해진 Section과 검증 가능한 구조 | 일반적인 CI/CD Pipeline |
| Scripted Pipeline | `node {}` | Groovy Flow Control을 직접 사용 | 동적 제어가 많은 복잡한 흐름 |

`pipeline {}`이 Declarative이고 `node {}`가 Scripted이다. 두 방식 모두 처리하지 않은 Step 실패가 발생하면 해당 실행 흐름이 실패하며 이후 Stage는 기본적으로 실행되지 않는다. 실패 후에도 특정 Step을 계속하려면 Declarative의 `post`, `catchError` 또는 Scripted의 `try-catch-finally`처럼 실패 처리 방식을 명시해야 한다.

Jenkins가 지원하는 Directive와 조건은 [Pipeline Syntax](https://www.jenkins.io/doc/book/pipeline/syntax/)에서 확인할 수 있다.

## 3 ) Scripted Pipeline 기본 구조

---

Scripted Pipeline은 `node` Block 안에서 Groovy 기반 Step을 순서대로 실행한다.

```groovy
node {
    stage('Ready') {
        echo 'Prepare workspace'
    }

    stage('Build') {
        echo 'Build application'
    }

    stage('Deploy') {
        echo 'Deploy application'
    }
}
```

`node`는 사용 가능한 Executor 하나를 점유하고 Workspace를 할당한다. Label이 있는 Agent에서 실행하려면 다음처럼 지정한다.

```groovy
node('docker-builder') {
    stage('Build Image') {
        sh 'docker version'
    }
}
```

동적 반복과 조건이 필요하면 Groovy 문법을 사용할 수 있다. 오류를 처리하지 않으면 Pipeline이 실패하므로, 계속 실행해야 하는 범위만 명확히 감싼다.

```groovy
node {
    try {
        stage('Build') {
            sh './gradlew clean build'
        }
    } catch (Exception error) {
        currentBuild.result = 'FAILURE'
        throw error
    } finally {
        echo "Result: ${currentBuild.currentResult}"
    }
}
```

## 4 ) Declarative Pipeline 기본 구조

---

Declarative Pipeline은 `pipeline`, `agent`, `stages`, `stage`와 `steps` 구조를 사용한다.

```groovy
pipeline {
    agent any

    stages {
        stage('Compile') {
            steps {
                echo 'Compile source'
            }
        }

        stage('Test') {
            steps {
                echo 'Run tests'
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploy application'
            }
        }
    }

    post {
        success {
            echo 'Pipeline succeeded'
        }

        failure {
            echo 'Pipeline failed'
        }

        always {
            echo "Final result: ${currentBuild.currentResult}"
        }
    }
}
```

| `post` 조건 | 실행 시점 |
|---|---|
| `always` | 결과와 관계없이 실행 |
| `success` | Pipeline 또는 Stage 성공 |
| `failure` | 이전 결과보다 실패 상태가 된 경우 |
| `unstable` | Test 실패 등으로 Unstable 상태가 된 경우 |
| `changed` | 이전 Build와 결과가 달라진 경우 |

`post`는 알림, Test Report 게시, Artifact 보관과 임시 Resource 정리에 사용한다. 실패를 숨기는 용도가 아니라 실패 후에도 반드시 필요한 작업을 실행하는 구간이다.

## 5 ) Source Checkout

---

Pipeline Script에 Repository를 직접 지정하려면 `git` Step을 사용할 수 있다.

```groovy
stage('Checkout') {
    steps {
        git branch: 'main',
            credentialsId: 'github-read-credential',
            url: 'https://github.com/<owner>/<repository>.git'
    }
}
```

| Parameter | 역할 |
|---|---|
| `branch` | Checkout할 Branch |
| `credentialsId` | Private Repository 읽기에 사용할 Jenkins Credential ID |
| `url` | Git Repository URL |

Job이 **Pipeline script from SCM** 방식으로 `Jenkinsfile`을 읽었다면 Jenkins가 이미 같은 Repository를 Checkout할 정보를 알고 있다. 이 경우 `checkout scm`을 사용하면 Job의 SCM 설정과 Branch 정보를 재사용할 수 있다.

```groovy
stage('Checkout') {
    steps {
        checkout scm
    }
}
```

## 6 ) Jenkinsfile을 Repository에서 관리

---

Repository Root에 `Jenkinsfile`을 Commit하면 Pipeline 변경도 Application Code와 함께 Review할 수 있다.

```text
calculator/
├── Jenkinsfile
├── Dockerfile
├── build.gradle
├── gradlew
├── gradle/
└── src/
```

Jenkins에서 새 Pipeline Job을 만들고 **Pipeline → Definition → Pipeline script from SCM**을 선택한다.

| 항목 | 설정 |
|---|---|
| SCM | Git |
| Repository URL | Application Repository URL |
| Credentials | Private Repository 읽기 Credential |
| Branch Specifier | Build할 Branch |
| Script Path | 기본값 `Jenkinsfile` 또는 실제 상대 경로 |

Script Path는 Workspace 기준 상대 경로이며 File명은 대소문자를 구분한다. 저장 후 **Build Now**를 실행하고 Console Output에서 Jenkinsfile Checkout과 Stage 진입 순서를 확인한다.

{% include visuals/jenkins-pipeline-release-flow.html %}

## 7 ) Gradle Build와 Docker Image Push Pipeline

---

다음 Declarative Pipeline은 Docker 명령을 실행할 수 있는 `docker-builder` Label의 Agent에서 동작한다. Jenkins Controller가 아니라 Build 전용 Agent를 선택하는 이유는 Source Build와 Docker Daemon 권한을 제어 영역에서 분리하기 위해서이다.

```groovy
pipeline {
    agent { label 'docker-builder' }

    environment {
        IMAGE_NAME = '<dockerhub-username>/calculator'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                sh '''
                    test -x ./gradlew
                    ./gradlew clean build
                '''
            }
        }

        stage('Set Image Tag') {
            steps {
                script {
                    env.IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(12)}"
                }
            }
        }

        stage('Build Image') {
            steps {
                sh 'docker build --tag "$IMAGE_NAME:$IMAGE_TAG" .'
            }
        }

        stage('Push Image') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-credential',
                        usernameVariable: 'DOCKERHUB_USERNAME',
                        passwordVariable: 'DOCKERHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        printf '%s' "$DOCKERHUB_TOKEN" | docker login \
                          --username "$DOCKERHUB_USERNAME" \
                          --password-stdin
                        docker push "$IMAGE_NAME:$IMAGE_TAG"
                        docker logout
                    '''
                }
            }
        }
    }

    post {
        success {
            archiveArtifacts artifacts: 'build/libs/*.jar', fingerprint: true
        }
    }
}
```

`gradlew`의 실행 Bit는 Repository에 Commit해 두는 것이 좋다. Pipeline에서 매번 `chmod 777 gradlew`를 실행하면 불필요한 사용자에게 쓰기 권한까지 부여한다. 실행 Bit가 누락됐다면 개발 환경에서 `git update-index --chmod=+x gradlew`로 수정해 Commit한다.

Image Tag에는 Build Number와 Commit SHA를 함께 넣었다. 동일한 Source Build를 식별할 수 있고 이전 Version으로 되돌릴 때도 정확한 Image를 선택할 수 있다.

## 8 ) SSH Agent를 이용한 원격 배포

---

SSH Agent Plugin은 Jenkins Credential에 저장한 Private Key를 Build 실행 중 임시 SSH Agent에 연결한다. Pipeline Script에 Private Key 내용을 직접 기록하지 않고 `ssh`와 `scp`가 인증에 사용하도록 한다.

**Manage Jenkins → Credentials**에서 **SSH Username with private key** 유형을 추가한다.

| 항목 | 역할 |
|---|---|
| ID | Pipeline에서 참조할 `deploy-server-ssh` |
| Username | 배포 Server의 전용 계정 |
| Private Key | Server의 `authorized_keys`에 등록한 Public Key와 짝을 이루는 Key |
| Passphrase | Private Key 생성 시 설정한 암호 |

Build Agent의 `known_hosts`에는 검증한 배포 Server Host Key가 미리 등록되어 있어야 한다. `StrictHostKeyChecking=no`로 검증을 건너뛰지 않는다.

Image Push 뒤에 다음 Stage를 추가한다.

```groovy
stage('Deploy') {
    steps {
        sshagent(credentials: ['deploy-server-ssh']) {
            sh '''
                ssh -o BatchMode=yes \
                  "$DEPLOY_USER@$DEPLOY_HOST" \
                  "IMAGE_NAME='$IMAGE_NAME' IMAGE_TAG='$IMAGE_TAG' bash ~/deploy/deploy.sh"
            '''
        }
    }
}
```

`DEPLOY_USER`와 `DEPLOY_HOST`는 Agent 환경 또는 Jenkins의 관리되는 설정에 둔다. IP와 Username 자체가 Secret은 아니더라도 환경별 값이므로 Pipeline Code와 분리하면 같은 Jenkinsfile을 개발·검증·운영 환경에서 재사용하기 쉽다.

배포 Server의 `~/deploy/deploy.sh`는 전달받은 Image Tag를 사용한다.

```bash
#!/usr/bin/env bash
set -euo pipefail

: "${IMAGE_NAME:?IMAGE_NAME is required}"
: "${IMAGE_TAG:?IMAGE_TAG is required}"

CONTAINER_NAME="calculator"

docker pull "$IMAGE_NAME:$IMAGE_TAG"

if docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
    docker stop --time 30 "$CONTAINER_NAME" || true
    docker rm "$CONTAINER_NAME" || true
fi

docker run --detach \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  --publish 9000:9000 \
  "$IMAGE_NAME:$IMAGE_TAG"
```

이 Script는 `latest` 대신 Pipeline이 Push한 고정 Tag를 Pull한다. 같은 이름의 Container만 중지하고 다시 생성하므로 다른 Application Container에 영향을 주지 않는다. `docker system prune -a -f`는 Host의 다른 Image와 Build Cache까지 제거할 수 있으므로 공용 Server의 자동 배포 Script에 넣지 않는다.

배포 계정을 Docker Group에 추가하면 Password 없이 Docker Daemon을 제어할 수 있지만 사실상 Root 수준 권한이 생긴다. 배포 전용 Server와 계정을 사용하고 SSH Key, Jenkins Credential과 Job 실행 권한을 제한한다.

## 9 ) Pipeline 실행 흐름 확인

---

Pipeline을 실행한 뒤 Stage별로 다음을 확인한다.

1. **Checkout**: Console Output의 Commit SHA가 Webhook 또는 수동 실행 대상과 일치하는가

2. **Build**: Gradle Test가 성공하고 `build/libs/calculator.jar`가 생성됐는가

3. **Build Image**: Image에 Build Number와 Commit SHA Tag가 붙었는가

4. **Push Image**: Registry에 같은 Tag가 존재하며 Credential이 Log에 노출되지 않았는가

5. **Deploy**: SSH Host Key 검증이 성공하고 지정한 Container만 교체됐는가

6. **Application**: 배포 Server에서 Container 상태, Log와 HTTP Endpoint가 정상인가

```bash
docker ps --filter name=calculator
docker logs --tail 100 calculator
curl --fail "http://localhost:9000/"
```

Pipeline 설정과 Jenkinsfile 운영 방법은 [Using a Jenkinsfile](https://www.jenkins.io/doc/book/pipeline/jenkinsfile/), SSH Credential 사용법은 [SSH Agent Plugin](https://plugins.jenkins.io/ssh-agent/)을 참고한다.

> **최종 정리**
> - `pipeline {}`은 Declarative Pipeline이고 `node {}`는 Scripted Pipeline이다.
>
> - 처리하지 않은 Step 실패는 두 방식 모두 실행 흐름을 중단하며, 계속할 작업은 `post`, `catchError` 또는 예외 처리로 명시한다.
>
> - Jenkinsfile을 SCM에서 읽으면 `checkout scm`으로 Job의 Repository와 Branch 정보를 재사용할 수 있다.
>
> - Docker Build는 Controller가 아닌 전용 Agent에서 실행하고 Credential은 `withCredentials`로 필요한 Stage에만 주입한다.
>
> - SSH Agent는 Jenkins Private Key를 실행 중에만 연결하며, 배포 대상은 검증된 `known_hosts`로 확인한다.
>
> - Build Number와 Commit SHA로 고정한 Image Tag를 배포하면 실행 Version과 Rollback 대상을 추적할 수 있다.
