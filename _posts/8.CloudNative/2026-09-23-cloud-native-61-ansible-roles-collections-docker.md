---
title: Ansible Role·Collection과 Docker 자동화
description: Ansible Role의 표준 구조와 Galaxy·Collection의 관계를 이해하고 현재 Docker APT Repository와 community.docker Module로 Container 배포를 자동화한다
date: 2026-09-23
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Ansible
---

[Ansible 변수와 Vault·Facts·제어문](/cloud-native-60-ansible-variables-vault-facts-control-flow/)에서는 변수, Facts, 반복문과 조건문으로 Host별 실행을 제어했다. 이번에는 길어진 Playbook의 Task, 변수, File과 Handler를 표준 Directory 구조의 Role로 분리한다. 외부 Role과 Collection을 관리하는 `ansible-galaxy`를 살펴본 뒤 `community.docker` Collection으로 Docker Container를 배포한다.

## 1 ) Role이 필요한 이유

---

> **Role**은 Task, Handler, 변수, 정적 File과 Template을 정해진 Directory 구조로 묶어 재사용하는 단위이다.

하나의 Playbook에 모든 내용을 넣으면 다른 Project에서 일부 기능만 재사용하기 어렵고 여러 사람이 같은 File을 동시에 수정하게 된다. Role은 Web Server, Database 또는 공통 OS 설정처럼 독립된 책임으로 자동화 내용을 나눈다.

Role을 사용하면 다음과 같은 이점이 있다.

- 관련 Task, Handler와 File을 한 Directory에서 관리한다.

- 기본값과 환경별 Override 값을 분리한다.

- 여러 Playbook에서 같은 구성을 재사용한다.

- Role 단위로 Test, Version과 의존성을 관리한다.

- Ansible Galaxy 또는 내부 Repository를 통해 공유한다.

## 2 ) Role 생성과 Directory 구조

---

Control Node의 Project Root에서 `webserver` Role 골격을 생성한다.

```bash
mkdir -p roles
ansible-galaxy role init roles/webserver
tree roles/webserver
```

주요 Directory의 역할은 다음과 같다.

| 경로 | 역할 |
|---|---|
| `tasks/main.yml` | Role이 수행할 기본 Task |
| `handlers/main.yml` | Role Task가 `notify`하는 Handler |
| `defaults/main.yml` | 다른 변수로 쉽게 Override할 수 있는 낮은 우선순위 기본값 |
| `vars/main.yml` | Role 내부에서 강하게 유지할 높은 우선순위 변수 |
| `files/` | `copy` 등에서 사용하는 정적 File |
| `templates/` | Jinja2 Template File |
| `meta/main.yml` | Role Metadata와 의존 Role |
| `tests/` | Role 동작 확인용 Inventory와 Playbook |

사용하지 않는 Directory는 반드시 유지할 필요가 없다. Role의 `files/`와 `templates/` Resource는 Role Root를 기준으로 찾으므로 `../files/index.html` 같은 상대 경로를 만들 필요가 없다.

## 3 ) Apache Web Server Role 작성

---

이번 Role은 Ubuntu와 Debian 계열 Managed Node에 Apache를 설치하고 정적 Page를 배포한다.

### 3.1 Override 가능한 기본값

`roles/webserver/defaults/main.yml`을 작성한다.

```yaml
---
webserver_title: Apache Web Server
webserver_package: apache2
webserver_service: apache2
webserver_document_root: /var/www/html
webserver_security_config: /etc/apache2/conf-available/security.conf
webserver_index_mode: "0644"
webserver_supported_os_families:
  - Debian
```

사용자가 환경별로 바꿀 가능성이 있는 값은 `defaults`에 둔다. `vars/main.yml`은 우선순위가 높아 Inventory 값으로 바꾸기 어려우므로 반드시 고정해야 하는 값에만 사용한다.

### 3.2 정적 Page

`roles/webserver/files/index.html`을 작성한다.

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Hello from Ansible</title>
  </head>
  <body>
    <h1>Hello! Ansible Role</h1>
  </body>
</html>
```

Host별 값이 들어가야 한다면 정적 `files` 대신 `templates/index.html.j2`와 `ansible.builtin.template` Module을 사용한다.

### 3.3 Task

`roles/webserver/tasks/main.yml`을 작성한다.

{% raw %}
```yaml
---
- name: Verify the managed operating system family
  ansible.builtin.assert:
    that:
      - ansible_facts['os_family'] in webserver_supported_os_families
    fail_msg: >-
      {{ ansible_facts['os_family'] }} is not supported by this role.

