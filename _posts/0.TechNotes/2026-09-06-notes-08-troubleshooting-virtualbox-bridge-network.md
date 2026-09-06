---
title: VirtualBox Kubernetes Lab에 접속할 수 없었던 이유
description: 노트북의 연결을 유선에서 Wi-Fi로 전환한 뒤 발생한 Windows DHCP, VirtualBox Bridged Adapter와 Ubuntu Netplan 문제를 계층별로 추적한 기록
date: 2026-09-06
series: TechNotes
tags:
  - TroubleShooting
  - Network
---

노트북에서 실행하던 Kubernetes 실습 VM을 별도의 데스크톱으로 이전하기 위해 노트북의 유선 LAN Cable을 데스크톱으로 옮겼다. 노트북은 Wi-Fi로 전환했지만 인터넷 연결부터 VirtualBox VM의 SSH 접속까지 연속해서 문제가 발생했다.

겉으로는 하나의 장애처럼 보였지만 Windows의 DHCP, VirtualBox의 Bridged Adapter와 Ubuntu VM의 Network 설정에서 서로 다른 문제가 이어진 상황이었다. 이 글에서는 확인된 사실과 당시의 추정을 구분하여 각 Network 계층을 어떤 순서로 확인했는지 정리한다.

## 1 ) 장애 발생 전 구성

---

나는 Windows 랩탑을 홈 네트워크 아래에 두고, VPN을 구성하여 외부에서 접속이 가능하도록 구성해두고 실습 시마다 사용해오고 있었다.
노트북의 VirtualBox에는 Kubernetes와 NFS 실습용 VM 네 개가 실행되고 있었다.

```text
Windows Laptop
│
├── lab-control-plane  192.168.0.200
├── lab-worker1        192.168.0.201
├── lab-worker2        192.168.0.202
└── lab-nfs            192.168.0.203
```

각 VM의 Network Adapter는 Bridged Adapter로 구성되어 노트북의 Realtek 유선 NIC를 통해 `192.168.0.0/24` Network에 연결되어 있었다.

```text
VM
 │
VirtualBox Bridged Adapter
 │
Realtek Ethernet NIC
 │
ipTIME Router
```

실습 VM을 장기적으로 수용할 별도의 Linux Host를 준비하면서 노트북에 연결되어 있던 LAN Cable을 데스크톱으로 옮겼다. 물리 연결은 다음과 같이 변경되었다.

```text
변경 전

Windows Laptop
      │ Ethernet
      ▼
ipTIME Router
```

```text
변경 후

Linux Host ── Ethernet ── ipTIME Router

Windows Laptop ── Wi-Fi ── ipTIME Router
```

이 변경은 Kubernetes 설정 자체를 수정한 작업이 아니다. Host의 물리 Network 경로가 Ethernet에서 Wi-Fi로 바뀐 작업이다.

## 2 ) 장애를 세 단계로 분리

---

복구 과정에서 관찰한 증상은 다음 세 단계로 나뉘었다.

| 단계 | 관찰한 증상 | 확인할 계층 |
|---|---|---|
| 1 | Wi-Fi AP에는 연결됐지만 인터넷을 사용할 수 없음 | Windows IP·DHCP |
| 2 | Windows 인터넷은 복구됐지만 Host에서 VM으로 Ping·SSH 실패 | Routing·VirtualBox Bridge |
| 3 | Bridge 설정 변경 후 일부 VM의 NIC는 존재하지만 `DOWN` 상태 | Guest NIC·Netplan |

단계별 장애를 구분하지 않으면 Windows DHCP 문제를 해결한 뒤에도 VM 접속 실패를 같은 원인으로 오해하기 쉽다.

## 3 ) Wi-Fi 연결과 IP 할당을 분리해서 확인

---

노트북은 Wi-Fi 이름과 신호 세기를 정상적으로 표시했지만 인터넷에 연결되지 않았다. 먼저 Windows에서 사용 중인 Adapter의 IP 설정을 확인했다.

```powershell
ipconfig /all
```

Wi-Fi Adapter에는 다음과 같은 값이 표시되었다.

```text
DHCP 사용           : 예
자동 구성 IPv4 주소 : 169.254.100.110
서브넷 마스크       : 255.255.0.0
기본 게이트웨이     : 없음
```

`169.254.0.0/16`은 Windows가 DHCP Server에서 IPv4 설정을 받지 못했을 때 사용하는 APIPA(Automatic Private IP Addressing) 범위이다. 이 주소와 Gateway가 없다는 결과로 다음 상태를 확인할 수 있었다.

