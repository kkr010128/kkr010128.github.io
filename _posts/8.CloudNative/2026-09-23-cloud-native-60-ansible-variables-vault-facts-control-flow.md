---
title: Ansible 변수와 Vault·Facts·제어문
description: Ansible 변수의 범위와 우선순위를 구분하고 Vault, Facts, 반복문, 조건문, Handler와 실패 처리를 이용해 재사용 가능한 Playbook을 작성한다
date: 2026-09-23
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Ansible
---

[Ansible Ad-hoc 명령과 Playbook으로 Nginx 자동화](/cloud-native-59-ansible-adhoc-playbook-nginx/)에서는 반복 가능한 Nginx 배포 절차를 Playbook으로 작성했다. 이번에는 Host와 환경마다 달라지는 값을 변수로 분리하고, Managed Node에서 수집한 Facts와 이전 Task의 결과를 이용해 실행 대상을 판단한다. 비밀 값은 Ansible Vault로 암호화하고 상태 변경이 발생했을 때만 Handler를 호출한다.

## 1 ) 변수의 역할과 이름

---

> **변수**는 사용자, Package, Service, File 경로처럼 Host나 환경에 따라 달라지는 값을 이름으로 저장한 것이다.

같은 값을 Task마다 직접 적으면 환경이 바뀔 때 여러 위치를 수정해야 한다. 변수를 사용하면 Playbook의 작업 구조는 유지하면서 입력 값만 바꿀 수 있다.

변수 이름은 문자, 숫자와 밑줄로 구성하며 숫자로 시작할 수 없다. Python이나 Ansible이 내부에서 사용하는 이름은 피한다.

| 이름 | 판단 | 이유 |
|---|---|---|
| `web_package` | 사용 가능 | 의미가 분명하고 영문자와 밑줄만 사용한다. |
| `web-package` | 사용하지 않음 | 하이픈은 식별자에서 빼기 연산자로 해석될 수 있다. |
| `1st_user` | 사용 불가 | 숫자로 시작한다. |
| `environment` | 사용하지 않음 | Ansible에서 특별한 의미를 가지는 예약 이름이다. |

변수는 Jinja2 표현식으로 참조한다. 값 전체가 변수라면 YAML 문자열로 감싸는 것이 안전하다.

{% raw %}
```yaml
ansible.builtin.user:
  name: "{{ managed_user }}"
  state: present
```
{% endraw %}

## 2 ) 변수의 정의 위치와 범위

---

변수는 Inventory, Playbook, 외부 File, Role과 실행 명령에서 정의할 수 있다.

| 종류 | 정의 위치 | 적용 범위 | 일반적인 용도 |
|---|---|---|---|
| Group 변수 | Inventory의 Group 또는 `group_vars/` | Group에 속한 Host | 공통 Package, Port와 계정 |
| Host 변수 | Inventory의 Host 또는 `host_vars/` | 특정 Host | Host별 IP, 장치명과 예외 값 |
| Play 변수 | Play의 `vars` | 해당 Play | Play 안에서만 사용하는 값 |
| 외부 변수 | `vars_files` | 불러온 Play | 환경별 변수 File 분리 |
| 추가 변수 | `--extra-vars`, `-e` | 실행 시 전달 | 일회성 Override |
| 등록 변수 | Task의 `register` | 해당 Host의 현재 실행 | 이전 Task 결과를 후속 Task에서 사용 |

같은 이름이 여러 위치에 있으면 우선순위가 높은 값이 낮은 값을 덮어쓴다. 전체 우선순위에는 많은 단계가 있지만 이번 범위에서는 다음 관계를 먼저 기억한다.

```text
Role defaults
  < Inventory Group 변수
  < Inventory Host 변수
  < Play vars·vars_files
  < Role vars
  < Task·등록 변수
  < Extra vars
```

`-e`로 전달한 Extra vars는 변수 중 가장 높은 우선순위를 가진다. 우선순위에 의존해 같은 이름을 여러 위치에서 반복 정의하기보다 값의 성격에 맞는 한 위치를 정하는 것이 좋다.

