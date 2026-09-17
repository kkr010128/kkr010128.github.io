---
title: Docker로 GitLab CE 설치와 운영 준비
description: GitLab CE를 Docker Container로 설치하고 Memory·Swap, Port, Volume, 초기 Password와 운영 점검 항목을 정리한다
date: 2026-09-17
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - GitLab
---

[GitHub Actions Workflow와 CI/CD 실습](/cloud-native-46-github-actions-ci/)에서는 GitHub Repository의 Event를 기준으로 Test, Image Build와 SSH 배포를 자동화했다. GitLab CE는 Source Repository, Merge Request와 CI/CD 기능을 직접 운영할 수 있는 Git Server이다. 이 글에서는 Linux Server에 GitLab CE를 Docker Container로 구성하고 지속적으로 유지할 Data와 운영 확인 항목을 정리한다.

## 1 ) GitLab Server Resource 준비

---

GitLab은 Web Application, Background Job, PostgreSQL, Redis와 Repository Storage 등 여러 Component를 함께 실행한다. 작은 실습 환경이라도 Memory를 넉넉하게 할당하고 Host Disk의 여유 공간을 먼저 확인한다.

```bash
free -h
df -h
nproc
```

| Resource | 실습 환경에서 확인할 내용 |
|---|---|
| Memory | 최소 4GiB 이상을 확보하고 실제 사용량을 관찰 |
| Swap | Memory가 일시적으로 부족할 때 Process 종료 가능성을 낮추는 보조 공간 |
| Disk | Repository, Artifact, Container Registry와 Log 증가량 고려 |
| CPU | 초기 설정과 Upgrade 중 사용량 증가 고려 |

Swap은 Memory를 대체하지 않는다. Disk I/O를 사용하므로 지속적으로 Swap을 사용한다면 Memory 증설이나 GitLab Component 조정이 필요하다.

## 2 ) Swap File 생성

---

4GiB Swap File을 만든다. `fallocate`를 지원하지 않는 File System에서는 `dd`를 사용할 수 있다.

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

생성 결과를 확인한다.

```bash
swapon --show
free -h
```

재부팅 후에도 활성화하려면 `/etc/fstab`에 다음 항목을 한 번만 추가한다.

```text
/swapfile none swap sw 0 0
```

추가 후 문법과 Mount 가능 여부를 확인한다.

```bash
sudo mount -a
swapon --show
```

`/etc/fstab`을 잘못 작성하면 Boot 과정에 영향을 줄 수 있으므로 기존 내용을 Backup하고 중복 항목이 없는지 확인한다.

## 3 ) GitLab Data Directory

---

Container를 삭제하거나 교체해도 설정과 Repository가 유지되도록 Host Directory를 준비한다.

```bash
sudo mkdir -p \
  /srv/gitlab/config \
  /srv/gitlab/logs \
  /srv/gitlab/data
```

| Host Directory | Container Directory | 저장 내용 |
|---|---|---|
| `/srv/gitlab/config` | `/etc/gitlab` | `gitlab.rb`, 인증서와 설정 |
| `/srv/gitlab/logs` | `/var/log/gitlab` | GitLab Component Log |
| `/srv/gitlab/data` | `/var/opt/gitlab` | Repository, Database와 Application Data |

세 Directory는 Backup 대상이다. Image만 보관해서는 GitLab Repository와 설정을 복구할 수 없다.

## 4 ) GitLab CE Container 실행

---

