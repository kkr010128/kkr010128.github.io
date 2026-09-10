---
title: Container Image Registry와 Kubernetes Image Pull
description: Public·Private Image Registry의 구조와 Docker Hub 배포, 자체 Registry 구성, Kubernetes Worker의 Image Pull 및 Harbor의 역할
date: 2026-09-09
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Docker
---

[Docker 이미지와 Union File System](/cloud-native-10-docker-images/)에서는 Image 이름, Tag와 Docker Hub Push를 다뤘다. 이 글에서는 범위를 Registry 전체로 확장하여 Image가 저장되고 배포되는 과정과 Kubernetes Worker가 Registry에서 Image를 가져오는 과정을 연결한다.

## 1 ) Image Registry

---

> **Image Registry**
>
> Container Image와 OCI Artifact를 이름과 Version별로 저장하고 Client의 Push와 Pull 요청에 응답하는 Service이다.

Registry는 Image File 하나를 그대로 보관하는 단순 File Server가 아니다. Image Manifest, 여러 Layer와 설정 정보를 Content Digest로 관리하고 Repository와 Tag를 통해 이를 찾을 수 있게 한다.

Image의 전체 참조 형식은 다음과 같다.

```text
REGISTRY/NAMESPACE/REPOSITORY:TAG
REGISTRY/NAMESPACE/REPOSITORY@DIGEST
```

| 구성 요소 | 예시 | 역할 |
|---|---|---|
| Registry | `docker.io` | Image를 제공하는 Registry 주소 |
| Namespace | `example-user` | 사용자, 조직 또는 Project 구분 |
| Repository | `python-app` | 하나의 Application Image 계열 |
| Tag | `v1.0` | 사람이 읽을 수 있는 Version 별칭 |
| Digest | `sha256:...` | Image Content를 식별하는 불변 Hash |

`docker.io/library/nginx:1.29`에서 `docker.io`는 Registry, `library`는 Namespace, `nginx`는 Repository, `1.29`는 Tag이다. Tag는 다른 Image를 가리키도록 바뀔 수 있지만 Digest는 같은 Content를 계속 가리킨다.

## 2 ) Public Registry와 Private Registry

---

Registry는 접근 범위와 운영 주체에 따라 구분할 수 있다.

| 구분 | 예시 | 특징 | 확인할 사항 |
|---|---|---|---|
| Public Registry Service | Docker Hub, GHCR, Quay.io | Internet에서 바로 사용하기 쉽고 공개 Image 생태계가 큼 | Rate Limit, 공개 범위, 계정 보안 |
| Cloud Registry Service | Amazon ECR, Google Artifact Registry 등 | Cloud IAM, Audit와 CI/CD Service 연동 | Region, 권한, Network와 비용 정책 |
| 자체 Private Registry | CNCF Distribution, Harbor | 내부 Network와 보안 정책에 맞게 직접 운영 | TLS, 인증, Storage, Backup, 고가용성 |

Private Registry가 반드시 사내 Server를 의미하는 것은 아니다. Docker Hub, GHCR와 Cloud Registry에서도 비공개 Repository를 사용할 수 있다. 반대로 자체 Registry를 실행해도 인증과 Network 접근 제어가 없다면 안전한 Private Registry라고 볼 수 없다.

Service의 무료 범위, 저장 용량과 과금 정책은 변경될 수 있으므로 Registry 선택 시 현재 공식 Plan을 확인한다.

## 3 ) Image 배포 흐름

---

Application을 Registry를 통해 배포하는 기본 흐름은 다음과 같다.

```text
Source Code + Dockerfile
          │ docker build
          ▼
      Local Image
          │ docker tag
          ▼
Registry 주소가 포함된 Image 참조
          │ docker push
          ▼
        Registry
          │ docker pull
          ▼
Docker Host 또는 Kubernetes Worker
```

