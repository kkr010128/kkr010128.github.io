---
title: 애플리케이션별 Docker 이미지 빌드
description: Django, FastAPI, Spring Boot, Node.js, Go 애플리케이션을 Docker 이미지로 빌드하고 실행하는 방법
date: 2026-08-19
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Docker
---
## 1 ) 애플리케이션 Image Build 흐름

---

애플리케이션의 언어와 Framework가 달라도 Docker Image를 만드는 전체 과정은 비슷하다.

1. Host에서 Application을 작성하고 실행을 확인한다.

2. Package 의존성을 File로 정의한다.

3. Base Image, 작업 Directory, 복사 대상과 실행 명령을 Dockerfile에 작성한다.

4. 가상 환경, Log, Build Cache처럼 Image에 넣지 않을 대상을 `.dockerignore`에 등록한다.

5. `docker build`로 Image를 생성한다.

6. Image로 Container를 실행하고 Host Port를 연결한다.

7. Browser나 `curl`로 Application의 응답을 확인한다.

각 애플리케이션은 의존성을 표현하고 실행하는 방식에서 차이가 난다.

| 애플리케이션 | Base Image | 의존성 또는 Build 입력 | Image의 실행 대상 | Container 실행 명령 |
|---|---|---|---|---|
| Django | `python` | `requirements.txt` | Python Source Code | `manage.py runserver` |
| FastAPI | `python` | `requirements.txt` | Python Source Code | `uvicorn` |
| Spring Boot | `eclipse-temurin:21-jdk` | Gradle로 만든 JAR | Build된 JAR | `java -jar` |
| Node.js | `node:20-slim` | `package.json` | JavaScript Source Code | `node app.js` |
| Go | `golang:1.23-alpine` | `go.mod`, Go Source Code | Compile한 Binary | `./main` |
| Apache Web | `ubuntu:20.04` | `webapp.tar.gz` | 압축 해제한 Web Source | `apachectl` |

Python과 Node.js 예제는 Source Code와 Runtime을 함께 Image에 넣는다. Spring Boot는 Host에서 Build한 JAR를 복사하고, Go 예제는 Image를 Build하는 과정에서 Source Code를 Compile한다.

## 2 ) Django Application Image

---

Django Application을 먼저 Host에서 실행한 뒤 Package 의존성과 Source Code를 Image에 복사한다. Host의 Python Package와 프로젝트 Package가 섞이지 않도록 가상 환경을 사용한다.

### 프로젝트 생성과 실행

1. Python Package 설치와 가상 환경 생성에 필요한 Package를 준비한다.

   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-pip python3-venv
   ```

2. 작업 Directory를 생성한다.

   ```bash
   mkdir django_workspace
   cd django_workspace
   ```

3. Python 가상 환경을 생성하고 활성화한다.

   ```bash
   python3 -m venv ./myvenv
   source ./myvenv/bin/activate
   ```

   가상 환경 생성 기능이 설치되어 있지 않다면 Ubuntu에서는 `python3-venv` Package가 필요할 수 있다.

4. Django를 설치하고 프로젝트를 생성한다.

   ```bash
   pip install django
   django-admin startproject dockeredjango
   cd dockeredjango
   ```

5. 개발 Server를 실행한다.

   ```bash
   python manage.py runserver
   ```

6. 다른 Terminal에서 응답을 확인한다.

   ```bash
   curl http://localhost:8000
   ```

### 의존성 File 생성

현재 가상 환경의 Package와 Version을 `requirements.txt`로 저장한다.

```bash
pip freeze > requirements.txt
```

### Dockerfile

```dockerfile
FROM python

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

Dockerfile의 주요 동작은 다음과 같다.

- `requirements.txt`를 먼저 복사하고 Package를 설치한다.

- 프로젝트 Source Code는 Package 설치 뒤에 복사한다.

- Django 개발 Server가 Container 밖의 요청을 받을 수 있도록 `0.0.0.0:8000`에서 실행한다.

### Image Build와 Container 실행

```bash
docker build -t dockerdjango:latest .
docker container run \
  --name dockerdjango \
  -d \
  -p 8000:8000 \
  dockerdjango:latest
```

```bash
curl http://localhost:8000
```