- name: Install the web server package
  ansible.builtin.apt:
    name: "{{ webserver_package }}"
    state: present
    update_cache: true
  become: true

- name: Copy the web server index page
  ansible.builtin.copy:
    src: index.html
    dest: "{{ webserver_document_root }}/index.html"
    owner: root
    group: root
    mode: "{{ webserver_index_mode }}"
  become: true

- name: Limit the Apache server signature
  ansible.builtin.lineinfile:
    path: "{{ webserver_security_config }}"
    regexp: '^ServerTokens '
    line: ServerTokens Prod
  become: true
  notify: Restart web server

- name: Ensure the web server is enabled and running
  ansible.builtin.service:
    name: "{{ webserver_service }}"
    enabled: true
    state: started
  become: true
```
{% endraw %}

`state: latest`는 Repository의 새 Version이 공개될 때마다 Package를 변경할 수 있다. 재현 가능한 기본 구성에는 `present`를 사용하고 Upgrade는 별도 절차로 관리한다.

### 3.4 Handler

`roles/webserver/handlers/main.yml`을 작성한다.

{% raw %}
```yaml
---
- name: Restart web server
  ansible.builtin.service:
    name: "{{ webserver_service }}"
    state: restarted
  become: true
```
{% endraw %}

### 3.5 Role 호출

`role-example.yml`에서 `import_role`로 정적으로 불러온다.

```yaml
---
- name: Configure web servers with a role
  hosts: lab

  tasks:
    - name: Print the start of the role play
      ansible.builtin.debug:
        msg: Start the webserver role.

    - name: Import the webserver role
      ansible.builtin.import_role:
        name: webserver
```

문법과 예상 변경을 확인한 뒤 실행한다.

```bash
ansible-playbook --syntax-check role-example.yml
ansible-playbook --check --diff role-example.yml
ansible-playbook role-example.yml
```

Role을 찾지 못하면 Project의 `ansible.cfg`에 Search Path를 지정한다.

```ini
[defaults]
inventory = ./inventory.ini
roles_path = ./roles
```

## 4 ) Ansible Galaxy의 Role 관리

---

> **Ansible Galaxy**는 Role과 Collection을 검색하고 배포하는 공개 Service이다.

Role 관련 명령을 확인한다.

```bash
ansible-galaxy role --help
```

PostgreSQL Role을 검색하고 선택한 Role의 Metadata를 확인하는 기본 흐름은 다음과 같다.

```bash
ansible-galaxy role search postgresql --platforms Ubuntu
ansible-galaxy role info <namespace.role_name>
ansible-galaxy role install -p roles <namespace.role_name>
ansible-galaxy role list -p roles
```

자료에서 사용한 `buluma.postgres`는 Galaxy 명령 흐름을 확인하기 위한 특정 시점의 예시이다. Role의 존재 여부, 최신 Release, 지원 OS와 유지보수 상태는 바뀔 수 있으므로 설치 전에 다시 검색한다.

```bash
ansible-galaxy role info buluma.postgres
```

더 이상 사용하지 않는 Role을 Project Directory에서 제거한다.

```bash
ansible-galaxy role remove <namespace.role_name>
```

Galaxy에 공개됐다는 사실만으로 Code의 보안과 품질이 검증됐다고 판단할 수 없다. 설치 전에 Source Repository, License, Release 이력, 지원 Platform, 의존 Role과 Task가 수행하는 Privileged 작업을 확인한다.

## 5 ) Content Collection

---

> **Collection**은 Module, Plugin, Role, Playbook과 문서를 Namespace 단위로 묶어 Ansible Core와 독립적으로 배포하는 형식이다.

초기의 Ansible은 많은 Module을 Core Package와 함께 배포했다. Collection은 Core Release와 Module·Plugin Release를 분리하고 필요한 Version을 Project별로 선택할 수 있게 한다.

`ansible.builtin.copy`는 Builtin Collection의 FQCN이고 `community.docker.docker_container`는 `community.docker` Collection의 Module이다.

설치된 Collection을 확인한다.

```bash
ansible-galaxy collection list
ansible-doc community.docker.docker_container
```

`community.docker`가 없다면 설치한다.

```bash
ansible-galaxy collection install community.docker
```

Project에서 의존성을 재현하려면 검증한 Version을 `requirements.yml`에 기록한다.

```yaml
---
collections:
  - name: community.docker
    version: "<VERIFIED-VERSION>"
