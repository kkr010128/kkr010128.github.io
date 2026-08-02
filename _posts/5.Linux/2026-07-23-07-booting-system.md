---
title: 부팅 시스템
description: Linux 부팅 과정, systemd 서비스, Namespaces, Cgroup 정리
date: 2026-07-23
series: Linux
tags:
  - Linux
  - AutoEverSW
---

## 1 ) 부팅 메뉴 출력
---
### `etc/default/grub`
- 해당 파일에서 `GRUB_TIMEOUT_STYLE=hidden`을 주석처리 

## 2 ) 모든 프로세스 출력
---
`ps -ef | more`











### systemd unit
- 전체 시스템을 싲가하고 관리하는데 유닛이라 부르는 구성 요소를 사용
- 관리 대상의 이름을 `서비스명.유닛종류`로 관리
- 부를 때는 유닛 종류를 생략하는 것이 일반적
- 유닛 종류
- service: 시스템 서비스 유닛으로 데몬을 시작, 종료, 재시작, 로드
- target: 유닛을 그룹화
- automount: 디렉토리 계층 구조에서 자동 마운트 포인트를 관리
- device: 리눅스 장치 트리에 있는 장치 관리
- mount: 디렉토리 계층 구조의 포인트 관리
- path
- scope: 외부에서 생성된 프로세스 관리
- slice: 시스템의 프로세스를 계층적으로 관리
- socket: 네트워크 통신을 위한 SW(랜카드)
- swap: 스왑 장치 관리
- timer

### systemctl
- `systemctl [opt] [cmd] [unitName]`
	- Option
		- 상태와 관계 없이 유닛 전체 출력 → `a`
		- 유닛 종류에 해당하는 것만 출력 → t
	- Cmd
		- start → 시작
		- stop → 중지
		- reload → 설정 파일 다시 읽어오기
		- restart → 재시작
		- status → 상태 확인
		- enable → 부팅하자마자 서비스 실행
		- disable → 부팅 시 시작 해제
		- is-active → 시작되었는지 확인
		- is-enabled → enable 여부
		- isolate → 지정한 유닛만 시작, 나머지는 정지
		- kill → 유닛에 시그널 전송


### cron 서비스 실습

```sh
# cron 서비스 시작
sudo systemctl start cron

# colord.service 동작 중인지 확인

# 동작 중이면 중지 → 시작

# PID 확인
```


### init 프로세스
- init 프로세스가 다른 프로세스들을 실행
- init 프로세스의 스크립트 디렉토리 → `/etc/init.d`

## 3) RUN Level
---
- 현재 시스템의 상태를 나타내는 **한 자리 숫자**

| 레벨 | 상태 |
|------|------|
| **0** | Poweroff (종료) |
| **1** | Rescue 모드 (안전 모드, 텍스트 모드) |
| **2** | 다중 사용자 |
| **3** | 다중 사용자 |
| **4** | 다중 사용자 |
| **5** | GUI (그래픽 모드) |
| **6** | Reboot (재부팅) |

```sh
# RUN Level 수정
sudo systemctl set-default runlevel숫자.target
```

- 기본은 **5번** 선택 권장
- 부팅이 제대로 되지 않을 때는 **1번**으로 수정해서 확인
    - 1번으로 부팅 시 GUI가 아닌 텍스트 모드로 부팅

### 서비스 등록

1. 서비스 파일 작성 → `/etc/systemd/system/` 디렉토리에 `.service` 파일 생성

```
[Unit]
Description=설명
After=먼저 실행해야 할 서비스

[Service]
ExecStart=실제스크립트파일경로
Restart=재시작옵션(on-failure)

[Install]
WantedBy=런레벨타겟
```

2. 서비스 파일 작성 후 reload
```sh
sudo systemctl daemon-reload
```

## 4) 종료
---
### 종료 방법
- `shutdown` 명령
- `halt` 명령
- `poweroff` 명령
- RUN Level을 0으로 설정
- `reboot`
- 전원 끄기
    - *하지만* 디스크나 운영체제가 망가질 수 있으므로 사용하지 않는 것을 권장

### shutdown 명령

- 형식: `shutdown [옵션] [시간] [메시지]`
- **옵션**
    - `k`: 실제 종료 없이 사용자에게 메시지만 전달
    - `r`: 종료 후 재시작
    - `h`: 종료 후 halt 상태로 이동
    - `f`: 빠른 재시작 (디스크 검사 fsck 생략)
    - `c`: 이전 shutdown 명령 취소
- **시간**
    - `hh:mm:ss` 형식 또는 `now`
    - `+분`

### RUN Level 변경으로 종료
- RUN Level을 0으로 설정하여 종료

## 5) Namespaces & Cgroup
---
### Container
- **컨테이너 기술**: 애플리케이션을 효율적이고 독립적으로 실행할 수 있는 **경량화된 환경** 제공
- 기본적으로 애플리케이션 실행 시 운영체제 + 애플리케이션 + 라이브러리가 필요
- 컨테이너는 실행에 필요한 **최소한의 운영체제 기능**만 포함
- 컨테이너의 근간이 되는 리눅스 기술
    1. **Cgroup**
    2. **Namespaces**
    3. **Union Mount Filesystem**

### Control Group (Cgroup)
- 프로세스들이 사용하는 **시스템 자원의 사용 정보를 수집 및 제한**하는 기능
- `/sys/fs/cgroup` 디렉토리에 가상 파일로 존재

**서브 시스템**

| 서브 시스템 | 설명 |
|------------|------|
| **CPU** | CPU 사용 제한 |
| **Memory** | 메모리 사용 제한 |
| **Freezer** | Cgroup 작업을 일시 중지/재시작 |
| **blkio** | 입출력(I/O) 제한 설정 |
| **net_cls** | 네트워크 패킷 태그 작성 |
| **cpuset** | CPU를 Cgroup에 할당 |
| **cpuacct** | CPU 자원 보고서 |
| **devices** | 장치 접근 제어 |
| **ns** | 네임스페이스 |

```sh
# CPU 사용 제한 설정
# /sys/fs/cgroup 디렉토리 안에 별도 디렉토리 생성
# 생성한 디렉토리에 파일을 생성해서 작성
# 사용시간 100000 → 100ms 중 사용시간만큼 사용

# 절반 사용
50000 100000

# 전체 사용
max 100000
```

### Namespace
- 프로세스를 **격리**시키기 위한 논리적인 그룹

### Union Mount Filesystem
- 프로세스 별로 별도의 파일을 소유해서 마운트 시킨 후 사용