```text
Wi-Fi Association   성공
        │
        ▼
DHCP 주소 할당      실패
        │
        ▼
169.254.x.x 자동 구성
        │
        ▼
기본 Gateway 없음
```

Wi-Fi의 무선 연결 상태는 별도로 확인했다.

```powershell
netsh wlan show interfaces
```

확인 결과 SSID, 신호 세기와 연결 상태는 정상으로 표시되었다. 따라서 이 시점의 문제는 AP와의 Association이 아니라 IPv4 설정을 받지 못한 상태였다.

### DHCP Lease 재요청

처음에는 DHCP 주소를 반납하고 다시 요청했다.

```powershell
ipconfig /release
ipconfig /renew
```

유선 LAN Cable이 제거된 Ethernet Adapter에서는 다음 메시지가 함께 출력되었다.

```text
미디어의 연결이 끊긴 상태에서는 이더넷에서 작업을 수행할 수 없습니다.
```

이 메시지는 Cable이 연결되지 않은 Ethernet Adapter에 대한 결과이다. Wi-Fi의 DHCP 처리 결과와 구분해야 한다. Wi-Fi만 대상으로 실행하려면 Adapter 이름을 지정한다.

```powershell
ipconfig /release "Wi-Fi"
ipconfig /renew "Wi-Fi"
```

Wi-Fi 갱신 과정에서는 다음 오류가 발생했다.

```text
인터페이스 갱신하는 동안 오류 발생:
개체가 이미 있음
```

이 메시지만으로 중복된 IP Address나 Route가 정확한 원인이라고 확정할 수는 없다. 당시에는 Windows TCP/IP 상태 이상을 의심하고 현재 설정을 먼저 확인했다.

```powershell
Get-NetIPConfiguration -InterfaceAlias "Wi-Fi"
Get-NetIPAddress -InterfaceAlias "Wi-Fi"
Get-NetRoute -InterfaceAlias "Wi-Fi"
```

### Windows Network 설정 초기화

일반적인 DHCP 재요청으로 복구되지 않아 관리자 권한 Terminal에서 Winsock Catalog와 TCP/IP 설정을 초기화했다.

```powershell
netsh winsock reset
netsh int ip reset
```

이 명령은 Network 설정에 영향을 준다. 기존 수동 IP, DNS나 별도 Network 구성이 있다면 먼저 기록하고, 다른 원인 확인 없이 첫 단계에서 실행하지 않는다. 적용을 완료하기 위해 Windows를 재부팅했다.

```powershell
shutdown /r /t 0
```

재부팅 후 `ipconfig /all`에서 다음 상태를 확인했다.

```text
IPv4 주소       : 192.168.0.x
서브넷 마스크   : 255.255.255.0
기본 게이트웨이 : 192.168.0.1
DHCP 사용       : 예
```

Wi-Fi 인터넷은 복구되었다. 다만 DHCP 응답을 받지 못한 최초 원인은 Packet Capture나 Windows Event 등으로 확인하지 못했다. 따라서 “Windows Network 초기화와 재부팅 후 복구됨”은 확인된 사실이지만, 특정 IP Object나 Route가 근본 원인이었다고 단정하지 않는다.

## 4 ) 인터넷 복구와 VM 접속 복구는 별개였다

---

Windows의 Wi-Fi 인터넷이 복구된 뒤에도 외부 SSH 에서 VirtualBox VM으로 접속할 수 없었다.

```powershell
ping 192.168.0.200
ping 192.168.0.201
ssh <user>@192.168.0.200
```

반면 VM 사이의 통신은 유지되고 있었다.

```text
lab-control-plane ↔ lab-worker1   정상
lab-control-plane ↔ lab-worker2   정상
worker            ↔ lab-nfs       정상
Windows Host       → VM            실패
```

이 결과는 Kubernetes Pod Network 전체가 중단됐다는 의미가 아니다. VM 내부 경로는 동작하고 있었고 Windows Host에서 VM으로 가는 경로만 실패했다. 따라서 Kubernetes Resource보다 먼저 Host Routing과 VirtualBox Network 연결을 확인했다.

Windows Routing Table을 조회했다.

```powershell
route print
```

주요 결과는 다음과 같았다.

```text
0.0.0.0/0       → 192.168.0.1   Interface 192.168.0.99
192.168.0.0/24  → 연결됨        Interface 192.168.0.99

VirtualBox Host-Only Adapter
169.254.70.191/16
```