## 3 ) Group 변수와 Host 변수

---

간단한 실습에서는 `inventory.ini` 안에 변수를 함께 작성할 수 있다.

```ini
[lab]
master ansible_host=192.0.2.11 managed_user=ansible-master
worker1 ansible_host=192.0.2.12
worker2 ansible_host=192.0.2.13

[lab:vars]
managed_user=ansible
```

`master`는 Host 변수의 `managed_user=ansible-master`가 Group 변수보다 우선한다. `worker1`과 `worker2`는 Group 값인 `ansible`을 사용한다.

Project가 커지면 Inventory의 연결 정보와 일반 변수를 분리한다.

```text
ansible-lab/
├── ansible.cfg
├── inventory.ini
├── group_vars/
│   └── lab.yml
└── host_vars/
    └── master.yml
```

`group_vars/lab.yml`을 작성한다.

```yaml
---
managed_user: ansible
```

`host_vars/master.yml`에서 `master`만 Override한다.

```yaml
---
managed_user: ansible-master
```

변수가 Host별로 어떻게 해석되는지 확인한다.

```bash
ansible-inventory --host master
ansible-inventory --host worker1
```

## 4 ) Play 변수와 외부 변수 File

---

Play 안에서만 사용할 값은 `vars`에 정의한다.

{% raw %}
```yaml
---
- name: Create a managed user
  hosts: lab
  vars:
    managed_user: ansible2

  tasks:
    - name: Ensure the managed user exists
      ansible.builtin.user:
        name: "{{ managed_user }}"
        state: present
      become: true
```
{% endraw %}

여러 Playbook이 같은 값을 사용하면 `vars/users.yml`로 분리한다.

```yaml
---
managed_user: ansible4
```

Play에서 `vars_files`로 불러온다.

{% raw %}
```yaml
---
- name: Create a user from an external variable file
  hosts: lab
  vars_files:
    - vars/users.yml

  tasks:
    - name: Ensure the managed user exists
      ansible.builtin.user:
        name: "{{ managed_user }}"
        state: present
      become: true
```
{% endraw %}

실행할 때만 값을 바꾸려면 Extra vars를 전달한다.

```bash
ansible-playbook \
  -e "managed_user=ansible5" \
  create-user.yml
```

Extra vars는 기존 값을 강제로 덮어쓰므로 자동화 Script에서 무분별하게 사용하면 실제 값의 출처를 추적하기 어렵다.

## 5 ) Task 결과를 등록 변수로 사용

---

`register`는 Task의 Return Data를 Host별 변수에 저장한다. 등록 변수는 현재 Playbook 실행 중 후속 Task에서 사용할 수 있으며 다음 실행까지 영구 보존되지 않는다.

{% raw %}
```yaml
---
- name: Inspect a service result
  hosts: lab
  gather_facts: false

  tasks:
    - name: Check whether rsyslog is active
      ansible.builtin.command: systemctl is-active rsyslog
      register: rsyslog_status
      changed_when: false
      failed_when: false

    - name: Print the registered result
      ansible.builtin.debug:
        var: rsyslog_status

    - name: Print active status only
      ansible.builtin.debug:
        msg: "Rsyslog is active on {{ inventory_hostname }}"
      when: rsyslog_status.rc == 0
```
{% endraw %}

`command` Module은 조회 명령도 기본적으로 변경으로 판단할 수 있으므로 `changed_when: false`를 지정했다. `systemctl is-active`의 Non-zero Exit Code도 결과로 비교하기 위해 `failed_when: false`를 사용했다.

주요 Return 값은 다음과 같다.

| 값 | 의미 |
|---|---|
| `rc` | 명령의 Exit Code |
| `stdout` | 표준 출력 |
| `stderr` | 표준 오류 |
| `changed` | 상태 변경 여부 |
| `failed` | Task 실패 여부 |

## 6 ) Ansible Vault

---

> **Ansible Vault**는 Password, API Key와 같은 변수를 File 또는 문자열 단위로 암호화하여 평문 노출을 줄이는 기능이다.