```

Placeholder를 설치 시점에 검증한 실제 Version으로 바꾼 뒤 실행한다.

```bash
ansible-galaxy collection install -r requirements.yml
ansible-galaxy collection list community.docker
```

Collection을 Offline 환경으로 전달해야 한다면 의존성을 포함한 Artifact와 생성된 `requirements.yml`을 Download할 수 있다.

```bash
mkdir -p collection-bundle
ansible-galaxy collection download \
  -p collection-bundle \
  community.docker
```

## 6 ) Docker 설치 자동화 준비

---

Docker 설치는 `docker_hosts` Inventory Group에만 적용한다.

```ini
[docker_hosts]
master
worker1
worker2
```

Docker의 현재 Ubuntu 설치 문서는 One-line `docker.list`보다 DEB822 형식의 `/etc/apt/sources.list.d/docker.sources`를 안내한다. 배포판 Codename과 Architecture를 고정 문자열로 넣지 않고 Managed Node에서 확인한다.

`install-docker.yml`을 작성한다.

{% raw %}
```yaml
---
- name: Install Docker Engine from the official repository
  hosts: docker_hosts
  become: true

  tasks:
    - name: Install repository prerequisites
      ansible.builtin.apt:
        name:
          - ca-certificates
          - curl
        state: present
        update_cache: true

    - name: Create the APT keyring directory
      ansible.builtin.file:
        path: /etc/apt/keyrings
        state: directory
        owner: root
        group: root
        mode: "0755"

    - name: Download the Docker repository signing key
      ansible.builtin.get_url:
        url: https://download.docker.com/linux/ubuntu/gpg
        dest: /etc/apt/keyrings/docker.asc
        owner: root
        group: root
        mode: "0644"

    - name: Read the Debian package architecture
      ansible.builtin.command: dpkg --print-architecture
      register: docker_dpkg_architecture
      changed_when: false

    - name: Configure the Docker DEB822 repository
      ansible.builtin.copy:
        dest: /etc/apt/sources.list.d/docker.sources
        owner: root
        group: root
        mode: "0644"
        content: |
          Types: deb
          URIs: https://download.docker.com/linux/ubuntu
          Suites: {{ ansible_facts['distribution_release'] }}
          Components: stable
          Architectures: {{ docker_dpkg_architecture.stdout }}
          Signed-By: /etc/apt/keyrings/docker.asc

    - name: Install Docker Engine packages
      ansible.builtin.apt:
        name:
          - docker-ce
          - docker-ce-cli
          - containerd.io
          - docker-buildx-plugin
          - docker-compose-plugin
          - python3-requests
        state: present
        update_cache: true

    - name: Ensure Docker is enabled and running
      ansible.builtin.service:
        name: docker
        enabled: true
        state: started
```
{% endraw %}

자료의 `docker-ce-li`는 `docker-ce-cli`의 오탈자이다. 또한 Ubuntu `noble`, `amd64`를 고정하면 다른 Ubuntu Release와 ARM64 Host에서 실패하므로 Facts와 `dpkg` 결과를 사용했다.

자료의 Container 예제는 `python3-docker`를 설치했지만 현재 `community.docker`의 해당 Module은 Docker SDK for Python을 직접 사용하지 않고 `requests`를 요구한다. 설치한 Collection Version의 공식 Requirements를 확인하고 이 예제에서는 Managed Node에 `python3-requests`를 설치한다.

문법을 검사하고 실행한다.

```bash
ansible-playbook --syntax-check install-docker.yml
ansible-playbook --check --diff install-docker.yml
ansible-playbook install-docker.yml -K
```

Check Mode에서는 APT Repository가 아직 생성되지 않아 뒤의 Package 설치 결과를 완전히 예측하지 못할 수 있다.

설치 결과를 확인한다.

```bash
ansible docker_hosts \
  -m ansible.builtin.command \
  -a "docker --version"

ansible docker_hosts \
  -m ansible.builtin.command \
  -a "systemctl is-active docker"