Windows는 VM의 `192.168.0.20x` 주소를 Wi-Fi와 같은 Local Network의 주소로 판단하고 있었다. Host-Only Adapter는 해당 대역을 담당하지 않았다. 이 결과만으로 VirtualBox 설정을 확정할 수는 없지만, VM이 어떤 Host Interface에 Bridge되어 있는지 확인해야 한다는 범위를 정할 수 있었다.

## 5 ) 확정 원인은 Bridged Adapter의 대상 NIC였다

---

VM을 종료한 뒤 VirtualBox의 다음 설정을 확인했다.

```text
VM 설정
└── Network
    └── Adapter 1
        ├── Attached to : Bridged Adapter
        └── Name        : Realtek PCIe GbE Family Controller
```

Bridged Adapter의 대상이 LAN Cable을 제거한 Realtek Ethernet NIC로 남아 있었다. 장애 전에는 이 경로가 유효했다.

```text
VM
 │
VirtualBox Bridge
 │
Realtek Ethernet
 │
LAN Cable
 │
Router
```

Cable을 데스크톱으로 옮긴 뒤에는 같은 설정이 물리적으로 끊긴 Interface를 가리켰다.

```text
VM
 │
VirtualBox Bridge
 │
Realtek Ethernet
 │
Cable 없음
 ╳
```

VirtualBox의 Bridged Adapter는 사용자가 선택한 Host Network Interface를 통해 Guest Traffic을 전달한다. Windows가 Wi-Fi로 인터넷에 연결되었다고 해서 기존 VM의 Bridge 대상도 자동으로 Wi-Fi NIC로 변경되는 것은 아니었다.

각 VM의 Bridge 대상 `Name`을 현재 연결된 Wi-Fi Adapter로 변경했다.

```text
기존: Realtek PCIe GbE Family Controller
변경: Intel(R) Wi-Fi 6 AX201 160MHz
```

이 단계에서는 동시에 여러 설정을 바꾸지 않는 것이 중요하다. 우선 다음 값은 유지하고 Bridge 대상만 변경해야 원인과 결과를 분리할 수 있다.

- Adapter Type

- MAC Address

- Promiscuous Mode

- Cable Connected 상태

Wi-Fi Bridging은 Host OS, Wi-Fi Driver와 Access Point 구성에 따라 Ethernet Bridging과 다르게 동작하거나 제한될 수 있다. 따라서 Bridge 대상을 Wi-Fi NIC로 변경했다는 사실만으로 모든 환경에서 같은 결과가 보장되지는 않는다.

## 6 ) 가상 NIC 변경 후 발생한 두 번째 문제

---

Bridge 대상을 변경하는 과정에서 Guest에 보여줄 Adapter Type도 `virtio-net`으로 변경했다. 이후 `lab-nfs`를 제외한 일부 Ubuntu VM에서 Network가 올라오지 않았다.

```bash
ip addr
```

다음 상태가 확인되었다.

```text
2: enp0s3: <BROADCAST,MULTICAST>
    state DOWN
```

`enp0s3` Interface는 존재했다. 처음엔 “NIC가 유실됐네” 라고 생각했는데, 다음 상태로 표현하는 것이 정확하다고 한다.

```text
NIC 존재
   │
   ▼
Link DOWN
   │
   ▼
IPv4 Address 없음
```

Adapter Type 변경이 직접 원인이었는지, Netplan 설정이 적용되지 않은 이유가 무엇인지는 당시 기록해두었던 자료만으로 확정할 수 없었다. 초반 이슈 이후로는 Interface 이름이 계속 `enp0s3`로 확인됐고 변경 전후 Netplan과 System Log를 모두 보존하지 못했기 때문이다.

### Interface와 Netplan 확인

먼저 한 VM에서 Interface를 임시로 활성화했다.

```bash
sudo ip link set enp0s3 up
ip link show enp0s3
ip addr show enp0s3
```

`ip link set`으로 변경한 상태는 재부팅 후에도 유지되는 영구 Network 설정이 아니다. NIC를 올릴 수 있는지 확인한 뒤 Netplan을 점검했다.

```bash
ls -l /etc/netplan/
sudo cat /etc/netplan/*.yaml
```

Netplan의 Interface 이름과 `ip addr`에서 확인한 실제 이름이 같은지 확인했다.

```yaml
network:
  version: 2
  ethernets:
    enp0s3:
      dhcp4: false
      addresses:
        - 192.168.0.200/24
      routes:
        - to: default
          via: 192.168.0.1
      nameservers:
        addresses:
          - 8.8.8.8
          - 1.1.1.1
```

각 VM에는 해당 Node에 할당한 IP Address를 사용한다.