Vault는 저장된 Data만 보호한다. Playbook 실행 중 복호화된 값이 Module 출력이나 Log에 표시되는 문제까지 자동으로 막지는 않는다. Secret을 사용하는 Task에는 필요에 따라 `no_log: true`를 설정한다.

### 6.1 암호화 변수 File 생성

Control Node에서 `vars/secrets.yml`을 생성한다.

```bash
mkdir -p vars
ansible-vault create \
  --vault-id lab@prompt \
  vars/secrets.yml
```

Editor에 다음 구조로 입력한다. 실제 Password를 문서나 Repository에 작성하지 않는다. Linux `user` Module의 `password`에는 평문 Password가 아니라 대상 OS가 이해하는 Password Hash가 필요하다.

```yaml
---
vault_user_name: itstudy
vault_user_password_hash: "<PASSWORD-HASH>"
```

암호화된 File은 `$ANSIBLE_VAULT` Header와 Ciphertext로 보인다.

```bash
head -n 1 vars/secrets.yml
ansible-vault view \
  --vault-id lab@prompt \
  vars/secrets.yml
```

내용을 수정할 때는 평문 File로 복호화해 방치하지 않고 `edit`을 사용한다.

```bash
ansible-vault edit \
  --vault-id lab@prompt \
  vars/secrets.yml
```

기존 File은 `encrypt`, 암호가 노출되었거나 교체 주기가 되면 `rekey`로 다시 암호화할 수 있다.

```bash
ansible-vault encrypt --vault-id lab@prompt vars/existing-secret.yml
ansible-vault rekey vars/secrets.yml
```

### 6.2 Vault 변수 사용

{% raw %}
```yaml
---
- name: Create a user with vaulted data
  hosts: lab
  vars_files:
    - vars/secrets.yml

  tasks:
    - name: Ensure the vaulted user exists
      ansible.builtin.user:
        name: "{{ vault_user_name }}"
        password: "{{ vault_user_password_hash }}"
        state: present
      become: true
      no_log: true
```
{% endraw %}

실행할 때 같은 Vault ID와 Password를 제공한다.

```bash
ansible-playbook \
  --vault-id lab@prompt \
  create-vault-user.yml
```

Vault Password File을 사용할 수도 있지만 그 File 자체가 복호화 Key이다. Repository나 일반 공유 Directory에 두지 않고 최소 Permission과 별도 Secret Manager를 사용한다.

## 7 ) Facts

---

> **Facts**는 Ansible이 Managed Node에서 자동으로 수집한 Hostname, OS, Kernel, CPU, Memory, Network와 Storage 정보이다.

Play의 `gather_facts` 기본값은 `true`이다. Facts가 필요 없는 단순 작업은 `false`로 설정해 시작 시간을 줄일 수 있다.

Ad-hoc 명령으로 전체 Facts를 확인한다.

```bash
ansible lab -m ansible.builtin.setup
```

Playbook에서 필요한 일부 값만 출력한다.

{% raw %}
```yaml
---
- name: Print selected facts
  hosts: lab

  tasks:
    - name: Print host and network facts
      ansible.builtin.debug:
        msg: >-
          {{ inventory_hostname }} runs
          {{ ansible_facts['distribution'] }}
          {{ ansible_facts['distribution_version'] }} and its default IPv4
          address is {{ ansible_facts['default_ipv4']['address'] }}.
```
{% endraw %}

`inventory_hostname`은 Inventory에서 정한 이름이고 `ansible_facts['hostname']`은 Managed Node OS가 보고한 Hostname이다. 두 값은 같지 않을 수 있다.

Facts 수집에 실패하면 SSH 연결뿐 아니라 Managed Node의 Python과 `setup` Module 실행 조건을 확인한다.

### 사용자 지정 Local Facts

Managed Node의 `/etc/ansible/facts.d`에 `.fact` File을 두면 `ansible_local` Namespace에서 읽을 수 있다. 다음 작업은 Managed Node에 INI 형식의 Local Fact를 배포한다.