`manage.py runserver`는 개발 과정에서 사용하는 Server이다. 이 실습에서는 Container Image 제작 흐름을 확인하기 위해 사용한다.

## 3 ) FastAPI Application Image

---

FastAPI도 Python Source Code와 `requirements.txt`를 Image에 복사하지만 Application은 Uvicorn으로 실행한다.

### 프로젝트 생성과 실행

1. 작업 Directory를 만들고 가상 환경을 활성화한다.

   ```bash
   mkdir fastapi_workspace
   cd fastapi_workspace
   python3 -m venv ./myvenv
   source ./myvenv/bin/activate
   ```

2. FastAPI와 Uvicorn을 설치한다.

   ```bash
   pip install fastapi uvicorn
   ```

3. `main.py`를 작성한다.

   ```python
   from fastapi import FastAPI

   app = FastAPI()


   @app.get("/")
   def read_root():
       return {"Hello": "World"}


   @app.get("/items/{item_id}")
   def read_item(item_id: int, q: str | None = None):
       return {"item_id": item_id, "q": q}
   ```

4. 개발 Server를 실행하고 응답을 확인한다.

   ```bash
   uvicorn main:app --reload
   ```

   ```bash
   curl http://localhost:8000
   curl 'http://localhost:8000/items/1?q=docker'
   ```

### 의존성 File과 `.dockerignore`

```bash
pip freeze > requirements.txt
```

Host의 가상 환경과 Python Cache는 Image에 복사하지 않는다.

```text
myvenv/
__pycache__/
.pytest_cache/
.env
```

### Dockerfile

```dockerfile
FROM python

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`requirements.txt`를 Source Code보다 먼저 복사하면 다음과 같이 Build Cache를 활용할 수 있다.

1. `requirements.txt`가 바뀌지 않으면 `pip install` Layer를 재사용한다.

2. Source Code만 수정하면 `COPY . .` 이후의 Layer만 다시 Build한다.

3. 시간이 오래 걸리는 Package 설치를 매번 반복하지 않는다.

### Image Build와 Container 실행

```bash
docker build -t my-fastapi-app .
docker container run \
  --name my-fastapi-app \
  -d \
  -p 8000:8000 \
  my-fastapi-app
```

```bash
curl http://localhost:8000
```

> **중간 정리**
>
> - Django와 FastAPI는 Python Runtime, Package 의존성과 Source Code를 Image에 포함한다.
>
> - 두 예제 모두 `requirements.txt`를 먼저 복사하여 Package 설치 Layer의 Cache를 활용한다.
>
> - Host의 가상 환경은 Image에 복사하지 않으며 Container 안에서 필요한 Package를 다시 설치한다.
>
> - Container 밖에서 접속하려면 Application이 `0.0.0.0`에서 요청을 받아야 한다.

## 4 ) Spring Boot Application Image

---

Python 예제는 Source Code를 Interpreter로 실행했지만 Java Application은 Gradle로 JAR를 Build한 뒤 결과물을 Image에 복사한다.

### 프로젝트 준비와 Build

1. Git을 설치하고 실습 Repository를 가져온다.

   ```bash
   sudo apt-get update
   sudo apt-get install -y git
   git clone https://github.com/itggangpae/spring_docker.git
   cd spring_docker
   ```

2. Linux에서 Gradle Wrapper를 실행할 수 있도록 권한을 부여한다.

   ```bash
   chmod +x ./gradlew
   ```

3. Application을 실행하여 동작을 확인한다.

   ```bash
   ./gradlew bootRun
   ```

4. 실행을 중지한 뒤 배포할 JAR를 Build한다.

   ```bash
   ./gradlew clean build
   ls ./build/libs
   ```

Build 결과는 `./build/libs`에 생성된다.

### Dockerfile

```dockerfile
FROM eclipse-temurin:21-jdk

WORKDIR /app

COPY ./build/libs/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
```

이 Dockerfile은 Gradle Build를 Image 안에서 다시 수행하지 않는다. Host에서 생성한 JAR만 복사하여 `java -jar`로 실행한다.

### Image Build와 Container 실행

```bash
docker build -t spring_docker:1.0.0 .
docker container run \
  --name spring_docker \
  -p 8000:8080 \
  spring_docker:1.0.0
