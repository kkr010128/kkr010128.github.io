---
title: Ansible Ad-hoc 명령과 Playbook으로 Nginx 자동화
description: Ansible Ad-hoc 명령의 Option과 Module을 익히고 반복 가능한 Playbook으로 Nginx 설치, 설정 배포와 검증을 자동화한다
date: 2026-09-22
updated_at: 2026-09-23
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Ansible
---

[Ansible Architecture와 Inventory 구성](/cloud-native-58-ansible-architecture-inventory/)에서는 Control Node와 Managed Node의 역할을 구분하고 SSH 공개키 인증과 Inventory를 구성했다. 이번에는 연결된 Host에 Ad-hoc 명령을 실행한 뒤 동일한 작업을 반복 가능한 Playbook으로 전환한다.

## 1 ) Ad-hoc 명령

---

> **Ad-hoc 명령**은 Playbook File을 만들지 않고 Ansible CLI에서 하나의 Module을 대상 Host에 직접 실행하는 방식이다.

일회성 상태 확인, 긴급한 File 복사와 간단한 Package 작업에 적합하다. 같은 작업을 반복하거나 여러 Task의 순서를 관리해야 한다면 Playbook으로 작성한다.

기본 형식은 다음과 같다.

```text
ansible <host-pattern> [option]
```

예를 들어 Inventory의 모든 Host에 Ping Module을 실행한다.

```bash
ansible all -m ansible.builtin.ping
```

주요 Option을 구분하면 다음과 같다.

| Option | Long Option | 역할 |
|---|---|---|
| `-i` | `--inventory` | 사용할 Inventory Source를 지정한다. |
| `-m` | `--module-name` | 실행할 Module을 지정한다. |
| `-a` | `--args` | Module에 전달할 Argument를 지정한다. |
| `-u` | `--user` | SSH로 접속할 Remote User를 지정한다. |
| `-b` | `--become` | `sudo` 등의 방법으로 권한을 상승한다. |
| `-k` | `--ask-pass` | SSH 접속 Password를 입력받는다. |
| `-K` | `--ask-become-pass` | Privilege Escalation Password를 입력받는다. |
|  | `--list-hosts` | 명령을 실행하지 않고 선택되는 Host만 표시한다. |
|  | `--check` | 지원하는 Module에서 실제 변경 없이 예상 결과를 확인한다. |

SSH Key 인증을 구성했다면 일반적으로 `-k`가 필요하지 않다. Managed Node의 `sudo`가 Password를 요구하면 `-b -K`를 함께 사용한다. `NOPASSWD` 정책을 사용한다면 `-b`만으로 권한을 상승할 수 있다.

명령을 실행하기 전에 Host Pattern이 의도한 대상을 선택하는지 확인한다.

```bash
ansible all --list-hosts
ansible lab --list-hosts
```

## 2 ) Module과 멱등성

---

> **Module**은 Package, File, Service처럼 Managed Node에서 수행할 작업을 캡슐화한 실행 단위이다.

이번 실습에서 사용하는 Module은 다음과 같다.

| Module | 역할 | 멱등성 판단 |
|---|---|---|
| `ansible.builtin.command` | Shell을 거치지 않고 명령 실행 | 기본적으로 실행할 때마다 동작 |
| `ansible.builtin.shell` | Pipe, Redirect와 환경 변수 등 Shell 문법 사용 | 기본적으로 실행할 때마다 동작 |
| `ansible.builtin.copy` | Control Node의 File을 Managed Node에 복사 | 내용과 속성이 같으면 변경하지 않음 |
| `ansible.builtin.file` | File, Directory와 Symbolic Link 상태 관리 | 원하는 상태와 같으면 변경하지 않음 |
| `ansible.builtin.get_url` | URL의 Resource를 Managed Node에 Download | Checksum과 대상 상태에 따라 판단 |
| `ansible.builtin.apt` | Debian·Ubuntu Package 관리 | 설치·삭제 상태를 비교하여 판단 |
| `ansible.builtin.service` | Service 상태 관리 | 현재 Service 상태를 확인하여 판단 |