```yaml
---
- name: Install a local fact
  hosts: lab
  become: true

  tasks:
    - name: Create the local facts directory
      ansible.builtin.file:
        path: /etc/ansible/facts.d
        state: directory
        mode: "0755"

    - name: Write package local facts
      ansible.builtin.copy:
        dest: /etc/ansible/facts.d/packages.fact
        mode: "0644"
        content: |
          [packages]
          web_package=nginx
          db_package=mariadb-server

    - name: Gather facts again
      ansible.builtin.setup:
```

다시 수집한 값은 `ansible_local['packages']['packages']['web_package']`와 같은 구조로 접근한다. Local Fact의 File 이름과 INI Section이 각각 중첩 Key가 된다.

## 8 ) 반복문

---

같은 Module을 여러 값에 적용할 때 `loop`를 사용한다.

{% raw %}
```yaml
---
- name: Ensure required services are running
  hosts: lab
  become: true
  vars:
    required_services:
      - ssh
      - rsyslog

  tasks:
    - name: Start required services
      ansible.builtin.service:
        name: "{{ item }}"
        state: started
      loop: "{{ required_services }}"
```
{% endraw %}

여러 속성을 함께 반복하려면 Dictionary 목록을 사용한다.

{% raw %}
```yaml
- name: Create log files
  ansible.builtin.file:
    path: "{{ item.path }}"
    state: touch
    mode: "{{ item.mode }}"
  loop:
    - path: /var/log/test1.log
      mode: "0644"
    - path: /var/log/test2.log
      mode: "0600"
  become: true
```
{% endraw %}

반복 Task에 `register`를 사용하면 각 반복 결과가 `results` 목록에 저장된다.

{% raw %}
```yaml
- name: Check service states
  ansible.builtin.command: "systemctl is-active {{ item }}"
  loop:
    - ssh
    - rsyslog
  register: service_checks
  changed_when: false
  failed_when: false

- name: Print each service result
  ansible.builtin.debug:
    msg: "{{ item.item }}: {{ item.stdout }}"
  loop: "{{ service_checks.results }}"
```
{% endraw %}

## 9 ) 조건문

---

`when`은 Boolean, Facts, 등록 변수와 반복 항목을 평가해 Task 실행 여부를 결정한다. 조건식 자체에는 Jinja2 이중 중괄호를 사용하지 않는다.

{% raw %}
```yaml
- name: Print the package manager family
  ansible.builtin.debug:
    msg: "Use apt on {{ inventory_hostname }}"
  when: ansible_facts['os_family'] == 'Debian'
```
{% endraw %}

목록으로 작성한 여러 조건은 모두 참이어야 한다.

```yaml
- name: Print supported Ubuntu version
  ansible.builtin.debug:
    msg: This host uses a supported Ubuntu release.
  when:
    - ansible_facts['distribution'] == 'Ubuntu'
    - ansible_facts['distribution_major_version'] | int >= 22
```

반복문과 조건문을 함께 사용해 Root Mount만 선택할 수 있다.

{% raw %}
```yaml
- name: Print root filesystem free space
  ansible.builtin.debug:
    msg: "Root free space is {{ item.size_available }} bytes"
  loop: "{{ ansible_facts['mounts'] }}"
  when: item.mount == '/'
```
{% endraw %}

Facts를 조건에 사용할 때 `gather_facts: false`를 설정하면 값이 존재하지 않을 수 있다. Facts Cache를 별도로 구성하지 않았다면 해당 Play에서 Facts를 수집한다.

## 10 ) Handler와 변경 알림

---

> **Handler**는 Task가 실제 변경을 만들고 `notify`한 경우에만 실행되는 특수 Task이다.

여러 Task가 같은 Handler를 알리더라도 기본적으로 Play의 해당 실행 지점에서 한 번만 처리한다. 설정 File이 변경되지 않으면 Service를 불필요하게 재시작하지 않는다.