```

```bash
curl http://localhost:8000
```

강의 Dockerfile에는 Gradle 프로젝트에서 Maven Wrapper인 `./mvnw`를 실행하는 `CMD`와 JAR를 실행하는 `ENTRYPOINT`가 함께 작성되어 있었다. 이 실습은 Host에서 Gradle Build를 마친 JAR를 실행하는 방식이므로 Maven 명령을 제거하고 JAR 실행 명령만 남겼다.

## 5 ) Node.js Application Image

---

Node.js Application은 Python Application과 마찬가지로 의존성 File과 Source Code를 Image에 복사한 뒤 Runtime으로 실행한다.

### 프로젝트 생성과 실행

1. Node.js와 npm을 설치한다.

   ```bash
   sudo apt-get update
   sudo apt-get install -y nodejs npm
   ```

2. 작업 Directory를 Node.js 프로젝트로 초기화하고 Package를 설치한다.

   ```bash
   mkdir node_workspace
   cd node_workspace
   npm init
   npm install express nodemon
   ```

3. `package.json`의 `scripts`에 실행 명령을 작성한다.

   ```json
   {
     "scripts": {
       "start": "node app.js"
     }
   }
   ```

4. `app.js`를 작성한다.

   ```javascript
   const express = require('express');

   const app = express();
   app.set('port', process.env.PORT || 3000);

   app.get('/', (req, res) => {
     res.send('Hello Express');
   });

   app.listen(app.get('port'), () => {
     console.log(`${app.get('port')}번에서 대기 중`);
   });
   ```

5. Application을 실행하고 응답을 확인한다.

   ```bash
   node app.js
   ```

   ```bash
   curl http://localhost:3000
   ```

### `.dockerignore`

Host에서 설치한 `node_modules`는 Image에 복사하지 않는다. Container의 Platform에 맞는 Package는 Image Build 과정에서 다시 설치한다.

```text
node_modules/
npm-debug.log
.git/
.env
```

### Dockerfile

```dockerfile
FROM node:20-slim

WORKDIR /usr/src/app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["node", "app.js"]
```

`package.json`과 Package Lock File을 먼저 복사하면 Source Code만 변경되었을 때 `npm install` Layer를 재사용할 수 있다.

### Image Build와 Container 실행

```bash
docker build -t node_app .
docker container run \
  --name nodeapp \
  -d \
  -p 8000:3000 \
  node_app
```

```bash
curl http://localhost:8000
```

## 6 ) Go Application Image

---

Go Application은 Compile한 실행 File을 Container의 주 Process로 실행한다. 이 실습에서는 Go Base Image 안에서 의존성을 내려받고 Source Code를 Build한다.

### Go 설치

강의에서는 Go 1.22.0 Archive를 내려받아 `/usr/local`에 설치했다.

```bash
curl -OL https://golang.org/dl/go1.22.0.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.22.0.linux-amd64.tar.gz
```

`~/.profile`에 Go 실행 경로를 추가하고 현재 Shell에 적용한다.

```bash
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.profile
echo 'export PATH=$PATH:$(go env GOPATH)/bin' >> ~/.profile
source ~/.profile
```

### 프로젝트 생성과 실행

1. 빈 Directory에서 Go Module을 생성한다.

   ```bash
   mkdir go_workspace
   cd go_workspace
   go mod init my-go-app
   ```

2. `main.go`를 작성한다.

   ```go
   package main

   import (
       "encoding/json"
       "fmt"
       "net/http"
   )

   func main() {
       http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
           w.Header().Set("Content-Type", "application/json")
           json.NewEncoder(w).Encode(map[string]string{
               "message": "Hello From Go",
           })
       })

       http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
           fmt.Fprint(w, "OK")
       })

       fmt.Println("서버가 8000번 Port에서 시작되어 대기 중이다.")

       if err := http.ListenAndServe(":8000", nil); err != nil {
           panic(err)
       }
   }
   ```

3. Application을 실행하고 응답을 확인한다.

   ```bash
   go run main.go
   ```

   ```bash
   curl http://localhost:8000
   curl http://localhost:8000/health
   ```

### Dockerfile

```dockerfile
FROM golang:1.23-alpine

