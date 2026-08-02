---
title: 소프트웨어 관리
description: Ubuntu 패키지 관리, apt, 압축, wget, curl 사용법 정리
date: 2026-07-22
series: Linux
tags:
  - Linux
  - AutoEverSW
---

## 1 ) Ubuntu Package
---
### 개요
- 리눅스의 소프트웨어는 소스코드 형식 또는 바로 설치해 사용 가능한 패키지 형태로 배포
- 소스 코드 형식으로 배포하는 경우
	- 하나의 아카이브 파일로 묶어 압축해 배포
- 바이너리 패키지로 배포하는 경우
	- 리눅스에서 주로 사용하는 패키지 형식인 RPM과 deb가 존재
		- ubuntu → deb (RPM 패키지 설치가 가능하긴 하나 별도의 작업 필요)
			- 16.04 이상부터 새로운 패키지(snap)형식이 추가됨
				→ 기존 패키지의 의존성 문제를 해결함 (deb과 호환됨)
		- redhat → RPM
### 특징
- 바이너리 파일로 구성되어 있어 별도의 컴파일 필요 없음
- package 내 파일이 관련 디렉토리에 바로 설치됨
- 삭제 시 관련 파일 일괄 삭제 가능
- 기존 설치한 패키지 삭제 없이 업그레이드 가능
- 설치 상태 검증 가능
- 의존성이 존재하는 패키지도 자동 설치
### 카테고리
- main 
	→  공식적으로 지원되고 자유롭게 배포 가능
- restricted
	→  지원은 하나, 자유 라이선스 소프트웨어는 아님
- universe
	→  자유 소프트웨어일 여부가 불분명하며 기술적 지원을 보장하지 않음
- multibus
	→ 개인이 직접 라이센스 확인 필요
### 패키지 저장소
- 우분투는 패키지와 패키지에 대한 정보를 저장하고 있는 서버인 패키지 저장소 개념 도입
- 패키지 저장소는 패키지의 기능 추가나 보안 패치 등 지속적 업그레이드를 집중적으로 관리
- 사용자는 저장소에 접속해 최신 패키지를 내려받아 설치
- 패키지 저장소를 이용하기 위해선 패키지 저장소를 설정해야 함

```bash
# 해당 파일에 패키지 저장소 설정
sudo ls -l /etc/apt/sources.list.d/ubuntu.sources
```


## 2 ) Package Management
---
### apt-cache
- apt cache에 질의해 여러가지 정보 검색
### apt-get | apt
- 명령 형식
	- `apt [option] 서브명령`
		- 패키지 내려받기만 수행 → `-d`
		- 의존성이 깨진 패키지 수정 시도 → `-f`
		- 도움말 → `-h`
		- 설치나 업그레이드 시 설치 여부 확인 부분을 생략 → `-y`
			- IaC(Infrastructure as Code) 시 에는 반드시 사용
			- 절대적으로 사람의 개입이 없어야 함
	- 서브 명령
		- 패키지 저장소에서 새로운 패키지 정보 가져옴 → `update`
		- 현재 설치된 패키지 업그레이드 → `upgrade`
		- 패키지 설치 → `install {packageName}`

		- 패키지 삭제 → `remove {packageName}`
		- 패키지 삭제(설정파일까지) → `purge {packageName}`
		- 패키지 다운로드 → `download {packageName}`
		- 불완전하게 내려받았거나 오래된 패키지 삭제 → `autoclean`
		- 캐시된 모든 패키지를 삭제해 디스크 공간 확보 → `clean`
		- 자동으로 설치되었지만 더 이상 필요 없는 패키지 삭제 → `autoremove`
		- 의존성 깨진 패키지 확인 → `check`
### update
- 저장소 정보로 패키지 정보를 다시 읽어와 동기화
- 저장소를 추가하면 수행
- docker에서 이미지를 만들 때 linux를 기본 이미지로 선택한 경우
	→ 반드시 수행하여 패키지 정보를 업데이트 하도록 해야 함
