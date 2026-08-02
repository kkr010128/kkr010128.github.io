---
title: 사용자 관리
description: Linux 사용자/그룹 계정 관리, 사용자 정보, 디스크 사용량 설정 정리
date: 2026-07-24
series: Linux
tags:
  - Linux
  - AutoEverSW
---

## 1 ) 사용자 계정 관리 파일
---
### `/etc/passwd`
- 사용자 계정 정보가 저장된 기본 파일
- 초창기 유닉스에서는 비밀번호도 해당 파일에 저장
	- but 해킹 위험 증가에 따라 암호는 `/etc/shadow`에 별도 저장
- root 계정으로 직접 수정 가능
	- 명령어 수정 권장
- 구조
	- `{userName}:x:1000:1000:Ubuntu:/home/{userName}:/bin/bash`

### `/etc/shadow`
- 비밀번호 관리를 위한 파일
- 해시를 이용해 저장
- 이전에는 `SHA-512`방식 → 지금은 `yescrypt`방식으로 보안성 강화
- 단방향 해시
	- 원래 데이터와 비교해 일치 여부 판단
	- 원본 데이터 복원 불가
- `.`을 기준으로 
	- 1번 항목 항목은 로그인 ID
	- 2번 항목 항목은 비밀번호
	- 3번 항목: 은 최종 변경일(1970.01.01 이후 지난 시간)
	- 4번 항목: 암호를 사용할 수 있는 최소 기간
		- 3이라면 암호 변경 후 최소 3일은 사용해야 함
	- 5번 항목: 암호를 사용할 수 있는 최대 기간
		- 기간이 지나면 암호를 변경해야 함
	- 6번 항목: 만료가 되기 n일 전부터 경고 메시지 보냄
	- 7번 항목: 만료 후 며칠 동안 로그인 가능하도록 할지 설정
	- 8번 항목: 해당 날짜가 지나면 로그인을 할 수 없도록 함(1970.01.01)
	- 9번 항목: 미래를 위한 값
	- 4~8 항목을 aging 정보라고 함

### `/etc/login.defs`
- 사용자 계정의 설정과 관련된 기본값을 정의한 파일
###  `/etc/group`
- 그룹에 대한 정보
- `{groupName}:x"4"{member1},{member2}`
- 그룹 이름 → {groupName}
- 비밀번호 → `x`
- 그룹아이디 → `4`
- 그룹의 멤버 → `member`
- 그룹의 비밀번호는 `/etc/gshadow` 파일에 존재

## 2) 계정 관리 명령
---
### useradd
- 사용자 생성 명령
- 형식: `useradd [옵션] [로그인ID]`

- **옵션**
    - `u uid`: UID 설정
    - `o`: UID 중복 허용
    - `g gid`: 기본 그룹 설정
    - `G gid`: 2차 그룹 설정
    - `d 디렉토리이름`: 홈 디렉토리 변경
    - `s 셸`: 로그인 쉘 변경
    - `c 설명`: 계정 설명
    - `D`: 기본값 설정 또는 출력
    - `e 유효기간`: EXPIRE 항목 설정 (YYYY-MM-DD)
    - `f 비활성일수`: 비활성 일수
    - `k 디렉토리`: 계정 생성 시 복사할 초기 파일/디렉토리 설정

```sh
# 옵션 없이 계정 생성
sudo useradd user2

# 비밀번호 설정
sudo passwd user2

# 옵션 이용 생성
sudo useradd -d /home/user3 -u 2000 -g 1000 -G 3 user3
```

### adduser
- 사용자 계정 생성 명령 (대화형)
- 형식: `adduser [옵션] 로그인ID`

- **옵션**
    - `uid UID`
    - `gid GID`
    - `home 홈디렉토리`
    - `shell 쉘`
    - `gecos 설명`

- 계정 생성 시 **암호 입력**을 요청함

### usermod
- 계정 정보 수정 명령
- 형식: `usermod [옵션] [로그인ID]`

- **옵션**
    - `u UID`: UID 변경
    - `g GID`: 기본 그룹 변경
    - `o`: UID 중복 허용
    - `G GID`: 2차 그룹 변경
    - `d 디렉토리이름`: 홈 디렉토리 변경
    - `s 쉘`: 로그인 쉘 변경
    - `c 설명`: 설명 변경
    - `f inactive`: 비활성 일수
    - `e expire`: 만료일 설정
    - `l`: 계정 이름 변경

### 패스워드 에이징 (Password Aging)
- `useradd`, `usermod`, `passwd`, `chage` 명령으로 설정
- `chage` 명령이 패스워드 에이징을 관리하는 별도의 명령

| 항목 | useradd/usermod/passwd | chage 명령 |
|------|----------------------|------------|
| **MIN** | `passwd -n 날수` | `chage -m` |
| **MAX** | `passwd -x 날수` | `chage -M` |
| **WARNING** | `passwd -w 날수` | `chage -W` |
| **INACTIVE** | `useradd -f 날수`, `usermod -f 날수` | `chage -I` |
| **EXPIRE** | `useradd -e 날짜`, `usermod -e 날짜` | `chage -E` |

