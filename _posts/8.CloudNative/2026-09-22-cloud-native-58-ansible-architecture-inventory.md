---
title: Ansible Architecture와 Inventory 구성
description: Ansible Control Node와 Managed Node의 역할을 이해하고 Ubuntu 설치, SSH 공개키 인증과 Inventory를 구성하여 연결을 검증한다
date: 2026-09-22
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Ansible
---

[Argo CD Git Repository 연동과 수동 Sync](/cloud-native-57-argocd-git-repository-manual-sync/)에서는 Git의 Desired State를 Kubernetes Cluster에 반영하는 GitOps 흐름을 구성했다. 이번에는 Ansible이 Control Node에서 여러 Managed Node의 Package, File과 Service 상태를 일관되게 관리하는 구조를 살펴보고 실제 연결 환경을 준비한다.

## 1 ) IaC와 Ansible의 역할

---

> **Infrastructure as Code(IaC)**는 Infrastructure의 구성과 원하는 상태를 Code 또는 선언 File로 관리하고, 변경 이력을 Version Control System에 남기는 방식이다.

Infrastructure 자동화 도구는 담당하는 범위에 따라 역할이 다르다. Terraform과 Ansible은 모두 자동화에 사용하지만 중심 영역이 다르다.

| 항목 | Terraform | Ansible |
|---|---|---|
| 중심 역할 | Infrastructure Provisioning과 수명 주기 관리 | Server 구성 관리와 IT 자동화 |
| 정의 언어 | HCL | YAML |
| 확장 단위 | Provider | Module, Plugin과 Collection |
| 일반적인 대상 | Cloud, Network, VM과 Managed Service | Package, File, Service, Application과 장비 설정 |
| Managed Node Agent | 별도 Agent 불필요 | 별도 Agent 불필요 |

두 도구의 영역이 완전히 분리되는 것은 아니다. Terraform으로 Network와 VM을 생성한 뒤 Ansible로 각 VM의 Package와 설정 File을 배포하는 방식으로 함께 사용할 수 있다. Terraform과 다른 IaC 도구의 관계는 [Cloud 기술 개요](/cloud-02-technology/)에서, CI/CD Pipeline에서 Ansible이 담당하는 위치는 [CI/CD Pipeline 구조와 도구](/cloud-native-45-cicd-pipeline/)에서 확인할 수 있다.

Ansible은 다음과 같은 작업을 자동화할 수 있다.

- `apt`, `dnf`와 같은 Package Manager를 이용한 Software 설치와 제거

- 설정 File, Script와 Application Artifact 배포

- Service 시작, 중지와 재시작

- HTTP 또는 FTP Resource Download

- Git Repository Checkout

- Cloud, Virtualization, Network와 Container Resource 관리

- Build와 Test 명령 실행

## 2 ) Ansible의 동작 특성

---

Ansible은 Python으로 작성된 Agentless 자동화 도구이다. 사용자가 Control Node에서 명령을 실행하면 Ansible이 Inventory를 이용해 대상을 선택하고 Module을 실행한다.

| 특성 | 의미 |
|---|---|
| Agentless | Managed Node에 상시 실행되는 Ansible Agent를 설치하지 않는다. |
| Push 방식 | Control Node가 SSH 등의 연결을 통해 작업을 Managed Node에 전달한다. |
| 선언적 상태 | 다수의 Module이 실행 절차보다 원하는 최종 상태를 매개변수로 받는다. |
| 멱등성 | 멱등성을 지원하는 Module은 이미 원하는 상태이면 추가 변경을 만들지 않는다. |
| 순서 보장 | 기본 Linear Strategy에서는 현재 Task가 대상 Host에서 처리된 뒤 다음 Task로 진행한다. |
| 병렬 실행 | 선택한 Host를 병렬로 처리하지만 한 번에 실행하는 수는 `forks` 설정의 제한을 받는다. |

멱등성은 모든 명령이 한 번만 실행된다는 뜻이 아니다. `ansible.builtin.apt`, `ansible.builtin.copy`처럼 현재 상태를 확인하는 Module은 불필요한 변경을 피할 수 있다. 반면 `ansible.builtin.command`와 `ansible.builtin.shell`은 별도 조건을 설정하지 않으면 실행할 때마다 명령을 수행한다.

실행 결과에는 Host별 상태가 표시된다.

| 상태 | 의미 |
|---|---|
| `ok` | Task가 정상 처리됐고 상태 변경은 없었다. |
| `changed` | Task가 정상 처리됐으며 Managed Node의 상태가 변경됐다. |
| `failed` | Managed Node에 연결했지만 Task 실행이 실패했다. |
| `unreachable` | Network, SSH 또는 인증 문제로 Managed Node에 연결하지 못했다. |

## 3 ) Ansible Architecture

---

