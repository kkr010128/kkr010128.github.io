---
title: 네트워크 관리
description: Linux 네트워크 기본 개념, 설정, 상태 확인, 방화벽 정리
date: 2026-07-24
series: Linux
tags:
  - Linux
  - AutoEver SW School
---

## 1) 네트워크 기본 개념
---
### TCP/IP 프로토콜
- **프로토콜**: 통신을 하기 위한 규칙 또는 규약
- **TCP/IP**: 인터넷이라는 통신망의 프로토콜

### 주소

#### MAC Address
- **Media Access Control**의 약자
- 하드웨어를 위한 주소로, 이더넷 주소/하드웨어 주소/물리 주소라고도 불림
- **NIC**(Network Interface Card)에 저장된 주소
- 하드웨어 제조 과정에서 부여되며 원칙적으로는 수정 불가
    - *하지만* 운영체제에 따라 수정 가능
- `:` 또는 `-`로 구분되는 6개의 16진수로 구성 → 총 **48bit**
    - `00:50:56:3e:3c:fe` 형태
    - 앞의 3개 → **제조사 번호**
    - 뒤의 3개 → **일련번호**

#### IP Address
- 인터넷 주소 체계
- 현재는 **IPv4**와 **IPv6**만 사용

**IPv4**
- 32비트 주소 체계
- 8비트씩 끊어 10진수로 표현, 구분은 `.`
- 0~255까지의 숫자 4개로 표현
- 현재는 주소가 고갈되어 IPv6 사용

**IPv6**
- 128비트 주소 체계
- 16진수 2개씩 묶어 표현
- 구분은 `:`

#### NetMask
- IP 주소에서 **네트워크 부분**을 알려주는 역할
- 동일한 네트워크를 나타내기 위해 사용
    - 내부 통신이 가능한 영역을 표현
- IP처럼 10진수 4자리 또는 1의 개수로 표현
    - `192.168.0.2 255.255.255.0` 또는 `192.168.0.2/24` 형태
    - `255.255.255.0` → `11111111.11111111.11111111.00000000`
    - 1의 개수가 24개 → `/24`
    - 1의 개수 24자리까지 동일하면 **동일한 네트워크**로 간주
    - `192.168.0`까지 동일하면 동일 네트워크 → 외부 라우터 없이 내부 처리

#### Broadcast Address
- 동일 네트워크의 모든 컴퓨터에 메시지를 보낼 때 사용하는 주소
- 일반적으로 네트워크 대역에서 **가장 마지막 주소** 사용
    - `192.168.0.2 255.255.255.0` → `192.168.0.255`

#### 호스트 이름
- IP 주소 대신 사용할 수 있는 컴퓨터 이름
- **도메인**: 인터넷에서 사용하는 호스트 이름
    - `www.naver.com` → `naver.com`은 네트워크 부분, `www`는 호스트 부분

#### DNS (Domain Name Service)
- 도메인을 해석해 **IP로 변환**해주는 시스템
- 도메인 입력 → DNS가 해석 → IP로 변환 → 해당 컴퓨터로 접속
- IP를 직접 사용하면 도메인보다 속도가 빠름

#### DHCP (Dynamic Host Configuration Protocol)
- **IP 주소 관리 자동화**를 위한 네트워크 프로토콜
- 네트워크에 연결되는 장비는 IP주소, 넷마스크, 기본 게이트웨이, DNS Server 주소를 설정해야 인터넷 사용 가능
- DHCP 서버가 장비의 요청을 받아 할당 가능한 주소를 찾아 **대여**

#### Gateway
- 로컬 네트워크는 내부 컴퓨터 정보만 알 수 있음
- **외부 네트워크**로 나가기 위해 거쳐야 하는 장비(라우터)
- 인터넷 사용 시 Gateway를 통해 요청
- 보통 사용 가능한 네트워크 주소 대역에서 **첫 번째 주소** 사용
    - `192.168.0.2/24` → `192.168.0.1` (또는 마지막 주소 `192.168.0.254` 사용)