{% raw %}
```yaml
---
- name: Manage rsyslog configuration
  hosts: lab
  become: true

  tasks:
    - name: Deploy rsyslog configuration
      ansible.builtin.copy:
        src: files/50-lab.conf
        dest: /etc/rsyslog.d/50-lab.conf
        owner: root
        group: root
        mode: "0644"
      notify: Restart rsyslog

  handlers:
    - name: Restart rsyslog
      ansible.builtin.service:
        name: rsyslog
        state: restarted
```
{% endraw %}

Handler 이름은 Play 범위에서 고유하게 작성한다. 중간에 즉시 실행해야 하는 특별한 이유가 없다면 기본 실행 시점을 유지한다.

## 11 ) 실패 처리

---

Task가 실패하면 Ansible은 기본적으로 해당 Host의 뒤 Task를 중단하고 다른 Host는 계속 처리한다.

`ignore_errors: true`는 실행된 Task가 `failed` 결과를 반환해도 다음 Task로 진행한다. Undefined Variable, 문법 오류와 `unreachable` 상태까지 무시하는 기능은 아니다.

```yaml
- name: Run an optional validation command
  ansible.builtin.command: /usr/local/bin/optional-check
  register: optional_check
  changed_when: false
  failed_when: false
```

예상 가능한 Non-zero Exit Code라면 모든 오류를 무시하기보다 `failed_when`으로 성공과 실패의 의미를 정의한다.

설정 File을 변경해 Handler가 알림을 받은 뒤 후속 Task가 실패하면 기본적으로 그 Host의 Handler가 실행되지 않을 수 있다. 실패한 Host에서도 이미 알림을 받은 Handler를 실행해야 한다면 Play에 `force_handlers: true`를 설정하거나 `--force-handlers`를 사용한다.

```yaml
---
- name: Apply configuration with forced handlers
  hosts: lab
  force_handlers: true

  tasks:
    - name: Explain force handler policy
      ansible.builtin.debug:
        msg: Notified handlers run even if a later task fails.
```

`force_handlers`도 Host가 `unreachable` 상태가 되는 문제까지 해결하지는 않는다.

## 12 ) 검사와 실행

---

변수와 조건을 추가한 뒤에는 선택되는 Host와 문법을 먼저 확인한다.

```bash
ansible-inventory --graph
ansible-playbook --syntax-check playbook.yml
ansible-playbook --check --diff playbook.yml
ansible-playbook playbook.yml
```

Check Mode는 외부 명령과 일부 Module의 실제 결과를 완전히 재현하지 않는다. 실제 실행 후 Play Recap의 `ok`, `changed`, `failed`, `unreachable`, `skipped`, `rescued`, `ignored`를 Host별로 확인한다.

공식 문서는 [변수](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_variables.html), [Facts](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_vars_facts.html), [Vault](https://docs.ansible.com/projects/ansible/latest/vault_guide/vault.html), [Handler](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_handlers.html)와 [실패 처리](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_error_handling.html)에서 확인할 수 있다.

> **최종 정리**
> - Group·Host·Play·외부·추가 변수는 적용 범위와 우선순위가 다르며 Extra vars는 기존 변수를 강제로 덮어쓴다.
>
> - `register`는 현재 실행의 Host별 Task 결과를 저장하고 Facts는 Managed Node에서 수집한 System 정보를 제공한다.
>
> - Vault는 저장 Data를 암호화하지만 실행 중 출력까지 보호하지 않으므로 Secret Task의 Log도 통제해야 한다.
>
> - `loop`는 같은 작업을 여러 값에 적용하고 `when`은 Facts와 이전 결과에 따라 Task를 선택한다.
>
> - Handler는 실제 변경 알림이 있을 때만 실행하며 실패를 무시하기보다 `failed_when`으로 기대하는 결과를 정의한다.

다음 글인 [Ansible Role·Collection과 Docker 자동화](/cloud-native-61-ansible-roles-collections-docker/)에서는 관련 Task, File, 변수와 Handler를 Role로 묶고 Collection Module로 Docker Container를 관리한다.