```

현재 Docker Ubuntu Repository 형식과 Package 목록은 [Docker Engine Ubuntu 설치 문서](https://docs.docker.com/engine/install/ubuntu/)에서 확인한다.

## 7 ) Nginx Container 배포

---

자료의 `community.gerneral`은 존재하지 않는 오탈자이다. Docker Resource는 `community.docker` Collection의 FQCN을 사용한다. `nginx-latest`도 Docker Hub의 일반적인 Tag 표기인 `nginx:latest`로 수정한다.

`deploy-docker.yml`을 작성한다.

{% raw %}
```yaml
---
- name: Deploy an Nginx container
  hosts: docker_hosts
  become: true
  vars:
    container_name: my-web-server
    image_name: nginx:latest
    host_port: 8080
    container_port: 80

  tasks:
    - name: Pull the Nginx image
      community.docker.docker_image_pull:
        name: "{{ image_name }}"

    - name: Create and start the Nginx container
      community.docker.docker_container:
        name: "{{ container_name }}"
        image: "{{ image_name }}"
        state: started
        restart_policy: always
        published_ports:
          - "{{ host_port }}:{{ container_port }}"
        env:
          MY_ENV_VAR: hello-ansible

    - name: Print the published endpoint
      ansible.builtin.debug:
        msg: >-
          {{ inventory_hostname }} exposes {{ container_name }}
          on TCP {{ host_port }}.
```
{% endraw %}

과거 예제에서 `community.docker.docker_image`로 Image를 Pull할 수 있었고 현재도 지원되지만, 현재 Collection 문서는 Pull 전용 작업에 `community.docker.docker_image_pull` 사용을 권장한다. 설치한 Collection Version의 요구 Package와 Parameter는 `ansible-doc`으로 확인한다.

```bash
ansible-doc community.docker.docker_image_pull
ansible-doc community.docker.docker_container
ansible-playbook --syntax-check deploy-docker.yml
ansible-playbook deploy-docker.yml -K
```

Container와 HTTP 응답을 확인한다.

```bash
ansible docker_hosts \
  -m ansible.builtin.command \
  -a "docker ps --filter name=my-web-server"

curl http://192.0.2.11:8080
curl http://192.0.2.12:8080
curl http://192.0.2.13:8080
```

다른 Computer에서 접속한다면 Managed Node의 Firewall과 Network에서 TCP 8080 접근이 허용되어 있어야 한다.

## 8 ) 문제 해결

---

| 증상 | 확인할 내용 |
|---|---|
| Role을 찾지 못함 | `roles/` 위치와 `roles_path` |
| Role 변수 Override가 적용되지 않음 | 값이 `defaults`가 아니라 우선순위가 높은 `vars`에 있는지 확인 |
| Collection Module을 찾지 못함 | `ansible-galaxy collection list`, `requirements.yml` 설치 여부 |
| Docker APT 서명 오류 | `docker.asc` Permission과 `Signed-By` 경로 |
| Docker Package를 찾지 못함 | Ubuntu Codename, Architecture와 `apt update` 결과 |
| Docker Socket 권한 오류 | `become` 사용 여부와 `/var/run/docker.sock` Permission |
| Container Module Parameter 오류 | 설치된 Collection Version의 `ansible-doc` 결과 |
| TCP 8080 접속 실패 | Container Port Mapping, Host Firewall과 Network 경로 |
| 모든 Host에서 Container가 생성됨 | `hosts: docker_hosts` Group과 `--list-hosts` 결과 |

Role 구조는 [Ansible Roles](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_reuse_roles.html), Collection Module은 [Community.Docker](https://docs.ansible.com/projects/ansible/latest/collections/community/docker/index.html)과 [docker_container Module](https://docs.ansible.com/projects/ansible/latest/collections/community/docker/docker_container_module.html)에서 확인할 수 있다.

> **최종 정리**
> - Role은 Task, Handler, 변수와 File을 표준 Directory 구조로 묶어 Playbook을 재사용한다.
>
> - `defaults`는 쉽게 Override할 값, `vars`는 높은 우선순위가 필요한 내부 값에 제한해 사용한다.
>
> - Galaxy의 공개 Role은 설치 전에 Source, 지원 Platform, Version과 Privileged 작업을 검토한다.
>
> - Collection은 Module과 Plugin을 Core와 독립적으로 배포하며 Playbook에서는 FQCN을 사용한다.
>
> - Docker 설치는 현재 DEB822 Repository 형식과 실제 Architecture를 사용하고 Container는 `community.docker` Module로 원하는 상태를 관리한다.
>
> - Container 제거, Docker Package 제거와 전체 Data 삭제는 영향 범위가 다르므로 별도 절차로 분리한다.