| 단계 | 명령 | 결과 |
|---|---|---|
| Build | `docker build` | Local Image Store에 Image 생성 |
| Tag | `docker tag` | 같은 Image에 Registry용 참조 이름 추가 |
| Push | `docker push` | Registry에 Manifest와 Layer 업로드 |
| Pull | `docker pull` | Registry에서 Manifest와 필요한 Layer 다운로드 |

Application Image를 만드는 방법은 [애플리케이션별 Docker 이미지 빌드](/cloud-native-14-application-image/)에서 자세히 다룬다. 여기서는 다음 Image가 Local에 준비되어 있다고 가정한다.

```bash
docker image ls my-python-app
```

## 4 ) Docker Hub에 Image 배포

---

### 로그인

Docker Hub 계정 이름을 지정하고 로그인한다. Password 대신 Personal Access Token을 사용하는 경우에도 명령 인자에 Token을 직접 작성하지 않고 Prompt에 입력한다.

```bash
docker login -u <docker-hub-username>
```

로그인 결과는 일반적으로 사용자별 Docker 설정 File에 저장된다. 개인 Token을 Markdown, Shell Script, Git Repository나 화면에 표시되는 명령에 넣지 않는다.

```bash
docker info
```

### Tag와 Push

Local Image에 Docker Hub Namespace가 포함된 이름을 추가한다.

```bash
docker tag my-python-app:latest \
  <docker-hub-username>/python-app:v1.0
```

두 이름이 같은 Image ID를 가리키는지 확인한다.

```bash
docker image ls \
  <docker-hub-username>/python-app:v1.0
```

Registry로 Push한다.

```bash
docker push \
  <docker-hub-username>/python-app:v1.0
```

Push가 끝나면 다른 Host 또는 Local Image를 사용하지 않는 격리된 환경에서 Pull하여 Registry 배포를 검증한다.

```bash
docker pull \
  <docker-hub-username>/python-app:v1.0
```

`latest`는 자동으로 최신 Version을 찾는 기능이 아니라 이름이 `latest`인 Tag이다. 배포 Manifest에는 검증한 Version Tag를 사용하고 더 강한 재현성이 필요하면 Digest를 고정한다.

### Public과 Private Repository

Public Repository의 Image는 일반적으로 인증 없이 Pull할 수 있다. Private Repository는 Registry가 발급한 Credential이 필요하며 Docker Hub의 제공 범위와 비용 정책은 현재 Plan을 확인해야 한다.

로그인하지 않은 상태에서 Private Image Pull이 실패하면 다음 항목을 확인한다.

- Image 이름의 Namespace와 Repository가 정확한지 확인한다.

- 계정 또는 Token에 Repository를 읽을 권한이 있는지 확인한다.

- Token이 만료되거나 폐기되지 않았는지 확인한다.

- `docker logout` 후 올바른 계정으로 다시 로그인했는지 확인한다.

## 5 ) Kubernetes의 Image Pull

---

Kubernetes는 Registry에 Image를 Push하지 않는다. 관리자가 Deployment를 생성하면 Control Plane이 Pod 배치를 결정하고, 선택된 Worker의 kubelet이 Container Runtime을 통해 Image를 Pull한다.

```text
관리 Client
    │ Deployment 제출
    ▼
API Server
    │
    ├── Deployment·ReplicaSet Controller가 Pod 생성
    │
    └── Scheduler가 실행할 Worker 결정
                         │
                         ▼
                    Worker kubelet
                         │ CRI 요청
                         ▼
                       containerd
                         │ Image Pull
                         ▼
                       Registry
                         │ Layer 저장
                         ▼
                    Container 실행
```

### Public Image를 사용하는 Deployment

다음 내용을 `flask-deployment.yaml`로 저장한다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flask-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: flask-web
  template:
    metadata:
      labels:
        app: flask-web
    spec:
      containers:
        - name: flask-container
          image: <docker-hub-username>/python-app:v1.0
          ports:
            - name: http
              containerPort: 5000