Ansible 환경은 자동화를 시작하는 Control Node와 실제 작업 대상인 Managed Node로 구분한다.

| 구성 요소 | 실행 위치 | 역할 |
|---|---|---|
| Control Node | Ansible 실행 Host | Ansible Core를 실행하고 Inventory와 Playbook을 해석한다. |
| Managed Node | 원격 관리 대상 | Module이 전달한 작업을 실행하고 결과를 반환한다. |
| Inventory | Control Node | 관리할 Host, Group과 연결 변수를 정의한다. |
| Playbook | Control Node | Managed Node에 적용할 Play와 Task를 YAML로 정의한다. |
| Module | 주로 Managed Node | Package, File과 Service 같은 실제 작업 단위를 수행한다. |
| Plugin | 주로 Control Node | 연결, Inventory 처리, Data 변환과 출력 기능을 확장한다. |

{% include visuals/ansible-control-managed-node-flow.html %}

Control Node는 Python이 설치된 Linux, macOS, BSD와 Windows Subsystem for Linux 환경에서 구성할 수 있다. WSL을 사용하지 않는 Native Windows는 Control Node로 지원되지 않는다.

일반적인 POSIX Managed Node에는 다음 조건이 필요하다.

- Control Node에서 접속할 수 있는 SSH Service와 사용자 계정

- Ansible Module이 생성한 Python Code를 실행할 수 있는 Python

- Package 설치나 System File 변경에 필요한 `sudo` 또는 다른 Privilege Escalation 수단

Network 장비 전용 Module처럼 Managed Node의 Python을 요구하지 않는 예외도 있으므로 사용하는 Module의 요구 조건을 확인한다.

Ansible의 기본 실행 흐름은 다음과 같다.

1. Control Node가 Inventory를 읽고 Host Pattern에 해당하는 Managed Node를 선택한다.

2. Ad-hoc 명령 또는 Playbook의 Task에서 실행할 Module과 Argument를 결정한다.

3. SSH 연결로 대상 Host를 인증하고 필요한 Module Code를 실행한다.

4. Managed Node가 현재 상태를 확인하고 필요한 변경을 수행한다.

5. Control Node가 Host별 `ok`, `changed`, `failed`, `unreachable` 결과를 집계한다.

## 4 ) 실습 구성

---

하나의 Control Node와 세 개의 Managed Node를 사용한다. 아래 IP는 문서용 예시 주소이므로 실제 환경의 주소로 바꾼다.

| Hostname | 역할 | 예시 IP | Ansible 설치 |
|---|---|---|---|
| `control` | Control Node | `192.0.2.10` | 필요 |
| `master` | Managed Node | `192.0.2.11` | 불필요 |
| `worker1` | Managed Node | `192.0.2.12` | 불필요 |
| `worker2` | Managed Node | `192.0.2.13` | 불필요 |

`master`, `worker1`, `worker2`는 Kubernetes 역할을 설명하기 위한 이름이 아니라 Ansible이 관리할 세 Linux Host의 식별자이다. Ansible은 세 Host를 같은 Inventory Group으로 묶어 동일한 작업을 적용한다.

작업 위치를 구분하면 다음과 같다.

| 작업 | Control Node | Managed Node |
|---|---:|---:|
| Ansible 설치 | O | X |
| 자동화 전용 계정 생성 | X | O |
| SSH Key 생성 | O | X |
| Public Key 등록 | 전송 | 저장 |
| Inventory와 Playbook 작성 | O | X |
| Module 실행 | 요청·결과 수집 | 실제 처리 |

## 5 ) Ubuntu Control Node에 Ansible 설치

---

다음 명령은 `control` Host에서 실행한다. Ubuntu PPA를 등록할 때 사용하는 `add-apt-repository` 명령을 위해 `software-properties-common`을 먼저 설치한다.

```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository --yes --update ppa:ansible/ansible
sudo apt install -y ansible
```

설치된 Ansible Core, Python, Module과 Collection 경로를 확인한다.

```bash
ansible --version
ansible-community --version
```

`ansible --version`은 실제 실행 Runtime인 `ansible-core` Version을 표시한다. 전체 Community Package Version은 `ansible-community --version`으로 구분해 확인한다.

원격 Host를 연결하기 전에 Local Connection으로 Ansible 실행 자체를 확인한다. `localhost,` 뒤의 쉼표는 문자열을 Inventory Host 목록으로 해석하게 하고, `-c local`은 SSH 대신 Local Connection을 사용한다.

```bash
ansible localhost \
  -i localhost, \
  -c local \
  -m ansible.builtin.ping
```

정상 결과에는 `SUCCESS`, `changed: false`와 `ping: pong`이 표시된다.

## 6 ) Managed Node 계정과 권한 준비

---