#### 포트 번호
- 컴퓨터 내부에서 통신 가능한 **애플리케이션**을 구분하기 위한 번호
- **0~65535**까지 사용 가능
- **0-1023번**: 국제 표준으로 합의된 잘 알려진 포트(Well-known port)
    - `cat /etc/services`에서 확인 가능

### 인터넷 사용을 위해 설정해야 할 주소
1. **IP Address**
2. **Subnet Mask**
3. **Gateway Address**
4. **DNS Address**

## 2) 네트워크 설정
---
### ip 명령으로 주소 관리
- 형식: `ip [옵션] 객체 [서브 명령]`

- **옵션**
    - `V`: 버전 출력
    - `s`: 자세한 정보 출력

- **객체와 서브 명령**
    - `address [add | del | show | help]`: **IP 주소 관리**
    - `route [add | del | help]`: **라우팅 테이블 관리**
    - `link [set]`: 네트워크 인터페이스 **활성화/비활성화**

```sh
# 전체 장치에 대한 상세 정보 출력
ip addr show

# 하나의 인터페이스에 대한 정보 출력
ip addr show enp0s3

# IP 추가 설정
sudo ip addr add 192.168.1.20/24 dev enp0s3
```

- *하지만* `ip` 명령은 **재부팅 시 사라지므로** 별도의 설정 파일에 저장해야 영구 적용됨

#### 라우팅 테이블과 게이트웨이
- **라우팅**: 최적의 경로를 찾아가는 것
- **라우팅 테이블**: 경로 정보를 저장해 놓은 테이블
    - 라우팅 테이블에 없는 경로는 게이트웨이를 통해 찾아감

```sh
# 기본 게이트웨이 설정
sudo ip route add default via IP주소 dev 인터페이스주소
```

### net-tools 패키지
- 네트워크 관련 전통적인 명령어들을 제공하는 패키지

```sh
sudo apt install net-tools
```

#### ifconfig 명령
- 형식: `ifconfig [인터페이스이름] [옵션] [값]`
- **옵션**
    - `a`: 시스템의 전체 인터페이스 정보 출력
    - `up/down`: 활성화 및 비활성화
    - `netmask`: 넷마스크 주소 설정
    - `broadcast`: 브로드캐스트 설정

### DNS 설정
- 리눅스는 DNS 정보를 `/etc/resolv.conf` 파일에 저장
    - `nameserver 127.0.0.53` → 로컬 스터브 주소를 가리키는 심볼릭 링크

```sh
# DNS 정보 확인
resolvectl status

# nmcli 명령으로 DNS 설정
nmcli con mod 커넥션이름 ipv4.dns DNS주소

# DNS 서버에 질의해 도메인의 IP 확인
nslookup
```

### netplan
- 우분투에서 네트워크 구성을 관리하는 도구
- 설정 파일은 **YAML 형식**으로 작성하며 `/etc/netplan/` 디렉토리에 존재
    - 파일 이름은 의미 없음

```sh
# 설정 적용
sudo netplan apply

# 또는 재부팅

# 권한 변경 (설정 파일들은 권한 변경 필요)
sudo chmod 600
```

- 파일을 수정하고 `sudo netplan apply` 또는 재부팅으로 적용

## 네트워크 설정
---
### 가상머신 복제
- 여러대의 가상머신을 하나의 네트워크로 구성
- 하나의 NAT 네트워크를 생성(여러 개의 가상머신을 하나의 스위치나 허브로 묶는 장비 생성)

===추가됨===

#### NAT 네트워크 생성
- [파일] → [도구] → [네트워크] 메뉴 실행
- [NAT 네트워크] 탭에서 만들기 선택
- 이름 수정 및 IPv4 접두사에 사용할 IP 대역 설정 (`192.168.0.0/24`)
- **DHCP 활성화** 체크 해제

