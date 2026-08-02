---
title: 원격 접속
description: Linux Telnet, SSH 원격 접속 프로토콜 설치 및 설정 정리
date: 2026-07-27
series: Linux
tags:
  - Linux
  - AutoEverSW
---

## 1) Telnet
---

### 개요
- **Telnet**은 **Te**lecommunication **Net**work의 약자
- 인터넷이나 로컬 영역 네트워크 연결에 사용되는 네트워크 프로토콜
- 1969년에 처음 개발된 오래된 표준

### 특징
- **원격 접속**: CLI를 통해 원격 호스트를 제어
- **TCP 기반**: 기본적으로 **TCP 23번 포트** 사용
- **플랫폼 독립적**: 운영체제가 달라도 상관없음
- **NVT**(Network Virtual Terminal): 서로 다른 시스템 환경에서도 명령어를 인식할 수 있도록 가상의 단말기 개념을 사용

### 장점
- 설치 간편, 사용법 매우 쉬움
- 시스템 리소스 적게 차지
- 오래된 장비와도 호환성 뛰어남

### 단점
- *하지만* 데이터가 암호화되지 않은 **평문(plaintext)** 으로 전송
    → 패킷 스니핑을 통해 정보 유출 위험이 큼

### 현재 사용 용도
- **포트 개방 확인**: `telnet IP주소 포트번호`

### 설치 확인
```sh
dpkg -l | grep telnet
```
- 기본적으로 클라이언트만 설치되어 있음

## 2) SSH
---

### 개요
- **SSH**(**S**ecure **Sh**ell)는 네트워크 상의 다른 컴퓨터에 로그인하거나 원격 시스템에서 명령을 실행할 수 있는 보안 네트워크 프로토콜
- 기존 Telnet, FTP 등은 데이터를 **평문(plaintext)** 으로 전송 → 해킹에 취약
- SSH는 모든 통신 내용을 **암호화**하여 보안성 획기적으로 향상

### 특징
- **강력한 암호화**: 전송되는 모든 데이터를 암호화
- **인증**(Authentication): 접속 사용자 확인 (비밀번호 방식, 공개키 방식)
- **무결성**(Integrity): 전송 데이터의 위변조 방지
- **압축**: 데이터를 압축 전송 → 네트워크 효율 향상
- **클라이언트-서버 모델**로 동작, 표준 포트는 **22번**
- **권장 인증 방식**: 비밀번호보다 **SSH Key**(공개키/개인키) 방식

### 활용 사례
- **원격 터미널 접속**
- **SFTP/SCP**: 보안 채널을 이용한 안전한 파일 전송
- **SSH Tunneling**: 보안이 취약한 다른 프로토콜을 SSH 안에 넣어 안전하게 전달
- **Git 원격 저장소**: GitHub, GitLab 등에서 인증 수단으로 사용

### 설치 및 접속

```sh
# SSH 서버 설치
sudo apt -y install openssh-server

# 서비스 시작
sudo systemctl start ssh

# 부팅 시 자동 시작
sudo systemctl enable ssh

# 서비스 상태 확인
systemctl status ssh

# 방화벽에서 SSH 포트 허용
sudo ufw allow 22/tcp

# 외부에서 접속
ssh 사용자이름@IP주소 -p 포트번호
```
- 맨 처음 접속하면 보안 확인 메시지가 출력됨

### SSH Key를 이용한 접속

#### 클라이언트에서 키 생성

```sh
ssh-keygen -t ed25519
```
- 비밀번호 생성 창은 **Enter**로 넘어감

#### 서버에 키 등록

```sh
ssh-copy-id -p 포트번호 사용자이름@서버주소
```

#### 서버 설정

```sh
# 권한 설정
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# SSH 설정 확인 및 수정
sudo nano /etc/ssh/sshd_config
```

- `PubkeyAuthentication yes` → 주석 해제
- `AuthorizedKeysFile .ssh/authorized_keys` → 주석 해제
- `PasswordAuthentication yes` → 주석 해제

```sh
# 설정 저장 후 SSH 재시작
sudo systemctl restart ssh
```

#### 클라이언트에서 키 접속

```sh
sudo ssh -i ~/.ssh/id_ed25519 사용자이름@컴퓨터이름이나IP주소
sudo ssh -i ~/.ssh/id_ed25519 adam@192.168.0.101
```

#### 접속 간편화 (클라이언트 설정)

```sh
vi ~/.ssh/config
```

```
Host 이름
    HostName 서버IP
    User 사용자계정
    IdentityFile ~/.ssh/id_ed25519
```

저장 후 `sudo ssh 이름` 으로 접속