---
title: 프로그래밍 언어 설치
description: Linux에서 C, Java, Python, Node.js, Go 언어 설치 환경 설정 정리
date: 2026-07-24
series: Linux
tags:
  - Linux
  - AutoEverSW
---

## 1 ) C Programming
---
### GCC 컴파일러 제공
- `sudo apt install gcc -y`
- `vim helloc.c`로 파일 생성 후 작성
```c
#include <stdio.h>
int main(){
	printf("Hello C Programming\n");
	return 0;
}
```

### GCC
- **Compile**
	- `gcc -o helloClang helloc.c`
- **Run**
	- `export PATH=$PATH:/home/{userName}/programming` 
		→ 빠른 실행을 위한 Path 추가 → `helloClang`
	- `./helloClang`

### Make
- 실제 패키지는 많은 파일로 구성됨
- gcc로 일일이 컴파일하지 않고 간단하게 해결할 수 있도록 함
- `makefile(Makefile)`에 설정된 정보 읽어 여러 소스 파일을 컴파일, 링크하여 최종 실행 파일을 만듦
- 많은 오픈소스 소프트웨어는 코드와 함께 makefile을 배포함
- **`Install Make`**
	- `sudo apt install make -y`
	- `make -V`

### **Practice** 

→ `[one.c, two.c]`

```c
#include <stdio.h>

extern int two();

int main() {
	printf("Go to Module Two----\n");
	two();
	printf("End of Module one.\n");
}
```

```c
#include <stdio.h>
int two() {
	printf("In Module Two --\n");
	printf("This is a Module Two\n");
	printf("End ofModule Two.\n");
}
```

→ **`[one.o]`**
```Makefile
TARGET=one
OBJECTS=one.o two.o
%{TARGET} : ${OBJECTS}
	gcc -o %{TARGET} ${OBJECTS}
	
one.o : one.c
	gcc -c one.c
two.o : two.c
	gcc -c two.c
```

### Run
```bash
make
```


## 2 ) Java Programming
---
### 설치 확인
- 개발 도구 확인(JDK) → `javac -version`
- 실행 환경 확인(JRE) → `java -version`

```bash
sudo apt update
sudo apt install openjdk-21-jdk # OpenJDK 21
javac -version
```

```java
// HelloJava.java                          
public class HelloJava{
        public static void main(String[] args){
                System.out.println("Hello Java");
        }
}
```

```bash
javac HelloJava.java
	→ HelloJava.class
```

```bash
java HelloJava
```

- Java는 배포 시 jar 파일을 배포
- 실행 시 java가 설치되어 있어야 함
```js
kkr010128@ubuntu:~/programming/makePractice$ cd java
kkr010128@ubuntu:~/programming/makePractice/java$ jar cf app.jar *class
kkr010128@ubuntu:~/programming/makePractice/java$ ls
HelloJava.class  HelloJava.java  app.jar
```
- Linux에 java를 설치하여 베이스 이미지를 만드는 방법과 이미 설치된 베이스 이용하는 방법 존재

## 3 ) Python Programming
---
### Installation
- `python3 --version`
- `sudo apt-get upgrade python3` → python 업그레이드
- `sudo apt install python3-venv` → venv 모듈 설치

### Programming
```bash
mkdir python && cd python
python3 -m venv myenv
source myenv/bin/activate
```

```python
#  학생 성적 리스트
scores = [85, 92, 78, 90, 88]

# 80점 이상인 성적만 필터링 (List comprehension)
high_scores = [s for s in scores if s >= 80]

# 평균 계산
average = sum(score) / len(scores)
print(f" 고득점 리스트: {high_scores}")
print(f" 전체 평균: {average:.2f}")
```
### Run Python
- `python3 main.py`
### Freeze pip
- 배포를 위해 사용된 패키지를 txt로 내보냄
	- `pip freeze > requirements.txt`
- `requirements.txt`와 `main.py`를 배포
### Production → Install Package
- `pip3 install requirements.txt`
- `python3 main.py`

## 4 ) Node.js Programming
---
### Installation
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

source ~/.bashrc

nvm install --lts

```
### Check Installation
- `node -v`
- `npm -v`

### Programming
```bash
mkdir node && cd node

# 프로젝트 생성
npm init -y
```

```js
// app.js

const http = require('http');
const hostname = '127.0.0.1';
const port = 3000;

const server = http.createServer((req, res) => {
	res.statusCode = 200;
	res.setHeader('Content-Type', 'text/plain; charset=utf-8');
	res.end('Ubuntu node.js Web Server\n');
});

server.listen(port, hostname, () => {
	console.log('Listening Server');
});
```

### Run
- `node app.js`
- 배포 시 node는 package.json과 소스코드를 배포
- node는 기존에 설치가 돼있어야 함
- npm install을 통한 라이브러리 설치 후 실행
- python과 node가 배포 방법이 유사

## 6 ) Go Programming
---
### Installation
- `sudo rm -rf /usr/local/go` → 기존 설치된 go 삭제


```bash
# download Go
curl -OL https://golang.org/dl/go1.22.0.linux-arm64.tar.gz

# unzip
sudo tar -C /usr/local -xzf go1.22.0.linux-arm64.tar.gz

# Add to Path
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.profile
echo 'export PATH=$PATH:$(go env GOPATH)/bin' >> ~/.profile

# Save Changes
source ~/.profile

# Check Installation
go version
```


### Programming
```bash
go mod init hello-go
```

```go
// main.go
package main

import "fmt"
func main() {
	fmt.Println("Hi, Welcome to Go-Lang World!")
	
	// 간단한 산술 연산 예제
	a := 10
	b := 20
	sum := a + b
	fmt.Print("%d + %d = %d\n", a, b, sum)
}
```

### Run
- `go run main.go`