```

Service는 세 Pod의 Port `5000`으로 요청을 전달한다. 다음 내용을 `flask-service.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: flask-service
spec:
  type: ClusterIP
  selector:
    app: flask-web
  ports:
    - name: http
      protocol: TCP
      port: 8080
      targetPort: 5000
```

Control Plane에 접근 가능한 관리 Client에서 적용한다.

```bash
kubectl apply -f flask-deployment.yaml
kubectl apply -f flask-service.yaml
kubectl rollout status deployment/flask-deployment
kubectl get pods -o wide
```

Ingress를 연결하기 전에 Port Forwarding으로 Service와 Pod 응답을 먼저 확인한다.

```bash
kubectl port-forward service/flask-service 8080:8080
```

다른 Terminal에서 요청한다.

```bash
curl http://127.0.0.1:8080
```

Application Log와 Pod Event를 함께 확인한다.

```bash
kubectl logs deployment/flask-deployment --all-pods=true
kubectl describe pod <pod-name>
kubectl get events \
  --sort-by=.metadata.creationTimestamp
```

외부 Host 기반 Routing은 [Kubernetes Ingress와 HTTP Routing](/cloud-native-33-kubernetes-ingress-routing/)에서 이어서 다룬다. 새 Ingress Manifest는 Legacy Annotation 대신 `spec.ingressClassName`을 사용한다.

### Private Image와 `imagePullSecrets`

Private Repository를 사용하는 Pod는 같은 Namespace의 Registry Credential Secret을 참조한다.

```yaml
spec:
  template:
    spec:
      imagePullSecrets:
        - name: regcred
      containers:
        - name: flask-container
          image: <docker-hub-username>/private-python-app:v1.0
```

동작 관계는 다음과 같다.

```text
Pod의 imagePullSecrets
        │
        ▼
Worker kubelet이 같은 Namespace의 Secret 확인
        │
        ▼
CRI Image Pull 요청에 Registry 인증 정보 전달
        │
        ▼
containerd가 Private Registry에서 Image Pull
```

Secret 생성과 안전한 Credential 관리 방법은 [Kubernetes 환경 변수, Secret과 ConfigMap](/cloud-native-34-kubernetes-env-secret-configmap/)의 Private Registry Secret 절에서 다룬다.

`ImagePullBackOff`가 발생하면 Application Log보다 Pod Event를 먼저 확인한다. Container가 시작되기 전 Image Pull 단계에서 실패하면 Application Log가 존재하지 않을 수 있다.

```bash
kubectl describe pod <pod-name>
kubectl get pod <pod-name> \
  -o jsonpath='{.spec.containers[*].image}{"\n"}'
```

## 6 ) 자체 Registry 구성

---

CNCF Distribution은 OCI Distribution API를 제공하는 가벼운 Registry 구현이다. Local File System을 기본 Storage로 사용할 수 있고 필요에 따라 외부 Object Storage와 인증 구성을 연결할 수 있다.

### 격리된 실습용 Registry 실행

다음 구성은 `localhost` 또는 신뢰할 수 있는 폐쇄형 실습 Network에서 Registry API를 확인하기 위한 예제이다. 외부에 공개할 운영 구성으로 사용하지 않는다.

Registry Data를 Container 삭제와 분리하기 위해 Named Volume을 먼저 생성한다.

```bash
docker volume create registry-data
```

Registry Container를 실행한다.

```bash
docker run -d \
  --name registry \
  --restart=always \
  -p 5000:5000 \
  -v registry-data:/var/lib/registry \
  registry:3
```

| 설정 | 역할 |
|---|---|
| `-p 5000:5000` | Host의 TCP `5000`을 Registry API에 연결 |
| `--restart=always` | Docker Daemon 재시작 후 Container 재실행 |
| `-v registry-data:/var/lib/registry` | Registry Manifest와 Layer를 Volume에 저장 |
| `registry:3` | CNCF Distribution 3.x Image 사용 |

Container 상태, API 응답과 Log를 확인한다.

```bash
docker ps --filter name=registry
curl -i http://127.0.0.1:5000/v2/
docker logs registry
```

인증이 없는 Local Registry의 `/v2/`가 정상 동작하면 빈 JSON Object인 `{}`가 반환될 수 있다. 인증을 적용한 Registry에서는 `401 Unauthorized`와 인증 Challenge가 정상 상태일 수 있다.

### Local Registry에 Push

Image에 Registry 주소가 포함된 Tag를 추가한다.

```bash
docker tag my-python-app:latest \
  127.0.0.1:5000/python-app:v1