### upgrade
- 기존에 설치된 패키지들을 업그레이드
### install
- 패키지를 설치
- xterm 패키지 설치
## 삭제
- remove → 설정 파일 제외 삭제
- purge → 설정 파일 함께 삭제
- autoremove → 자동 정리 및 삭제
- clean → 공간 정리
### 다운로드
- download → 패키지를 파일로 다운로드만 실행
- source → 특정 패키지의 소스코드만 다운로드할 때 사용
	- `sudo apt --download-only source {packageName}`
	- `sudo apt source {packageName}` → 다운로드 후 압축 해제
	- `sudo apt --complie source {packageName}` → 다운로드 후 압축 해제 및 컴파일

### 외부 저장소 이용
→ docker 설치
- https://docs.docker.com/engine/install/ubuntu
1. 패키지 정보 업데이트 → `sudo apt-get update`
2. 인증서 관련 패키지 설치
3. Docker의 공식 GPG키 추가: 
4. Docker의 공식 apt 저장소 추가
5. 시스템 패키지 업데이트
	→ sudo apt-get update u
6. Docker 설치
	→ sudo apt-get install docker-ce docker-ce-cli containerd.io u 
7. 도커 실행상태 확인: sudo systemctl status docker u
8. 도커 실행: sudo docker run hello-world

### dpkg 명령으로 패키지 관리
- `apt` 명령은 fedora의 `yum` 또는 `dnf` 명령과 비슷함
- fedora의 `rpm과` 유사 명령이 `dkpg`
- `apt도` 내부적으로는 dpkg 사용
- 패키지 설치는 일반적으로 apt를 이용하나, 시스템의 특정 파일이 어느 패키지에 속했는지를 확인하는 등 세부적인 기능을 사용할 때 이용

- `dpkg [opt] {fileName | packageName}`
	- `[opt]`
		- 패키지 목록 출력 → `l`
		- 상세 정보 출력 → `s`
		- 파일의 목록 출력 → `L`
		- 설치 → `i`
		- 삭제 → `r`

#### dpkg 명령 사용 예시

```sh
# 패키지 목록 출력
dpkg -l

# 특정 패키지 상세 정보 출력
dpkg -s 패키지이름

# 특정 패키지가 설치한 파일 목록 출력
dpkg -L 패키지이름

# 패키지 설치
sudo dpkg -i 패키지파일.deb

# 패키지 삭제
sudo dpkg -r 패키지이름
```

### aptitude
- 옵션이나 서브 명령 없이 사용하면 curses를 이용한 visual mode로 동작
- `sudo apt install aptitude -y`
- `sudo aptitude`

### snap
- 우분투가 새로 도입한 패키지 형식
- 샌드박스 형태의 패키지
- 패키지를 만들 때 필요한 모든 라이브러리를 패키지 안에 포함하는 방식
- 외부 파일이 내부 시스템에 악영향을 주는 것을 방지하는
- 단점은 패키지의 용량이 커짐


### snap 명령어

- 형식: `snap [옵션] 명령`

| 명령             | 설명        |
| -------------- | --------- |
| `disable`      | 스냅 비활성화   |
| `download`     | 스냅 다운로드   |
| `enable`       | 스냅 활성화    |
| `find 스냅이름`    | 스냅 검색     |
| `info 스냅이름`    | 스냅 정보 확인  |
| `install 스냅이름` | 스냅 설치     |
| `list`         | 설치된 스냅 목록 |
| `remove 스냅이름`  | 스냅 제거     |



## 3 ) 압축
---
### tar(tape archive)
- 여러 개의 파일이나 디렉토리를 하나의 파일로 묶는 것
- `tar {fnc} [opt] [archiveFile] [fileName]`
	- **Function**
		- 새로운 압축파일 생성 → `c`
		- 압축 파일의 내용 출력 → `t`
		- 압축 해제 → `x`
		- 새로운 파일 추가 → `r`
		- 수정된 파일 업데이트 → `u`
		- 
	- **Option**
		- 아카이브 파일 또는 테이프 장치 지정 → `f`
		- 처리하고 있는 파일의 정보 출력 → `v`
		- 심볼릭 링크의 원본 파일 포함 → `h`
		- 파일 복구 시 원래의 접근 권한 유지 → `p`
		- bzip2로 압축 또는 해제 → `j`
		- gzip으로 압축 또는 해제 → `z`
	- 자주 쓰는 옵션
		- 아카이브 생성 → `cvf`
		- 아카이브 압축 해제 → `cvf`
		- 아카이브 내용 확인 → `tvf`
		- 아카이브 업데이트 → `uvf`
		- 아카이브에 파일 추가 → `rvf`