#### 가상머신 네트워크 연결
- 가상머신 선택 → 설정 아이콘 → 네트워크 탭 선택
- `Attached to`를 **NAT 네트워크**로 선택 → 생성한 NAT 네트워크 선택

#### 가상머신 IP 설정

```sh
# 네트워크 설정 파일 확인
ls /etc/netplan

# 기존 설정 파일 삭제 후 새 파일 생성 (파일명 무관, 확장자는 yaml/yml)
vi netcfg.yaml
```

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    enp0s3:
      dhcp4: no
      addresses:
        - 192.168.0.101/24
      gateway4: 192.168.0.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
```

```sh
# 적용
sudo netplan apply
```

- *주의*: YAML 파일의 위치는 `/etc/netplan`이어야 하며, 이 디렉토리에는 YAML 파일이 1개만 있어야 함

#### 네트워크 연결 확인
- 2개 컴퓨터 간 `ping 상대방IP주소`로 연결 확인

#### 포트포워딩 설정
- **HOST IP/PORT**: 현재 컴퓨터의 IP와 사용할 포트
- **게스트 IP/PORT**: 가상머신의 IP와 포트 번호 (SSH는 22번)

### 호스트 이름 관련 명령어

#### uname
- 호스트 이름 관련 명령어
- 형식: `uname [옵션]`
- **옵션**: `m`, `n`, `r`, `s`, `v`, `a`

#### hostname
- 호스트 이름과 관련된 명령어
- `hostname -I`: 현재 설정된 IP 주소 확인 (IP가 안 보이면 IP 설정 미완료)
- `hostname`: 호스트 이름 출력
- `hostname [호스트이름]`: 호스트 이름 변경 (다음 로그인 시 적용, *하지만* 재부팅 시 소멸)

#### hostnamectl
- 호스트 이름 관련 명령 (영구 적용)
- `hostnamectl status`: 상태 조회
- `hostnamectl set-hostname 호스트이름`: 호스트 이름 변경 (파일 기반 → 재부팅 후 유지)

#### /etc/hostname
- hostname 관련 설정 파일
- `hostnamectl`은 이 파일을 수정 → 영구 적용
- `hostname`은 메모리만 변경 → 재부팅 시 소멸

#### /etc/hosts
- **개요**
    - 도메인 이름을 IP 주소에 수동 매핑하는 텍스트 파일
    - 호스트 이름 사용 시 가장 먼저 참조됨
    - 이 파일에 없으면 **DNS**가 해석
- **용도**
    - **로컬 호스트 및 개발**: 내부 통신 시 IP 대신 사용
    - **시스템 최적화**: 자주 사용하는 도메인 기재 → DNS 생략 → 속도 향상
    - **특정 사이트 차단**: 도메인에 루프백 주소 설정
- **설정 형식**: `IP주소 호스트이름 [별명 나열]`

===여기까지===

===추가됨===
## 3) 네트워크 상태 확인
---

### ping
- 외부와 통신이 되는지 확인하거나 외부 서버가 동작 중인지 확인
- 형식: `ping [옵션] [목적지 주소]`
- **옵션**
    - `a`: 통신이 되면 소리 출력
    - `q`: 종합 결과만 출력
    - `c 개수`: 보낼 패킷 수 지정
- 출력 해석: `64 bytes from server (192.168.0.101): icmp_seq=1 ttl=64 time=1.52 ms`
    - `icmp_seq`: 응답 순서
    - **ttl**(Time To Live): 패킷이 목적지까지 거친 라우터 수를 간접적으로 알려줌
        → 128 또는 64부터 시작, 라우터 거칠 때마다 1씩 감소
        → 높을수록 경로가 짧거나 안정적
    - `time`: 왕복 시간
- 요약 예시: `5 packets transmitted, 5 received, 0% packet loss, time 4005ms`
    - `rtt min/avg/max/mdev`: 최소/평균/최대/표준편차
- 통신이 안 될 때는 `ping`으로 **gateway** 확인 후 **DNS** 확인

### netstat
- 네트워크 연결 상태, 라우팅 테이블, 인터페이스 통계 정보 출력
- 현재 시스템에 열려있는 **포트** 확인 가능
- 형식: `netstat [옵션]`
- **옵션**
    - `a`: 모든 소켓 정보 출력
    - `r`: 라우팅 정보 출력
    - `n`: IP 주소로 출력 (호스트 이름 대신)
    - `i`: 모든 네트워크 인터페이스 정보 출력
    - `s`: 프로토콜별 통계 정보 출력
    - `p`: 해당 소켓과 관련된 프로세스 이름과 PID 출력

```sh
# 열려 있는 포트 확인
netstat -an | grep LISTEN