```

Push한 뒤 Registry Catalog와 Tag를 확인한다.

```bash
docker push 127.0.0.1:5000/python-app:v1
curl http://127.0.0.1:5000/v2/_catalog
curl http://127.0.0.1:5000/v2/python-app/tags/list
```

Registry Container를 재시작하고 Image를 다시 Pull하여 Volume의 Data가 유지되는지 확인한다.

```bash
docker restart registry
docker pull 127.0.0.1:5000/python-app:v1
docker logs --tail 50 registry
```

## 7 ) HTTP Registry와 TLS Registry

---

Docker와 containerd는 Registry 통신에서 HTTPS를 기본으로 기대한다. Plain HTTP Registry는 Traffic과 Credential을 보호하지 못하므로 격리된 실습 환경에서만 제한적으로 사용한다.

| 환경 | 통신 방식 | 요구 사항 |
|---|---|---|
| Local 단일 Host 실습 | `http://127.0.0.1:5000` | 외부 접근 차단, 실제 Credential 사용 금지 |
| 폐쇄형 다중 Node 실습 | 임시 HTTP 또는 내부 CA 기반 HTTPS | 접근 가능한 Node 제한, 사용 목적과 위험 명시 |
| 운영 환경 | 신뢰 가능한 TLS 기반 HTTPS | 인증, 권한, 영구 Storage, Backup, Monitoring |

운영 Registry는 다음 항목을 함께 설계한다.

- DNS Name과 Server 인증서의 Subject Alternative Name이 일치해야 한다.

- Registry를 사용하는 모든 Client가 인증서 발급 CA를 신뢰해야 한다.

- Repository별 Push와 Pull 권한을 분리한다.

- Registry Metadata와 Blob Storage를 영구 저장하고 Backup한다.

- Disk 사용량, 오류율, 인증 실패와 취약점 Scan 결과를 Monitoring한다.

### Docker Engine의 실습용 HTTP 허용

Docker Engine으로 Remote HTTP Registry에 Push하거나 Pull해야 하는 격리된 실습 환경에서는 `/etc/docker/daemon.json`의 `insecure-registries`에 정확한 Host와 Port를 등록할 수 있다.

```json
{
  "insecure-registries": [
    "192.168.0.100:5000"
  ]
}
```

기존 `daemon.json`에 다른 설정이 있다면 File 전체를 덮어쓰지 않고 JSON Object 안에 항목을 병합한다. 문법을 확인한 뒤 Docker를 재시작한다.

```bash
sudo systemctl restart docker
docker info
```

이 설정은 해당 Docker Daemon의 동작만 바꾼다. Kubernetes Worker가 containerd를 사용한다면 Docker 설정만으로 kubelet의 Image Pull이 허용되지 않는다.

## 8 ) Kubernetes Worker의 containerd Registry 설정

---

Registry 설정은 실제 Image를 Pull할 가능성이 있는 모든 Worker에 필요하다. Control Plane Node에도 Workload Scheduling을 허용했다면 해당 Node 역시 같은 설정 대상이다.

```text
Control Plane
└── Pod를 어느 Worker에 배치할지 결정

Worker
├── kubelet이 PodSpec의 Image 참조 확인
├── containerd에 Pull 요청
└── Worker Local Storage에 Image Layer 저장
```

### `hosts.toml` 작성

각 Worker에서 Registry Host와 Port에 해당하는 Directory를 만든다.

```bash
sudo mkdir -p \
  /etc/containerd/certs.d/192.168.0.100:5000
```