```sh
# passwd 명령으로 기본값 설정
sudo passwd -n 3 -x 100 -w 5 user3

# chage 명령으로 설정
sudo chage -m 3 -M 100 -W 5 -E 2026-08-01 user5
```

## 3) 그룹 관리 명령
---
- **groupadd**: 그룹 생성
- **addgroup**: 그룹 생성
- **groupmod**: 그룹 정보 수정
- **groupdel**: 그룹 삭제
- **gpasswd**: 그룹 암호 설정

## 4) 사용자 정보 관리
---
### UID와 EUID
- **UID** (= RUID): 사용자가 로그인할 때 사용하는 ID
- **EUID**: 현재 명령을 수행하는 주체의 UID
- UID와 EUID가 달라지는 경우
    1. 실행 파일에 **setuid**가 설정된 경우
        - 해당 파일을 실행한 프로세스의 UID가 사용자 계정의 UID가 아닌 실행 파일 소유자의 UID가 됨
    2. `su` 명령을 사용해 다른 계정으로 전환한 경우

### 사용자 확인 명령

| 명령 | 설명 |
|------|------|
| **who** | 로그인 정보 확인 |
| **w [사용자계정]** | 사용자 정보 + 현재 실행 중인 작업 정보 |
| **last** | 사용자 계정, 로그인/로그아웃 시간, 터미널 번호, IP 주소 출력 |
| **whoami** | 현재 UID 확인 |
| **who am i** | 현재 EUID 확인 |
| **id** | UID와 EUID 확인 |

### root 권한 사용

- `su` 명령으로 root 계정 전환
    - *하지만* 보안상 매우 위험

#### sudo 명령
- 일반 사용자에게 특정 시스템 관리 작업만 수행할 수 있는 **제한적 권한 부여**
- 권한은 `/etc/sudoers` 파일에 설정
    - root 계정으로만 수정 가능
    - 일반적으로 `visudo` 명령으로 수정 권장 (문법 검증 후 저장)

```sh
# 현재 설정 내용
root ALL=(ALL) ALL

# 권한 부여 형식
유저 ALL=명령 나열

# 예시: user2에게 useradd, usermod 권한 부여
user2 ALL=/usr/sbin/useradd, /usr/sbin/usermod

# 명령은 절대 경로로 설정, 여러 개는 쉼표로 구분
```

- **sudo 명령 사용**: `sudo 명령`
- *하지만* 일반 사용자에게 모든 권한을 부여하는 것은 매우 위험

### 파일 및 디렉토리 소유자/소유 그룹 변경

#### chown (소유자 변경)
- 형식: `chown [옵션] [사용자계정] [파일/디렉토리경로]`
- 인터넷에서 다운로드한 파일의 소유자 변경 시 사용

```sh
# 실습
mkdir linux_ex
cd linux_ex
mkdir usermanagement
cd usermanagement
cp /etc/hosts .
```

#### chgrp (소유 그룹 변경)

## 5) 디스크 사용량 설정 (Quota)
---
### 개요
- 리눅스는 여러 사용자가 함께 사용하는 시스템이므로 특정 사용자의 과도한 디스크 사용을 제한할 필요가 있음
- 제한 방법
    - 디스크 크기 제한
    - 파일 개수 제한
- 제한 유형
    - **Hard Limit**: 절대로 넘어설 수 없는 최대치
    - **Soft Limit**: 일정 시간 내에서는 넘을 수 있는 한계치
- 할당된 쿼터 초과 시 사용자는 파일을 지우거나 관리자에게 용량 추가 요청
- 우분투에서는 `quota` 패키지 이용

### 쿼터 설정 준비

1. 쿼터 속성 설정 → `/etc/fstab`

| 파티션         | 마운트된 디렉토리 | 파일시스템  | 마운트 옵션              | Dump | Pass |
| ----------- | --------- | ------ | ------------------- | ---- | ---- |
| `/dev/sdb1` | `/mnt`    | `ext4` | `defaults,usrquota` | `1`  | `1`  |

```fstab
/dev/sdb1    /mnt    ext4    defaults,usrquota    1    1
```
2. 쿼터 속성 적용
```sh
sudo mount -o remount /mnt
sudo systemctl daemon-reload
mount
```

3. 데이터베이스 생성
```sh
sudo quotacheck -ugvm /mnt
```

4. 쿼터 사용 활성화
```sh
sudo quotaon -uv /mnt
```

### 쿼터 설정

```sh
edquota [옵션] [사용자계정]
sudo edquota -u user1
```

- 클라우드 서비스 중 **메일이나 디스크 관련 서비스**에서 이 기능을 많이 사용