# 열려 있는 포트의 프로세스 확인
netstat -p
```

### arp
- 같은 네트워크에 있는 시스템들의 **MAC 주소**와 **IP 주소** 확인
- 형식: `arp [IP주소]`

### tcpdump
- **패킷 캡처** 명령
- 네트워크 상태 확인에 사용
- **옵션**
    - `c 패킷수`
    - `i 인터페이스이름`
    - `n`: IP 주소를 호스트 이름으로 변경하지 않음
    - `q`: 정보를 간단히 출력
    - `X`: 패킷 내용을 16진수와 ASCII로 출력
    - `w 파일명`: 덤프 내용을 파일에 기록
    - `r 파일명`: 파일에서 읽어오기
    - `host 호스트이름`
    - `port`
    - `ip`
- 명령보다는 **별도 애플리케이션**(와이어샤크, 패킷트레이서 등)을 이용해 수행

## 4) 방화벽 설정
---

### iptables
- **개요**
    - 리눅스 커널 내부의 패킷 필터링 프레임워크인 **netfilter**를 제어하는 명령줄 기반 보안 도구
    - 들어오고 나가는 모든 네트워크 패킷을 검사하고 규칙에 따라 허용/차단/전달 결정
    - 네트워크 **게이트키퍼** 역할
- **장점**
    - **커널 레벨의 고성능**: 커널 레이어에서 직접 패킷 제어 → 처리 속도 빠름, 자원 적게 사용
    - 포트, IP, 패킷 상태, NIC, MAC 주소, 패킷 문자열 감지 등 정교한 조건 생성 가능
    - 오랜 기간 리눅스 표준 방화벽 → 레퍼런스와 스크립트 툴이 다양
- **단점**
    - *하지만* 명령어가 복잡하고 가독성이 떨어짐 → 규칙 하나 잘못 추가 시 네트워크 전체 마비 가능
    - *하지만* 규칙을 위에서부터 순서대로 검사 → **순서 의존성**
    - *하지만* **휘발성 메모리**에서 작동 → 별도 저장하지 않으면 재부팅 시 규칙 소멸
- **구조: 3대 테이블**
    - **Filter**(기본 테이블): 패킷 허용/차단 결정 (방화벽 핵심)
    - **NAT**(Network Address Translation): 출발지/목적지 IP/포트 변환
    - **Mangle**: 패킷 헤더 정보 마킹/수정
- **구조: 5대 체인**
    - **INPUT**: 외부 → 서버 자체로 들어오는 패킷
    - **OUTPUT**: 서버 → 외부로 나가는 패킷
    - **FORWARD**: 서버를 거쳐 다른 곳으로 전달되는 패킷 (라우터/공유기 역할)
    - **PREROUTING**: NIC 도착 직후, 라우팅 경로 결정 전
    - **POSTROUTING**: 라우팅 완료 후, NIC 통해 나가기 직전
- **패킷 처리 규칙**
    - **ACCEPT**: 허용 및 통과
    - **DROP**: 완전 차단 (응답 없음 → **보안상 추천**)
    - **REJECT**: 차단 + 거부 메시지(ICMP 에러) 반환
    - **LOG**: 시스템 로그 기록 (패킷은 통과)

```sh
# 기본 filter 테이블 규칙 조회
sudo iptables -L -n -v --line-numbers