운영 환경에서는 `latest` 대신 검증한 GitLab Version Tag를 고정한다. 사용할 Version은 [GitLab Docker 설치 문서](https://docs.gitlab.com/install/docker/installation/)와 Container Registry의 CE Tag에서 확인한다.

다음 예제에서 Hostname과 Version을 실제 환경 값으로 바꾼다.

```bash
export GITLAB_HOSTNAME='gitlab.example.com'
export GITLAB_VERSION='<major.minor.patch>-ce.0'

sudo docker run --detach \
  --hostname "$GITLAB_HOSTNAME" \
  --env GITLAB_OMNIBUS_CONFIG="external_url 'https://$GITLAB_HOSTNAME'; gitlab_rails['gitlab_shell_ssh_port'] = 2222" \
  --publish 443:443 \
  --publish 80:80 \
  --publish 2222:22 \
  --name gitlab \
  --restart always \
  --volume /srv/gitlab/config:/etc/gitlab \
  --volume /srv/gitlab/logs:/var/log/gitlab \
  --volume /srv/gitlab/data:/var/opt/gitlab \
  --shm-size 256m \
  "gitlab/gitlab-ce:$GITLAB_VERSION"
```

| Option | 역할 |
|---|---|
| `--hostname` | GitLab이 Link와 Clone URL 생성에 사용할 DNS 이름 |
| `external_url` | 사용자가 접속할 외부 URL |
| `gitlab_shell_ssh_port` | SSH Clone URL에 표시할 외부 Port |
| `--publish 2222:22` | Host `2222`를 Container SSH `22`에 연결 |
| `--restart always` | Docker Daemon 시작 후 GitLab 자동 복구 |
| `--shm-size 256m` | Prometheus Metric 등에 사용하는 Shared Memory 확대 |

Host SSH Server가 이미 Port `22`를 사용하므로 GitLab SSH는 `2222` 같은 별도 Port에 연결한다. Firewall이나 Cloud Security Group에서도 실제로 사용할 HTTP, HTTPS와 SSH Port만 허용한다.

공인 IP를 `--hostname`으로 고정하면 IP 변경과 TLS 인증서 관리가 어렵다. DNS 이름을 사용하고, DNS Record와 인증서가 준비되지 않은 학습 환경에서는 HTTP 구성과 운영용 HTTPS 구성을 명확히 분리한다.

## 5 ) 초기화 상태와 Log 확인

---

GitLab은 첫 실행에서 내부 Service와 Database를 구성하므로 시작까지 시간이 걸릴 수 있다.

```bash
sudo docker ps --filter name=gitlab
sudo docker logs --follow gitlab
```

별도 Terminal에서 Health 상태를 확인한다.

{% raw %}
```bash
sudo docker inspect gitlab \
  --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}'
```
{% endraw %}

Log 추적은 `Ctrl+C`로 종료해도 Container 실행에는 영향을 주지 않는다. 오류가 반복되면 Memory, Disk 여유 공간, Volume 권한과 `external_url`을 먼저 확인한다.

## 6 ) 초기 Root Password 처리

---

초기 Password File이 남아 있는 기간에는 다음 명령으로 값을 확인할 수 있다.

```bash
sudo docker exec gitlab \
  grep 'Password:' /etc/gitlab/initial_root_password
```

이 값은 Blog, Screenshot, Shell Script나 Git Repository에 기록하지 않는다. 첫 Login 직후 Root Password를 변경하고, 초기 Password File이 영구적인 Credential 저장소가 아니라는 점을 전제로 운영한다.

이미 공개된 초기 Password는 File에서 문자열을 지우는 것으로 안전해지지 않는다. Password를 변경하고 활성 Session과 Access Token도 확인해야 한다.

## 7 ) Container 재시작과 Data 유지 확인

---

Container를 재시작한 뒤 Project와 설정이 유지되는지 확인한다.

```bash
sudo docker restart gitlab
sudo docker ps --filter name=gitlab
sudo docker logs --tail 100 gitlab
```

Volume 연결 상태도 확인한다.

{% raw %}
```bash
sudo docker inspect gitlab \
  --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
```
{% endraw %}

GitLab Upgrade는 Container Image만 바꾸는 단순 작업으로 취급하면 안 된다. 현재 Version에서 지원하는 Upgrade Path를 확인하고 `/srv/gitlab` Backup을 만든 뒤 단계적으로 진행한다.

> **최종 정리**
> - GitLab은 여러 Component를 함께 실행하므로 Memory, Swap과 Disk 사용량을 먼저 확인한다.
>
> - 설정, Log와 Application Data를 Host Volume에 분리해 Container 수명과 Data 수명을 분리한다.
>
> - 운영 환경에서는 `latest`가 아니라 검증한 GitLab Version Tag를 고정한다.
>
> - Hostname, `external_url`, 외부 SSH Port와 실제 Port Mapping을 일치시킨다.
>
> - 초기 Root Password는 첫 Login 후 변경하고 공개된 Credential은 즉시 폐기한다.

다음 글인 [GitOps와 Argo CD Architecture·설치](/cloud-native-55-gitops-argocd-architecture-installation/)에서는 Git Repository의 Desired State와 Kubernetes Cluster의 Live State를 지속적으로 일치시키는 구조를 정리한다.