단순한 실행은 `command`를 우선한다. 다음처럼 Shell 기능이 필요한 경우에만 `shell`을 사용한다.

```bash
ansible all \
  -m ansible.builtin.shell \
  -a 'ps -ef | grep [n]ginx > /tmp/nginx-process.txt'
```

`shell`의 Argument에 외부 입력을 그대로 연결하면 Shell Injection이 발생할 수 있다. 입력을 제한하고, Pipe나 Redirect가 필요하지 않다면 `command`를 사용한다.

사용 가능한 Module과 상세 Argument는 Control Node에서 확인할 수 있다.

```bash
ansible-doc -l
ansible-doc ansible.builtin.command
ansible-doc ansible.builtin.copy
ansible-doc ansible.builtin.apt
```

공식 [Ansible Builtin Collection](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/)에서도 Module별 Parameter와 Example을 확인할 수 있다.

## 3 ) 상태 확인과 File 복사

---

현재 SSH로 접속한 계정을 확인한다. `whoami`는 Shell 기능이 필요하지 않으므로 `command` Module을 사용한다.

```bash
ansible all \
  -m ansible.builtin.command \
  -a "whoami"
```

Managed Node의 Memory 상태도 같은 방식으로 확인한다.

```bash
ansible all \
  -m ansible.builtin.command \
  -a "free -h"
```

각 Host가 실행 결과를 반환하지만 `command` Module은 해당 명령이 상태를 변경하는지 판단할 수 없다. 조회 명령도 기본 결과에 `changed`가 표시될 수 있으므로 Playbook에서는 `changed_when: false`를 지정할 수 있다.

Control Node에서 전송할 File을 만든다.

```bash
touch test.txt
```

`copy` Module로 모든 Managed Node의 `/tmp/test.txt`에 복사한다.

```bash
ansible all \
  -m ansible.builtin.copy \
  -a "src=./test.txt dest=/tmp/test.txt mode=0644"
```

복사된 File의 속성을 확인한다.

```bash
ansible all \
  -m ansible.builtin.command \
  -a "ls -l /tmp/test.txt"
```

같은 `copy` 명령을 다시 실행하면 Source 내용과 Permission이 바뀌지 않았으므로 `changed: false`가 표시된다.

## 4 ) Nginx 설치와 삭제

---

Ubuntu Managed Node의 Package 목록을 갱신하고 Nginx를 설치한다. Package 변경에는 Root 권한이 필요하므로 `-b`를 사용한다.

```bash
ansible all \
  -m ansible.builtin.apt \
  -a "name=nginx state=present update_cache=true" \
  -b
```

`sudo` Password가 필요한 환경에서는 `-K`를 추가한다.

```bash
ansible all \
  -m ansible.builtin.apt \
  -a "name=nginx state=present update_cache=true" \
  -b -K
```

Nginx Package Version과 Service 상태를 확인한다.

```bash
ansible all \
  -m ansible.builtin.command \
  -a "nginx -v"

ansible all \
  -m ansible.builtin.command \
  -a "systemctl is-active nginx"
```

`systemctl status nginx`는 사람이 읽기 좋은 상세 출력을 제공하지만 상태 확인 자동화에는 종료 Code가 명확한 `systemctl is-active nginx`가 간결하다.

Ad-hoc 실습 후 Nginx를 제거하려면 다음 명령을 사용한다.

```bash
ansible all \
  -m ansible.builtin.apt \
  -a "name=nginx state=absent purge=true autoremove=true" \
  -b
```

`state=absent`는 Package를 제거하고 `purge=true`는 Package 설정 File 제거를 요청한다. `autoremove=true`는 더 이상 필요하지 않은 자동 설치 의존성을 정리한다.

## 5 ) Playbook 구조

---