WORKDIR /app

COPY . .

RUN go mod download
RUN go build -o main .

EXPOSE 8000

CMD ["./main"]
```

Build 단계에서는 다음 작업을 수행한다.

- `go mod download`로 `go.mod`에 정의된 의존성을 내려받는다.

- `go build -o main .`으로 Source Code를 `main` 실행 File로 Compile한다.

- Container가 시작되면 Compile된 `main`을 실행한다.

### Image Build와 Container 실행

```bash
docker build -t goapp .
docker container run \
  --name goapp \
  -d \
  -p 8000:8000 \
  goapp
```

```bash
curl http://localhost:8000
curl http://localhost:8000/health
```

이 예제는 Build 도구와 실행 File을 하나의 Image에 함께 두는 단일 Stage Build이다.

## 7 ) 압축된 Web Source로 Apache Image 생성

---

`ADD`는 Local Tar Archive를 Image에 추가할 때 압축을 자동으로 해제할 수 있다. 이 기능을 이용해 `webapp.tar.gz`의 Web Source를 Apache Document Root에 배치한다.

### Source Code 준비

```bash
git clone https://github.com/brayanlee/webapp.git
cd webapp
ls
```

Build Context에 `webapp.tar.gz`가 있는지 확인한다.

### Dockerfile

```dockerfile
FROM ubuntu:20.04

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends apache2 && \
    rm -rf /var/lib/apt/lists/*

ADD webapp.tar.gz /var/www/html/

WORKDIR /var/www/html

EXPOSE 80

CMD ["/usr/sbin/apachectl", "-D", "FOREGROUND"]
```

`ADD webapp.tar.gz /var/www/html/`은 Archive의 내용을 해당 Directory에 자동으로 압축 해제한다. 자동 압축 해제가 필요하지 않은 일반 File과 Directory는 동작이 더 명확한 `COPY`를 사용한다.

### Image Build와 Container 실행

```bash
docker build -t webapp .
docker container run \
  --name webapp \
  -d \
  -p 8000:80 \
  webapp
```

```bash
curl http://localhost:8000
```

## 8 ) 애플리케이션별 Build 방식 비교

---

애플리케이션 Image를 구성할 때는 다음 세 가지를 구분해야 한다.

1. 의존성을 어떤 File로 재현할 것인지 결정한다.

2. Source Code와 Build 산출물 중 무엇을 Image에 복사할지 결정한다.

3. Container가 시작될 때 실행할 하나의 주 Process를 지정한다.

| 구분 | Django·FastAPI | Node.js | Spring Boot | Go |
|---|---|---|---|---|
| 의존성 정의 | `requirements.txt` | `package.json` | Gradle 설정 | `go.mod` |
| Build 시 Package 처리 | `pip install` | `npm install` | Host에서 Gradle Build | `go mod download` |
| Image에 포함하는 주요 대상 | Python Source Code | JavaScript Source Code | JAR | Source Code와 실행 Binary |
| 실행 방식 | Python Runtime | Node.js Runtime | JVM에서 JAR 실행 | Native Binary 실행 |
| Cache 활용 지점 | 의존성 File 우선 복사 | Package File 우선 복사 | JAR 변경 시 복사 | 의존성 다운로드와 Compile |

> **최종 정리**
>
> - 애플리케이션을 먼저 Host에서 실행하여 Source Code 자체의 동작을 확인한 뒤 Image를 Build한다.
>
> - 의존성 File을 Source Code보다 먼저 복사하면 Package 설치 Layer의 Build Cache를 활용할 수 있다.
>
> - `.dockerignore`로 Host의 가상 환경, Package Directory, Cache와 환경 변수 File을 제외한다.
>
> - Python과 Node.js는 Source Code를 Runtime으로 실행하고, Spring Boot와 Go는 Build 또는 Compile 결과를 실행한다.
>
> - `CMD`와 `ENTRYPOINT`에는 Container가 시작될 때 실행할 주 Process를 지정한다.
>
> - Local Tar Archive의 자동 압축 해제가 필요한 경우 `ADD`를 사용하고 일반 복사에는 `COPY`를 사용한다.