- 실습

```bash
# 디렉토리 생성
mkdir ex_archive

# 디렉토리 이동
cd ex_archive

# 디렉토리 생성
mkdir sample1 sample2 sample3

# sample1 디렉토리를 압축
tar cvf sample1.tar smaple1

# 압축한 내용 확인
tar tvf sample1.tar

# sample1 디렉토리 삭제
rmdir sample1

# 압축 해제
tar xvf sample1.tar

# 파일 생성
touch sample1/data

# 압축된 파일 업데이트
tar uvf sample1.tar sample1

# 파일 생성
touch service

# 이미 압축된 파일에 추가
tar rvf sample1.tar service

# 아카이브 생성과 함께 압축
tar czvf sample1.tar.gz sample1
tar czvf sample1.tar.bz2 sample1
```

- 아카이브 생성과 함께 압축
	- gzip으로 압축하고자 하는 경우 z 옵션 이용
	- 일반적으로 압축된 사실을 알려주기 위해 마지막에 확장자 gz를 추가함
	- `tar czvf sample1.tar.gz sample1`

### gzip / gunzip
- 압축률이 좋은 유틸
- `gzip [opt] [fileName]`
- **Option**
	- 압축 해제 → `d`
	- 압축 파일의 정보 출력→ `l`
	- 하위 디렉토리 탐색해 압축 → `r`
	- 압축 파일 검사 → `t`
	- 압축 정보 출력 → `v`
	- 최대한 압축 → `9`

- 압축된 파일 내용 조회
	- `zcat sample1.tar.gz | more`
- 압축 해제
	- `gunzip sample1.tar.gz`
	- 해제 시 압축된 파일이 사라지면서 해제 됨

### bzip2 / bunzip2
- gzip에 비해 압축률이 놓으나 속도가 느림
- 압축 시 원본 파일 사라짐
- 
- xz, zip도 지원

## 4 ) wget
- 웹 상의 파일을 다운 받을 때 사용
- `wget [opt] [url]`
	- **Option**
		- 일반 다운로드 → `wget {url}`
		- 다른 이름으로 저장 → `wget -O {fileName} {url}`
		- 이어서 받기 → `wget -c {url}`
		- 백그라운드에서 다운로드 → `wget -b {url}`
		- 속도 제한 다운로드 → `wget --limit-rate={speed} {url}`
### 웹 사이트 미러링
- `wget -m {url}`
- 하위 디렉토리를 따라가며 다운로드 → `-r`
- 상위 디렉토리로 이동하지 않도록 제한 → `-np`
- 로컬에서 오프라인으로 보기 편하도록 링크를 반환 → `-k`

## 5 ) curl
- 서버와의 데이터 통신 및 API 테스트에 최적화되어 있어 개발자들이 선호
### 웹 페이지 소스 보기 
- `curl {url}`
### 파일로 저장
- 동일한 이름으로 저장
	- `curl -O {filePath}`
- 이름 변경
	- `curl -o {fileName} {filePath}`
### 헤더 확인
- `curl l {url}`
### Redirect 자동 추적
- `curl -L {url}`
### API 테스트 시 사용하는 옵션
- HTTP 메서드 설정 → `-X`
- 전송할 데이터 생성 → `-d`
- 헤더 정보 설정 → `-H`
### 자주 사용하는 옵션 → fsSL
- 오류가 발생하는 경우 실패 처리 → `f`
- 에러 메시지 표시 하지 않음 → `s`
- 진짜 에러인 경우만 출력 → `S`
- 리다이렉트 되는 경우 자동으로 새로운 주소에서 데이터 받아옴 → `L`
	- 다운로드 받아서 설치할 때 주로 이용
	- `curl -fsSL https://install.direct/go.sh | sudo bash`