> **Playbook**은 어떤 Host에 어떤 Task를 어떤 순서로 적용할지 YAML로 작성한 자동화 정의이다.

Playbook은 다음 단위로 구성한다.

| 구성 요소 | 역할 |
|---|---|
| Play | 대상 Host Group과 실행 정책을 정의한다. |
| Task | 순서대로 실행할 작업 하나를 정의한다. |
| Module | Task가 호출하는 실제 작업 기능이다. |
| Handler | 다른 Task의 변경 알림을 받았을 때만 실행되는 보조 Task이다. |

Ansible은 Play를 위에서 아래로 처리하고 각 Play의 Task도 작성된 순서대로 실행한다. 기본 Linear Strategy에서는 현재 Task가 대상 Host에서 처리된 뒤 다음 Task로 이동한다.

`ping-test.yml`을 작성한다.

```yaml
---
- name: Verify Ansible connections
  hosts: all
  gather_facts: false

  tasks:
    - name: Check Python and Ansible connection
      ansible.builtin.ping:
```

YAML 문법과 Ansible 구조를 먼저 검사한다.

```bash
ansible-playbook --syntax-check ping-test.yml
```

문법이 정상이라면 Playbook을 실행한다.

```bash
ansible-playbook ping-test.yml
```

## 6 ) File 복사 Playbook

---

반복할 File 배포 작업을 `filecopy.yml`에 작성한다.

```yaml
---
- name: Copy a file from the control node
  hosts: all
  gather_facts: false

  tasks:
    - name: Copy test file to managed nodes
      ansible.builtin.copy:
        src: ./test.txt
        dest: /tmp/test.txt
        owner: ansible
        group: ansible
        mode: "0644"
```

`mode`를 문자열로 작성하면 YAML Parser가 앞자리 `0`이 있는 값을 다른 숫자 형식으로 해석하는 문제를 피할 수 있다.

```bash
ansible-playbook --syntax-check filecopy.yml
ansible-playbook filecopy.yml
```

## 7 ) Directory 생성과 File Download

---

`file` Module로 Directory를 만들고 `get_url` Module로 Apache Tomcat Archive를 Download한다.

```yaml
---
- name: Prepare a Tomcat archive directory
  hosts: all
  gather_facts: false

  tasks:
    - name: Create Tomcat download directory
      ansible.builtin.file:
        path: /tmp/tomcat9
        state: directory
        owner: ansible
        group: ansible
        mode: "0755"

    - name: Download Tomcat archive
      ansible.builtin.get_url:
        url: https://archive.apache.org/dist/tomcat/tomcat-9/v9.0.8/bin/apache-tomcat-9.0.8.tar.gz
        dest: /tmp/tomcat9/apache-tomcat-9.0.8.tar.gz
        mode: "0644"
```

이 URL의 Tomcat 9.0.8은 `get_url` 동작을 확인하기 위한 과거 Archive 예시이다. 실제 운영 설치에는 Apache Tomcat의 현재 지원 Version과 보안 Update 상태를 확인하고 Download File의 Checksum도 함께 검증한다.

## 8 ) Nginx 설정 File 준비

---

Control Node의 Project Directory를 다음처럼 구성한다.

```text
ansible-lab/
├── ansible.cfg
├── inventory.ini
├── files/
│   ├── index.html
│   └── nginx-default.conf
├── ping-test.yml
├── filecopy.yml
├── download-tomcat.yml
├── webservers.yml
└── remove-nginx.yml
```

Nginx가 제공할 `files/index.html`을 작성한다.

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Welcome to Nginx</title>
  </head>
  <body>
    <h1>Nginx configured by Ansible</h1>
  </body>