다음 작업은 `master`, `worker1`, `worker2` 각각에서 실행한다. 자동화 전용 사용자 `ansible`을 만들고 처음 Public Key를 복사할 때 사용할 Password를 설정한다.

```bash
sudo adduser ansible
sudo passwd ansible
```

Package와 System Service를 관리하려면 Privilege Escalation 권한이 필요하다. 실습 환경에서 Password 없이 `sudo`를 사용하려면 `/etc/sudoers` 자체의 Permission을 변경하지 않고 전용 Drop-in File을 `visudo`로 작성한다.

```bash
sudo visudo -f /etc/sudoers.d/ansible
```

다음 한 줄을 입력하고 저장한다.

```text
ansible ALL=(ALL:ALL) NOPASSWD: ALL
```

File Permission과 문법을 검증한다.

```bash
sudo chmod 0440 /etc/sudoers.d/ansible
sudo visudo -cf /etc/sudoers.d/ansible
```

`NOPASSWD: ALL`은 실습 절차를 단순화하지만 해당 계정에 넓은 Root 권한을 부여한다. 운영 환경에서는 자동화 전용 계정, 접속 Source와 실행 가능한 명령을 제한하거나 `NOPASSWD`를 사용하지 않고 실행 시 `--ask-become-pass`를 사용한다.

SSH Service 상태와 Python을 확인한다.

```bash
systemctl is-active ssh
python3 --version
```

계정이나 Public Key를 추가했다는 이유만으로 SSH Service를 재시작할 필요는 없다. `sshd_config`를 변경한 경우에만 문법을 확인하고 Service를 Reload 또는 Restart한다.

## 7 ) SSH 공개키 인증과 Host Key 검증

---

> **사용자 공개키 인증**은 Control Node가 Private Key로 자신의 신원을 증명하고, Managed Node가 `authorized_keys`에 등록된 Public Key로 이를 확인하는 방식이다.

> **SSH Host Key**는 접속 대상 Server의 신원을 확인한다. 사용자 Key와 Host Key를 모두 검증해야 사용자와 Server 양쪽의 신원을 확인할 수 있다.

다음 명령은 `control` Host에서 실행한다. 기존 개인용 Key와 구분되는 Ansible 전용 Ed25519 Key Pair를 생성한다.

```bash
ssh-keygen \
  -t ed25519 \
  -C "ansible-control" \
  -f "$HOME/.ssh/id_ed25519_ansible"
```

| File | 역할 | 보관 위치 |
|---|---|---|
| `id_ed25519_ansible` | Control Node가 서명에 사용하는 Private Key | Control Node에서만 보관 |
| `id_ed25519_ansible.pub` | Managed Node가 접속 허용 여부를 확인하는 Public Key | 각 Managed Node의 `authorized_keys` |

Public Key만 각 Managed Node의 `ansible` 계정에 복사한다.

```bash
ssh-copy-id -i "$HOME/.ssh/id_ed25519_ansible.pub" ansible@192.0.2.11
ssh-copy-id -i "$HOME/.ssh/id_ed25519_ansible.pub" ansible@192.0.2.12
ssh-copy-id -i "$HOME/.ssh/id_ed25519_ansible.pub" ansible@192.0.2.13
```

Private Key는 전송하거나 Repository에 Commit하지 않는다. Managed Node에서 등록 상태와 Permission을 확인할 수 있다.

```bash
chmod 700 "$HOME/.ssh"
chmod 600 "$HOME/.ssh/authorized_keys"
```

최초 연결 전에 각 Managed Node Console에서 실제 SSH Host Key Fingerprint를 확인한다.

```bash
sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

Control Node에서 처음 `ssh`로 접속할 때 표시되는 Fingerprint가 위 결과와 같은지 확인하고 등록한다.

```bash
ssh -i "$HOME/.ssh/id_ed25519_ansible" ansible@192.0.2.11
ssh -i "$HOME/.ssh/id_ed25519_ansible" ansible@192.0.2.12
ssh -i "$HOME/.ssh/id_ed25519_ansible" ansible@192.0.2.13
```

Host Key 검사를 끄면 다른 Server를 대상 Host로 오인하는 공격을 탐지할 수 없다. `ANSIBLE_HOST_KEY_CHECKING=False`로 우회하지 않고 검증한 Host Key를 `known_hosts`에 유지한다.

## 8 ) Inventory 작성

---

> **Inventory**는 Ansible이 관리할 Host와 Group, 연결에 필요한 변수를 정의하는 Source이다.

Control Node에서 Project Directory를 만든다.

```bash
mkdir -p "$HOME/ansible-lab"
cd "$HOME/ansible-lab"
```

`inventory.ini`를 작성한다. Host Alias와 실제 접속 주소를 분리하면 Playbook에서는 `master`, `worker1`, `worker2`라는 이름을 유지하면서 IP만 바꿀 수 있다.

```ini
[lab]
master  ansible_host=192.0.2.11
worker1 ansible_host=192.0.2.12
worker2 ansible_host=192.0.2.13