# NAT 테이블 규칙 조회
sudo iptables -t nat -L -n -v --line-numbers

# 기본 정책 변경
sudo iptables -P INPUT DROP       # 들어오는 패킷 기본 차단
sudo iptables -P OUTPUT ACCEPT    # 나가는 패킷 기본 허용
sudo iptables -P FORWARD DROP     # 거쳐가는 패킷 기본 차단

# 방화벽 규칙 추가
sudo iptables -A INPUT -i lo -j ACCEPT                     # 로컬 호스트 트래픽 허용
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT  # 연결된 패킷 자동 허용
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT         # SSH(22) 허용
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT         # HTTP(80) 허용
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT        # HTTPS(443) 허용
sudo iptables -A INPUT -s 아이피주소 -j DROP                # 특정 IP 차단

# 방화벽 규칙 삭제
sudo iptables -D INPUT 라인번호    # 번호 기반 삭제
sudo iptables -F                   # 모든 규칙 삭제

# 포트포워딩 (80 → 8080)
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080
```

- **규칙 저장**

```sh
# 패키지 설치
sudo apt install iptables-persistent

# 파일에 저장
sudo iptables-save | sudo tee /etc/iptables/rules.v4

# 파일에서 읽어오기
sudo iptables-restore < /etc/iptables/rules.v4
```

- **현대 리눅스에서 위치**
    - **ufw**: Ubuntu 기본 방화벽 도구 (iptables를 단순화 Wrapping)
    - **nftables**: 차세대 패킷 필터링 프레임워크

### ufw
- **개요**
    - **U**n**c**omplicated **F**ire**W**all의 약자
    - iptables를 사용자 친화적으로 **Wrapping**한 도구
    - 백엔드는 여전히 iptables 규칙을 생성하지만 사용자는 단순한 명령어로 제어 가능
- **핵심 동작 방식**
    - **Whitelist** 방식 기본: 외부 접근은 전부 차단, 내부 통신은 전부 허용
    - 필요한 포트만 선택적으로 개방
- **특징**
    - 명령 체계 단순
        - iptables: `iptables -A INPUT -p tcp --dport 22 -j ACCEPT`
        - ufw: `sudo ufw allow ssh`
    - 규칙 관리: `sudo ufw status numbered` / `sudo ufw delete 번호`
    - 응용프로그램 프로필 지원: `sudo ufw allow nginx full`
    - 다중 조건 조합 가능 (IP + 프로토콜 + 포트)

```sh
# 상태 확인 및 활성화
sudo ufw status verbose    # 상태 확인
sudo ufw enable           # 방화벽 활성화
sudo ufw disable          # 방화벽 비활성화

# 기본 정책 설정
sudo ufw default deny incoming     # 들어오는 모든 접속 차단
sudo ufw default allow outgoing    # 나가는 모든 접속 허용

# 포트 번호 기반 설정
sudo ufw allow 포트번호              # 특정 포트 허용
sudo ufw allow 포트번호/tcp          # 프로토콜 지정 허용
sudo ufw deny 포트번호               # 특정 포트 차단
sudo ufw allow 시작번호:끝번호/tcp    # 포트 범위 허용

# 서비스 이름 기반 설정
sudo ufw allow ssh                # SSH 허용

# 특정 IP 기반 설정
sudo ufw allow from IP                       # 특정 IP 접근만 허용
sudo ufw allow from 네트워크주소/서브넷마스크  # 특정 네트워크 대역 허용
sudo ufw allow from IP주소 to any port 포트번호 proto tcp  # IP + 포트 조건

# 규칙 삭제 및 초기화
sudo ufw delete 번호              # 번호로 삭제
sudo ufw delete allow 80          # 명령어로 삭제
sudo ufw reset                    # 전체 초기화
```

===여기까지===