| VM | Address |
|---|---|
| `lab-control-plane` | `192.168.0.200/24` |
| `lab-worker1` | `192.168.0.201/24` |
| `lab-worker2` | `192.168.0.202/24` |
| `lab-nfs` | `192.168.0.203/24` |

여러 Netplan YAML File이 존재하면 설정이 함께 처리되므로 같은 Interface를 중복 정의하거나 서로 다른 값을 적용하는 File이 있는지도 확인해야 한다.

설정의 YAML 문법과 생성 결과를 먼저 검사했다.

```bash
sudo netplan generate
```

Network를 변경할 때는 가능하면 다음 명령으로 임시 적용하여 **연결이 끊기면 이전 설정으로 돌아갈 수 있게 한다**.

```bash
sudo netplan try
```

확인 후 설정을 적용한다.

```bash
sudo netplan apply
```

SSH로 접속한 상태에서 Network를 변경하면 연결을 잃을 수 있다. 이번과 같이 Guest Network 자체가 동작하지 않는 상황에서는 VirtualBox Console에서 작업하는 것이 안전하다.

적용 후 Interface, Route와 통신을 순서대로 확인했다.

```bash
ip addr show enp0s3
ip route
ping -c 3 192.168.0.1
ping -c 3 192.168.0.99
```

Netplan을 다시 적용한 뒤 각 VM의 고정 IP가 복구되었고 외부 네트워크에서 VPN에 접속된 Mac의 SSH와 Windows Host에서이 VM으로 Ping과 SSH가 가능해졌다. 

## 7 ) 확인된 사실과 추정을 구분

---

복구됐다는 사실만으로 사용한 명령이 곧 근본 원인을 입증하는 것은 아니지만, 네트워크 구성이 변경될 때마다 비슷한 장애가 발생해왔었고, 다시 기억할 수 있도록 이번 장애의 판단 수준을 구분하면 다음과 같다.

| 항목                                   | 판단  | 근거                                        |
| ------------------------------------ | --- | ----------------------------------------- |
| Windows가 정상 DHCP 주소를 받지 못함           | 확인됨 | `169.254.x.x`, Gateway 없음                 |
| Wi-Fi Association 자체는 정상             | 확인됨 | `netsh wlan show interfaces`의 연결 상태       |
| Windows TCP/IP 내부 Object 충돌이 근본 원인   | 미확정 | 초기화 후 복구됐지만 직접 원인을 확인하지 못함                |
| VM Bridge가 연결이 끊긴 Ethernet NIC를 참조함  | 확인됨 | VirtualBox VM Network 설정에서 Realtek NIC 확인 |
| 해당 Bridge 설정이 Host에서 VM으로 접근하지 못한 원인 | 확인됨 | 물리 연결 상태와 Bridge 대상이 불일치했고 변경 후 경로 복구     |
| Ubuntu VM의 `enp0s3`가 존재하지만 `DOWN` 상태 | 확인됨 | VM의 `ip addr` 결과                          |
| Adapter Type 변경 후 Netplan 장애 발생      | 확인됨 | Adapter에 따라 netplan에서 인터페이스를 재할당하여 복구     |
| Guest Network 설정을 확인하고 다시 적용한 뒤 복구   | 확인됨 | 고정 IP, Ping과 SSH 복구                       |

가장 명확했던 원인은 VirtualBox Bridge가 물리적으로 연결되지 않은 Host NIC를 계속 참조했다는 점이다.

## 8 ) 계층별 진단 순서

---

“통신이 안 된다”는 증상을 하나의 문제로 다루지 않고 아래에서 위로 확인했다.

```text
Wi-Fi Association
        │
        ▼
IP Address와 DHCP
        │
        ▼
Default Gateway와 Host Route
        │
        ▼
VirtualBox Attachment Mode
        │
        ▼
Bridge 대상 Host NIC
        │
        ▼
Guest NIC Link 상태
        │
        ▼
Netplan Address와 Route
        │
        ▼
Ping과 SSH
```

각 단계의 판단 기준은 다음과 같다.