`/etc/containerd/certs.d/192.168.0.100:5000/hosts.toml`에 격리된 HTTP 실습 Registry를 등록한다.

```toml
server = "http://192.168.0.100:5000"

[host."http://192.168.0.100:5000"]
  capabilities = ["pull", "resolve"]
```

`skip_verify`는 HTTPS 인증서 검증을 건너뛰는 Option이다. Plain HTTP를 지정하는 설정에 습관적으로 추가하지 않는다. 운영 환경에서는 `http://` 대신 `https://`를 사용하고 필요한 CA 인증서를 배포한다.

### containerd 1.x의 `config_path`

`/etc/containerd/config.toml`이 Version 2 형식이고 containerd 1.x를 사용한다면 다음 Section을 확인한다.

```toml
version = 2

[plugins."io.containerd.grpc.v1.cri".registry]
  config_path = "/etc/containerd/certs.d"
```

### containerd 2.x의 `config_path`

containerd 2.x의 Version 3 설정에서는 Plugin 경로가 다르다.

```toml
version = 3

[plugins."io.containerd.cri.v1.images".registry]
  config_path = "/etc/containerd/certs.d"
```

기존 설정의 `version`과 Plugin Section을 먼저 확인하고 서로 다른 Version 예제를 한 File에 동시에 넣지 않는다.

```bash
containerd --version
sudo containerd config dump | less
```

`config_path`를 처음 활성화하도록 `config.toml`을 변경했다면 containerd를 재시작하고 상태와 Log를 확인한다.

```bash
sudo systemctl restart containerd
sudo systemctl status containerd --no-pager
sudo journalctl -u containerd -n 100 --no-pager
```

`config_path`가 이미 설정된 환경에서 Registry별 `hosts.toml`만 변경하는 경우에는 containerd가 해당 Directory의 변경을 읽으므로 일반적으로 Daemon 재시작이 필요하지 않다.

각 Worker에서 CRI 경로를 직접 검증한다.

```bash
sudo crictl pull \
  192.168.0.100:5000/python-app:v1
sudo crictl images
```

그다음 Control Plane에 접근 가능한 관리 Client에서 Pod를 다시 생성하거나 Deployment Rollout을 수행한다.

```bash
kubectl rollout restart deployment/flask-deployment
kubectl rollout status deployment/flask-deployment
kubectl get pods -o wide
```

### Deprecated Registry 설정

다음과 같이 CRI Plugin 아래에 `registry.mirrors`와 `registry.configs`를 직접 작성하는 방식은 Deprecated 상태이다.

```toml
[plugins."io.containerd.grpc.v1.cri".registry.mirrors."192.168.0.100:5000"]
  endpoint = ["http://192.168.0.100:5000"]
```

기존 환경을 확인할 때는 볼 수 있지만 신규 구성은 `config_path`와 Registry별 `hosts.toml`을 사용한다.

## 9 ) Legacy Registry Web UI

---

Registry API 자체는 Image 검색과 권한 관리를 위한 완성된 Web Portal을 제공하지 않는다. 과거에는 `hyper/docker-registry-web` Container를 `--link`로 Registry에 연결하는 예제가 사용되었다.

이 구성은 다음 이유로 신규 환경에 그대로 적용하지 않는다.

- Docker의 Legacy Container Link에 의존한다.

- 오래된 별도 Image의 유지보수와 보안 상태를 추가로 검증해야 한다.

- 인증, 권한, 취약점 Scan과 Project 관리가 Registry와 분리된다.

단순 API 확인은 `/v2/`, `/v2/_catalog`와 `/tags/list`를 사용하고 관리 UI와 보안 기능이 필요하면 Harbor 같은 Registry Platform을 검토한다.

## 10 ) Harbor

---

Harbor는 OCI 호환 Registry를 기반으로 내부 Image와 Artifact를 관리하는 Open Source Registry Platform이다.