</html>
```

Ubuntu Nginx의 기본 Site 설정으로 사용할 `files/nginx-default.conf`를 작성한다. Document Root는 `/var/www/html`로 맞춘다.

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    root /var/www/html;
    index index.html index.htm;

    server_name _;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

## 9 ) Nginx 배포 Playbook

---

`webservers.yml`은 Package 설치, 설정 File과 Welcome Page 복사, 설정 검증과 Service 시작을 순서대로 처리한다.

```yaml
---
- name: Configure web servers with Nginx
  hosts: all
  become: true

  tasks:
    - name: Install Nginx
      ansible.builtin.apt:
        name: nginx
        state: present
        update_cache: true

    - name: Copy Nginx default site configuration
      ansible.builtin.copy:
        src: files/nginx-default.conf
        dest: /etc/nginx/sites-available/default
        owner: root
        group: root
        mode: "0644"
      notify: Restart Nginx

    - name: Enable Nginx default site
      ansible.builtin.file:
        src: /etc/nginx/sites-available/default
        dest: /etc/nginx/sites-enabled/default
        state: link
        force: true
      notify: Restart Nginx

    - name: Copy welcome page
      ansible.builtin.copy:
        src: files/index.html
        dest: /var/www/html/index.html
        owner: root
        group: root
        mode: "0644"

    - name: Validate Nginx configuration
      ansible.builtin.command: nginx -t
      changed_when: false

    - name: Ensure Nginx is enabled and running
      ansible.builtin.service:
        name: nginx
        enabled: true
        state: started

  handlers:
    - name: Restart Nginx
      ansible.builtin.service:
        name: nginx
        state: restarted
```

설정 File이나 Symbolic Link가 실제로 변경된 경우에만 `notify`가 Handler를 호출한다. Welcome Page만 바뀌면 Nginx는 정적 File을 다시 읽을 수 있으므로 Service를 재시작하지 않는다.

`nginx -t`가 실패하면 Play가 중단되고 알림을 받은 Handler도 실행되지 않는다. 잘못된 설정으로 Service를 재시작하는 상황을 피할 수 있다.

## 10 ) Playbook 검사와 실행

---

먼저 문법을 검사한다.

```bash
ansible-playbook --syntax-check webservers.yml
```

지원되는 Module에서 예상 변경과 File 차이를 확인한다.

```bash
ansible-playbook --check --diff webservers.yml
```

Check Mode는 모든 Module의 실제 결과를 완전히 재현하지 않는다. 예를 들어 Package가 아직 설치되지 않은 환경에서는 뒤의 Nginx 검증 Task가 실행될 수 없으므로 Preview 결과와 실제 실행을 구분한다.

실제 배포를 실행한다.

```bash
ansible-playbook webservers.yml
```

`sudo` Password가 필요한 환경에서는 `-K`를 추가한다.

```bash
ansible-playbook -K webservers.yml
```

## 11 ) Nginx 배포 검증

---

Control Node에서 Package Version, 설정 문법과 Service 상태를 확인한다.

```bash
ansible all \
  -m ansible.builtin.command \
  -a "nginx -v"

ansible all \
  -m ansible.builtin.command \
  -a "nginx -t"

ansible all \
  -m ansible.builtin.command \
  -a "systemctl is-active nginx"
```

각 Managed Node의 HTTP 응답을 확인한다.

```bash
curl http://192.0.2.11
curl http://192.0.2.12
curl http://192.0.2.13
```

응답에 `Nginx configured by Ansible`이 포함되어야 한다. 다른 Computer에서 확인한다면 Managed Node의 Firewall과 Network에서 TCP 80 Port 접근도 허용되어 있어야 한다.

같은 Playbook을 다시 실행해 불필요한 변경이 없는지 확인한다.

```bash
ansible-playbook webservers.yml
```

두 번째 실행에서는 변경할 상태가 없다면 `changed=0`이 표시된다. `nginx -t` Task는 명령 자체를 다시 실행하지만 `changed_when: false`로 조회 작업임을 명시했기 때문에 변경으로 집계하지 않는다.

## 12 ) Nginx 제거 Playbook

---

`remove-nginx.yml`을 작성한다.

```yaml
---
- name: Remove Nginx from managed nodes
  hosts: all
  become: true

  tasks:
    - name: Stop Nginx before removal
      ansible.builtin.service:
        name: nginx
        state: stopped
      ignore_errors: true

    - name: Remove Nginx packages and configuration
      ansible.builtin.apt:
        name:
          - nginx
          - nginx-common
          - nginx-core
          - nginx-full
        state: absent
        purge: true
        autoremove: true

    - name: Reload systemd manager configuration
      ansible.builtin.systemd_service:
        daemon_reload: true