| 확인 결과                               | 다음으로 볼 대상                         |
| ----------------------------------- | --------------------------------- |
| Wi-Fi가 연결되지 않음                      | Wi-Fi Profile, 인증과 Adapter 상태     |
| Wi-Fi 연결, `169.254.x.x`, Gateway 없음 | DHCP와 Windows IP 설정               |
| ipTIME 의 DHCP 충돌은 아니었음              | ipTIME DHCP 서버 관리 및 내부 네트워크 설정    |
| Host 인터넷 정상, Host에서 모든 VM 접근 실패     | VirtualBox Attachment와 Bridge 대상  |
| VM끼리 통신 가능, Host에서 VM만 실패           | Host와 VM 사이의 VirtualBox 경로        |
| Guest NIC가 보이지 않음                   | 가상 NIC 연결 여부와 Guest Driver        |
| Guest NIC가 존재하지만 `DOWN`             | Link 상태와 Guest Network 설정         |
| IP는 있지만 Gateway Ping 실패             | Subnet, Route, Bridge와 물리 Network |
| Ping 성공, SSH만 실패                    | SSH Service, Port와 Firewall       |

이 순서를 사용하면 DHCP 장애 상태에서 SSH 설정을 바꾸거나, Guest NIC가 `DOWN`인 상태에서 Kubernetes 설정을 먼저 수정하는 일을 피할 수 있을 것 같다.

## 9 ) 재발 방지 기준

---

### Host의 물리 Interface가 바뀌면 Bridge 대상을 확인한다

Bridged Adapter는 특정 Host Interface에 연결된다. Ethernet에서 Wi-Fi로 전환하거나 USB Ethernet Adapter를 교체했다면 모든 VM의 Bridge 대상을 확인한다.

### 한 번에 하나의 설정만 변경한다

Bridge 대상과 Adapter Type을 동시에 변경하면 어떤 변경이 장애를 만들었는지 분리하기 어렵다. 다음 순서로 하나씩 변경하고 매 단계에서 통신을 확인한다.

1. Bridge 대상 Host NIC 변경

2. Guest 부팅 후 NIC와 IP 확인

3. Gateway와 Host 통신 확인

4. 필요한 경우에만 Adapter Type 변경

5. 다시 Guest NIC와 Netplan 확인

### MAC Address를 불필요하게 변경하지 않는다

DHCP Reservation이나 Network 접근 정책에서 MAC Address를 사용할 수 있다. Bridge 대상만 변경하는 작업에서는 Guest MAC Address를 유지한다.

### Network 변경 전 현재 상태를 기록한다

Windows에서는 다음 결과를 보존한다.

```powershell
ipconfig /all
route print
Get-NetIPConfiguration
```

Ubuntu VM에서는 다음 결과를 보존한다.

```bash
ip addr
ip route
sudo cat /etc/netplan/*.yaml
```

변경 전후 결과가 있으면 복구 여부뿐 아니라 정확한 원인까지 확인할 수 있다.

### Netplan은 Console과 Rollback을 준비한다

Remote 접속 중 Network를 변경해야 한다면 `netplan try`를 우선 사용한다. Bridge, IP와 Route를 변경하는 작업은 연결이 끊길 수 있으므로 가능한 경우 Local Console이나 VirtualBox Console을 확보한다.

## 10 ) 최종 확인

---

각 계층의 복구 여부를 다음 순서로 확인했다.

### Windows Host

```powershell
ipconfig /all
ping 192.168.0.1
ping 192.168.0.200
ssh <user>@192.168.0.200
```

### Ubuntu VM

```bash
ip addr show enp0s3
ip route
ping -c 3 192.168.0.1
ping -c 3 192.168.0.99
```

확인 결과는 다음과 같았다.

| 대상 | 결과 |
|---|---|
| Windows Wi-Fi의 DHCP Address와 Default Gateway | 복구 |
| Windows 인터넷 연결 | 복구 |
| Windows Host에서 VM Ping | 복구 |
| Windows Host에서 VM SSH | 복구 |
| VM 사이 통신 | 정상 |
| Ubuntu VM의 고정 IP와 Default Route | 복구 |

## 전체 정리

---

> **최종 정리**
>
> - `169.254.x.x` 주소와 Gateway 부재는 Wi-Fi 연결 여부가 아니라 DHCP 주소 할당부터 확인해야 한다는 단서였다.
>
> - Windows 인터넷이 복구되어도 VirtualBox VM의 Network 경로가 자동으로 복구되는 것은 아니다.
>
> - VirtualBox VM은 연결이 끊긴 Realtek Ethernet NIC에 계속 Bridge되어 있었으며, 이것이 Host에서 VM으로 접근할 수 없었던 확정 원인이었다.
>
> - Guest의 `enp0s3`는 유실된 것이 아니라 존재하지만 `DOWN` 상태였고, Interface와 Netplan을 확인하고 다시 적용한 뒤 고정 IP가 복구되었다.
>
> - Network 장애는 Association, DHCP, Route, VirtualBox Bridge, Guest NIC, Netplan과 Application 순서로 계층을 나누어 확인한다.