| 기능 | 역할 |
|---|---|
| Project | Repository와 접근 범위를 조직 단위로 구분 |
| RBAC | 사용자와 Robot Account의 Push·Pull 권한 관리 |
| Web UI | Repository, Artifact, Tag와 Scan 결과 확인 |
| Vulnerability Scan | 저장된 Artifact의 알려진 취약점 검사 |
| Replication | 다른 Registry와 Artifact 복제 |
| OCI Artifact | Container Image 외 Helm Chart 등의 Artifact 저장 |

CNCF Distribution이 Registry API의 가벼운 기반을 제공한다면 Harbor는 조직에서 필요한 사용자 관리, 보안 검사와 운영 UI를 함께 제공한다. 그 대신 구성 요소와 운영 부담이 더 크므로 단일 개발 Host의 단순 저장소에는 Distribution이 적합할 수 있고, 여러 사용자와 Project를 관리해야 하는 환경에는 Harbor가 적합할 수 있다.

Helm Chart도 OCI Artifact로 Registry에 저장할 수 있다. Chart Package의 실제 Push와 Pull 과정은 [Kubernetes Helm Chart와 Release 관리](/cloud-native-40-kubernetes-helm/)에서 이어서 다룬다.

## 11 ) Registry 문제 진단 순서

---

Image Pull 실패는 Application 실행 이전 단계의 문제이다. 다음 순서로 범위를 좁힌다.

1. Image 참조의 Registry, Namespace, Repository와 Tag가 정확한지 확인한다.

2. 실행 주체가 Public Image인지 Private Image인지 확인한다.

3. Registry API와 TCP Port에 접근할 수 있는지 확인한다.

4. TLS 인증서와 Client의 CA 신뢰 상태를 확인한다.

5. Docker 또는 containerd 중 실제 Pull을 수행하는 Runtime 설정을 확인한다.

6. Kubernetes에서는 Secret의 Namespace와 `imagePullSecrets` 이름을 확인한다.

7. Pod Event, containerd Log와 Registry Log의 같은 시간대 요청을 대조한다.

```bash
# Registry Host
docker logs --since 10m registry

# Worker
sudo journalctl -u containerd --since "10 minutes ago"

# Control Plane에 접근 가능한 관리 Client
kubectl describe pod <pod-name>
kubectl get events \
  --sort-by=.metadata.creationTimestamp
```

| 증상 | 우선 확인 대상 |
|---|---|
| `ImagePullBackOff` | 직전 Pull 실패 원인을 보여주는 Pod Event |
| `unauthorized` | Registry Credential과 Repository 권한 |
| `manifest unknown` | Repository, Tag와 Platform Manifest |
| `x509: certificate signed by unknown authority` | Worker의 CA Trust와 Registry 인증서 Chain |
| `http: server gave HTTP response to HTTPS client` | HTTP Registry 허용 설정과 실제 Protocol |
| `connection refused` | Registry Process, Listen Port, Firewall와 주소 |

## 전체 정리

---

> **최종 정리**
>
> - Registry는 Image Manifest와 Layer를 Repository, Tag와 Digest로 관리하고 Push와 Pull API를 제공한다.
>
> - Kubernetes에서는 Scheduler가 Worker를 선택하고 해당 Worker의 kubelet과 containerd가 Registry에서 Image를 Pull한다.
>
> - Private Image는 같은 Namespace의 `imagePullSecrets`와 Registry 읽기 권한이 필요하다.
>
> - Docker Engine의 Registry 설정과 Kubernetes Worker의 containerd Registry 설정은 서로 다른 대상이다.
>
> - Plain HTTP와 인증서 검증 생략은 격리된 실습에만 제한하고 운영 Registry에는 TLS, 인증, 권한과 영구 Storage를 구성한다.
>
> - containerd의 Legacy `registry.mirrors` 방식은 Deprecated 상태이며 신규 구성은 `config_path`와 `hosts.toml`을 사용한다.
>
> - Harbor는 OCI Registry에 Project, RBAC, Web UI, 취약점 Scan과 Replication을 결합한 Platform이다.