```

`ignore_errors`는 Nginx가 설치되지 않았거나 Service가 없는 Host에서도 Package 제거 Task까지 진행하기 위한 실습용 처리이다. 오류 원인을 숨길 수 있으므로 운영 Playbook에서는 Service Facts나 조건문으로 존재 여부를 확인하는 방식을 우선한다.

문법을 확인한 뒤 실행한다.

```bash
ansible-playbook --syntax-check remove-nginx.yml
ansible-playbook remove-nginx.yml
```

제거 결과를 확인한다.

```bash
ansible all \
  -m ansible.builtin.command \
  -a "systemctl is-active nginx"
```

Package가 제거됐다면 명령이 실패할 수 있다. 이 결과는 Ansible 연결 실패가 아니라 Nginx Service가 더 이상 존재하지 않거나 실행 중이 아니라는 의미이다.

## 13 ) 문제 해결

---

| 증상 | 확인할 내용 |
|---|---|
| `Missing sudo password` | `-K` 사용 여부 또는 Managed Node의 `sudoers` 정책 |
| `Could not find or access` | `copy.src`가 Control Node의 Playbook 기준 경로에 존재하는지 확인 |
| YAML Syntax Error | 들여쓰기, `:` 뒤 공백과 `--syntax-check` 결과 |
| Nginx 설정 검사 실패 | `nginx-default.conf` 문법과 `nginx -t`의 `stderr` |
| Service 시작 실패 | `systemctl status nginx`와 `journalctl -u nginx` 결과 |
| HTTP 연결 실패 | Service 상태, TCP 80 Firewall, Network 경로와 대상 IP |
| 매번 `changed` 표시 | `command`·`shell` 사용 여부와 `changed_when`, Module의 상태 Parameter |
| 일부 Host만 실패 | Play Recap의 Host별 `failed`, `unreachable`와 해당 Host의 상세 출력 |

Playbook 구조와 실행 방식은 [Ansible Playbook 공식 문서](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_intro.html)에서, 일회성 명령은 [Ad-hoc 명령 공식 문서](https://docs.ansible.com/projects/ansible/latest/command_guide/intro_adhoc.html)에서 확인할 수 있다.

> **최종 정리**
> - Ad-hoc 명령은 하나의 Module을 즉시 실행하는 방식이며 반복 작업과 여러 단계 자동화는 Playbook으로 관리한다.
>
> - `-k`는 SSH Password, `-K`는 Privilege Escalation Password를 요청하고 `-b`는 권한 상승을 활성화한다.
>
> - Shell 기능이 필요하지 않다면 `command`를 사용하고 Package, File과 Service는 목적에 맞는 전용 Module로 상태를 관리한다.
>
> - Playbook은 Play, Task와 Module을 순서대로 실행하며 Handler는 변경 알림이 발생했을 때만 실행한다.
>
> - Nginx 배포는 Package 설치, 설정·Page 복사, 문법 검사, Service 상태와 HTTP 응답을 함께 확인해야 완료된다.
>
> - 같은 Playbook을 다시 실행했을 때 불필요한 변경이 없는지 확인하면 Module의 멱등성과 Task 설계를 검증할 수 있다.

다음 글인 [Ansible 변수와 Vault·Facts·제어문](/cloud-native-60-ansible-variables-vault-facts-control-flow/)에서는 같은 Playbook을 여러 Host와 환경에서 재사용하기 위한 변수, 암호화 Data, Facts, 반복문과 조건문을 구성한다.