[lab:vars]
ansible_user=ansible
ansible_ssh_private_key_file=~/.ssh/id_ed25519_ansible
```

`ansible_host`를 생략하고 Hostname을 직접 사용하려면 Control Node의 DNS 또는 `/etc/hosts`에서 이름이 해석되어야 한다.

```text
192.0.2.11 master
192.0.2.12 worker1
192.0.2.13 worker2
```

이 경우 Inventory는 다음처럼 단순화할 수 있다.

```ini
[lab]
master
worker1
worker2

[lab:vars]
ansible_user=ansible
ansible_ssh_private_key_file=~/.ssh/id_ed25519_ansible
```

Inventory에 Password나 Private Key 원문을 기록하지 않는다. Private Key는 제한된 File Permission으로 보관하고 Inventory에는 경로만 지정한다.

## 9 ) Project Local ansible.cfg

---

Project Directory의 `ansible.cfg`에 기본 Inventory를 지정하면 매번 `-i inventory.ini`를 입력하지 않아도 된다.

```ini
[defaults]
inventory = ./inventory.ini
host_key_checking = True
```

Ansible이 현재 Project의 설정을 읽었는지 확인한다.

```bash
ansible-config view
ansible-config dump --only-changed
```

`inventory`가 Project의 `inventory.ini`를 가리키고 `HOST_KEY_CHECKING`이 활성화되어 있어야 한다.

## 10 ) Inventory와 통신 검증

---

Inventory 문법과 Host 구성을 먼저 확인한다.

```bash
ansible-inventory --graph
ansible-inventory --list
ansible all --list-hosts
```

`--graph`는 Group과 Host 관계를 보여주고, `--list`는 Ansible이 해석한 전체 Inventory Data를 JSON으로 출력한다. `--list-hosts`는 현재 Host Pattern이 실제로 선택하는 대상만 확인한다.

세 Managed Node에 Ping Module을 실행한다.

```bash
ansible all -m ansible.builtin.ping
```

`ansible.builtin.ping`은 ICMP Echo를 보내는 Network Ping이 아니다. Ansible이 대상에 연결하고 사용할 수 있는 Python으로 Module을 실행한 뒤 `pong`을 반환하는 연결 검증이다.

문제가 발생하면 상태에 따라 확인 범위를 나눈다.

| 증상 | 확인할 내용 |
|---|---|
| `No inventory was parsed` | `ansible.cfg` 위치, `inventory` 경로와 INI 문법 |
| Host가 목록에 없음 | Group 이름, Host Pattern과 `ansible-inventory --graph` 결과 |
| `UNREACHABLE` | IP·DNS, SSH Port, Firewall, 계정과 Private Key 경로 |
| Host Key 검증 실패 | 대상 Server 변경 여부와 `known_hosts`의 기존 Key |
| `Permission denied (publickey)` | Public Key 등록 계정, `authorized_keys`와 Directory Permission |
| Python Interpreter 오류 | Managed Node의 Python 설치와 `ansible_python_interpreter` 설정 |
| `sudo` 실패 | `become` 사용 여부, `sudoers` 문법과 Password 정책 |

공식 문서는 [Ansible 설치 요구 조건](https://docs.ansible.com/projects/ansible/latest/installation_guide/intro_installation.html), [Ubuntu 설치](https://docs.ansible.com/projects/ansible/latest/installation_guide/installation_distros.html)와 [Inventory 작성 방법](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html)에서 확인할 수 있다.

> **최종 정리**
> - Ansible은 Control Node에서 Inventory와 자동화 정의를 읽고 SSH를 통해 Managed Node의 상태를 관리한다.
>
> - Agentless는 Managed Node에 상시 Ansible Agent를 설치하지 않는다는 뜻이며 일반적인 POSIX Module 실행에는 SSH와 Python이 필요하다.
>
> - 멱등성을 지원하는 Module은 이미 원하는 상태이면 변경하지 않지만 `command`와 `shell` 같은 작업은 별도 조건 없이 매번 실행된다.
>
> - Inventory는 Host Alias, 실제 주소, Group과 연결 변수를 분리하여 여러 Managed Node를 일관되게 선택한다.
>
> - SSH 사용자 Key와 Server Host Key를 모두 검증하고 `ping` Module로 실제 Ansible 연결을 확인한다.

다음 글인 [Ansible Ad-hoc 명령과 Playbook으로 Nginx 자동화](/cloud-native-59-ansible-adhoc-playbook-nginx/)에서는 연결된 Managed Node에 일회성 명령을 실행하고 반복 가능한 Playbook으로 Nginx를 배포한다.
