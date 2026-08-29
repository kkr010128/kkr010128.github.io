---
title: kubeadm으로 Kubernetes Cluster 구축
description: Master와 Worker 공통 준비부터 Control Plane 초기화, CNI 설치, Worker Join과 Cluster 확인까지 단계별 구성
date: 2026-08-25
updated_at: 2026-08-26
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
---

Kubernetes Cluster는 Local 도구, 직접 구성 도구 또는 Public Cloud의 Managed Service를 이용해 구축할 수 있다. 이 글에서는 Linux Virtual Machine 세 대와 `kubeadm`을 사용하여 Master(Control Plane) 한 대와 Worker 두 대를 구성한다.

공통 준비는 모든 Node에서 수행하고, Cluster 초기화와 관리는 Control Plane에서, `kubeadm join`은 Worker에서 수행한다.

## 1 ) Kubernetes Cluster 구축 방식

---

| 방식 | 예시 | 특징 |
|---|---|---|
| Local Kubernetes | Docker Desktop, Minikube, kind | 한 대의 개발 Machine에서 학습·개발·CI 용도로 사용 |
| 경량 Distribution | k3s, k0s | 설치와 운영 구성을 단순화한 Kubernetes Distribution |
| 직접 구성 | kubeadm, kOps, Kubespray | On-premises 또는 Cloud VM에 Cluster 직접 구성 |
| Managed Kubernetes | EKS, AKS, GKE, NKS | Cloud Provider가 Control Plane 운영을 관리 |

### Local Kubernetes

- Docker Desktop은 Desktop 환경에서 Kubernetes Cluster를 활성화할 수 있다.

- Minikube는 Container, Virtual Machine 또는 Bare Metal Driver를 사용하여 Local Cluster를 만든다.

- kind(Kubernetes IN Docker)는 Kubernetes Node를 Container로 실행하며 Local 개발과 CI Test에 활용할 수 있다.

- k3s와 k0s는 비교적 간단하게 설치할 수 있는 Kubernetes Distribution이다.

### 직접 구성과 Managed Service

`kubeadm`은 Kubernetes가 제공하는 Cluster Bootstrap 도구이다. Control Plane과 Worker를 직접 구성하면서 각 Node의 역할과 Component를 확인하기에 적합하다. kOps와 Kubespray 같은 도구는 Infrastructure 구성이나 반복 설치 자동화에 활용할 수 있다.

AWS EKS, Microsoft AKS, Google GKE와 NHN Cloud NKS 같은 Managed Kubernetes는 Control Plane 운영의 많은 부분을 Cloud Provider가 담당한다. SUSE Rancher와 Red Hat OpenShift는 Kubernetes 기반 Platform을 구축하고 관리하는 데 사용할 수 있다.

## 2 ) 실습 Cluster 구성

---

서로 통신할 수 있는 Linux Virtual Machine 세 대를 준비한다.

```text
Kubernetes Cluster
├── master   192.168.0.100   Control Plane
├── worker1  192.168.0.101   Worker Node
└── worker2  192.168.0.102   Worker Node
```

IP Address는 내 현재 환경에 맞춘 예시이다. 실제 Network에 맞는 고정 Address를 사용하고 모든 Node에서 서로 통신할 수 있어야 한다.

### Node별 역할

| 작업 | Master(Control Plane) | Worker |
|---|---|---|
| Hostname·Network 설정 | 수행 | 수행 |
| Kernel·Swap 설정 | 수행 | 수행 |
| Container Runtime 설치 | 수행 | 수행 |
| kubelet·kubeadm 설치 | 수행 | 수행 |
| `kubeadm init` | 수행 | 수행하지 않음 |
| Kubeconfig 설정 | 수행 | 일반적으로 수행하지 않음 |
| CNI 설치 | 수행 | 수행하지 않음 |
| `kubeadm join` | 수행하지 않음 | 수행 |
| `kubectl get nodes` | 수행 | Kubeconfig가 있다면 가능 |

### 최소 Resource와 Network

- 모든 Machine에 2GiB 이상의 Memory를 준비한다.

- Control Plane에는 2개 이상의 CPU Core를 할당한다.

- Application 실습을 고려하여 Worker에도 CPU, Memory와 Disk를 넉넉하게 할당한다.

- 모든 Node에서 고유한 Hostname, MAC Address와 Product UUID를 사용한다.

- 모든 Node의 시간 동기화와 양방향 Network 통신을 확인한다.

Control Plane 한 대가 중지되면 Cluster 관리 API를 사용할 수 없으므로 이 구성은 학습용이다. 운영 환경에서는 여러 Control Plane과 Load Balancer를 이용한 고가용성 구성을 검토한다.

## 3 ) 모든 Node 공통 준비

---

이 절의 명령은 **Master와 모든 Worker에서 실행**한다.

### Hostname 설정

각 Node에서 역할에 맞는 Hostname을 지정한다.

```bash
# Master에서 실행
sudo hostnamectl set-hostname master
```

```bash
# Worker 1에서 실행
sudo hostnamectl set-hostname worker1
```

```bash
# Worker 2에서 실행
sudo hostnamectl set-hostname worker2
```

모든 Node의 `/etc/hosts`에 Master와 Worker의 IP Address 및 Hostname을 등록한다. 기존 `localhost` 관련 항목은 유지하고 다음 세 줄을 추가한다.

```bash
# Master와 모든 Worker에서 실행
sudo nano /etc/hosts

→ 127.0.0.1 {hostName}
```

```text
192.168.0.100 master
192.168.0.101 worker1
192.168.0.102 worker2
```

세 Node에 동일한 내용을 등록하면 IP Address 대신 Hostname으로 통신할 수 있다.

```bash
ping -c 3 master
ping -c 3 worker1
ping -c 3 worker2
```

고정 IP는 Ubuntu의 경우 `/etc/netplan` 아래 YAML File 등 운영체제의 Network 설정 방식으로 구성한다. 설정 후 각 Node에서 다른 Node의 IP Address로 통신되는지 확인한다.

```bash
ping -c 3 192.168.0.100
ping -c 3 192.168.0.101
ping -c 3 192.168.0.102
```

### Package 업데이트

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y apt-transport-https ca-certificates curl gpg
```

#### apt-transport-https ca-certificates curl gpg
Ubuntu/Debian에서 HTTPS 기반 외부 APT 저장소를 추가할 때 필요한 기본 도구들을 설치하는 명령이다.
> 우분투 24.04와 같은 최신 APT에서는 HTTPS 지원이 **APT 자체에 포함되어 있어 별도로 설치할 필요 가 없다.**
>
> 따라서 다음 명령으로도 충분하다.
>
> `sudo apt-get install -y ca-certificates curl gpg`

| 패키지                   | 역할                              |
| --------------------- | ------------------------------- |
| `apt-transport-https` | APT가 HTTPS 저장소에서 패키지를 받도록 지원    |
| `ca-certificates`     | HTTPS 서버 인증서를 검증하기 위한 CA 인증서 모음 |
| `curl`                | URL을 통해 파일/데이터 다운로드             |
| `gpg`                 | 저장소의 GPG 서명을 검증하기 위한 도구         |

### Swap 비활성화

> **Swap**
>
> 물리 메모리(RAM)가 부족할 때 디스크의 일부 공간을 메모리처럼 사용하는 기능이다. RAM보다 속도가 느리지만 메모리 부족 상황을 보완할 수 있다.

Kubernetes가 각 Pod의 메모리 사용량을 정확하게 관리하고 예측하기 어려워지는 경우를 방지하기 위해, 기본 kubelet 설정은 Swap이 활성화된 Node에서 시작을 거부한다. 따라서 현재 Session의 Swap을 비활성화하고 재부팅 후에도 다시 활성화되지 않도록 `/etc/fstab`을 수정한다.

```bash
sudo swapoff -a
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
```

```bash
swapon --show
```

출력이 없으면 활성화된 Swap 영역이 없는 상태이다. 기존 `/etc/fstab` 항목을 수정하기 전에는 원본을 Backup하고 중복 실행 시 결과를 확인한다.

### Kernel Module과 `sysctl`

Container Network에서 Overlay File System과 Bridge Traffic 처리를 사용할 수 있도록 Module을 설정한다.

```bash
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
```

```bash
sudo modprobe overlay
sudo modprobe br_netfilter
```

IPv4 Forwarding과 Bridge Traffic의 iptables 처리를 활성화한다.

```bash
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
```

```bash
sudo sysctl --system
```

설정값을 확인한다.

```bash
sysctl net.bridge.bridge-nf-call-iptables
sysctl net.bridge.bridge-nf-call-ip6tables
sysctl net.ipv4.ip_forward
```

## 4 ) 모든 Node에 containerd 설치

---

Pod는 Worker에서 실행되지만 Control Plane도 Kubernetes Component를 Static Pod로 실행할 수 있으므로 **모든 Node에 Container Runtime이 필요**하다.

### containerd 설치

```bash
sudo apt-get install -y containerd
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml
```

Kubernetes의 kubelet과 Runtime이 같은 cgroup Driver를 사용하도록 `/etc/containerd/config.toml`에서 `SystemdCgroup`을 `true`로 설정한다.

```bash
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
```

설정이 실제 File에 반영되었는지 확인한다.

```bash
grep SystemdCgroup /etc/containerd/config.toml
```

containerd를 재시작하고 Boot 시 자동으로 시작하도록 설정한다.

```bash
sudo systemctl restart containerd
sudo systemctl enable containerd
sudo systemctl status containerd
```

Distribution에서 제공하는 containerd Version에 따라 설정 File 구조가 다를 수 있다. `SystemdCgroup` 항목이 없거나 Service가 시작되지 않으면 설치된 containerd Version의 설정 구조를 먼저 확인한다.

## 5 ) 모든 Node에 Kubernetes Package 설치

---

Kubernetes `v1.30`은 지원이 종료된 Version이다. 이 글은 2026년 8월 25일 기준 지원 Branch인 Kubernetes `v1.36` Package Repository를 사용한다.

### Repository Key 등록

```bash
sudo mkdir -p -m 755 /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.36/deb/Release.key \
  | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
```

### Repository 등록

```bash
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.36/deb/ /' \
  | sudo tee /etc/apt/sources.list.d/kubernetes.list
```

Kubernetes Package Repository는 Minor Version별로 분리되어 있다. 다른 Version을 사용할 때는 Cluster 전체에서 Version 호환 정책을 확인하고 URL의 Minor Version을 일관되게 변경한다.

### kubelet, kubeadm, kubectl 설치

```bash
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
sudo systemctl enable --now kubelet
```

| Package | 역할 | 필요한 Node |
|---|---|---|
| `kubelet` | Node에서 Pod와 Container 상태 관리 | 모든 Node |
| `kubeadm` | Cluster 초기화와 Node Join | 모든 Node |
| `kubectl` | API Server에 관리 요청 전달 | Control Plane 또는 별도 관리 Client |

Worker에 `kubectl`이 반드시 필요한 것은 아니지만 Package 구성을 동일하게 유지하는 학습 환경에서는 함께 설치할 수 있다. Kubeconfig가 없으면 `kubectl`만 설치되어 있어도 Cluster를 관리할 수 없다.

초기화 전 kubelet이 반복 재시작될 수 있다. 아직 Cluster 설정을 받지 못한 상태이므로 `kubeadm init` 또는 `kubeadm join` 전에는 예상되는 동작이다.

## 6 ) 방화벽과 Port 확인

---
Kubernetes Cluster에서는 Control Plane, Worker Node, CNI Plugin 사이 통신을 위해 여러 Port를 사용한다.
운영 환경에서는 방화벽 전체를 중지하기보다 Node 역할과 CNI Plugin에 필요한 Port만 허용하는 방식으로 구성할 수 있다.
따라서 운영 환경 기준으로, 방화벽 전체를 중지하지 않고 Node 역할과 CNI Plugin에 필요한 Port를 허용한다.
### Control Plane Port

| Port | Protocol | 용도 |
|---|---|---|
| `6443` | TCP | Kubernetes API Server |
| `2379-2380` | TCP | etcd Client와 Peer 통신 |
| `10250` | TCP | kubelet API |
| `10257` | TCP | kube-controller-manager |
| `10259` | TCP | kube-scheduler |

```bash
# Kubernetes API Server
sudo ufw allow 6443/tcp

# etcd Client / Peer
sudo ufw allow 2379:2380/tcp

# kubelet API
sudo ufw allow 10250/tcp

# kube-controller-manager
sudo ufw allow 10257/tcp

# kube-scheduler
sudo ufw allow 10259/tcp

# Flannel VXLAN
sudo ufw allow 8472/udp
```
### Worker Port

| Port          | Protocol | 용도                         |
| ------------- | -------- | -------------------------- |
| `10250`       | TCP      | kubelet API                |
| `10256`       | TCP      | kube-proxy Health Endpoint |
| `30000-32767` | TCP/UDP  | 기본 NodePort 범위             |

```bash
# kubelet API
sudo ufw allow 10250/tcp

# kube-proxy Health Endpoint
sudo ufw allow 10256/tcp

# NodePort
sudo ufw allow 30000:32767/tcp
sudo ufw allow 30000:32767/udp

# Flannel VXLAN
sudo ufw allow 8472/udp
```

`sudo ufw allow 10250`도 정상 동작하지만, kubernetes에서 필요한 프로토콜이 명시적으로 정해져 있다면 `10250/tcp` 처럼 프로토콜을 명시한 문법을 사용하는 것이 적절하다.

Flannel VXLAN은 Node 사이의 UDP `8472` 등 별도 Port가 필요할 수 있다. 실제 허용 Port는 사용하는 CNI와 운영체제 방화벽 정책을 함께 확인한다.

Flannel의 `8472/udp`는 **Control Plane/Worker를 포함해 Flannel이 실행되는 각 Node 간 통신**에 필요하다.

### 실습 환경에서의 방화벽 비활성화
학습 및 실습용 Cluster에서는 UFW를 비활성화 하여 방화벽 설정으로 인한 노드 간 통신 문제를 피하고, 구축 과정을 단순화하는 방법을 사용할 수도 있다.
```bash
sudo systemctl stop ufw       # 현재 실행 중인 UFW 중지

sudo systemctl disable ufw    # 부팅 시 UFW 자동 실행 비활성화
```
이 방법으로 방화벽을 비활성화하면 K8s에서 사용하는 포트를 개별적으로 허용하지 않아도 된다.
다만 실제 운영 환경에서는 보안을 위해 방화벽 전체를 비활성화하기보다는 필요한 포트만 허용하는 방식으로 구성하는 것이 적절하다.

## 7 ) Master에서 Control Plane 초기화

---

이 절은 **Master(Control Plane)에서만 실행**한다. Worker에서는 실행하지 않는다.

Flannel의 기본 Pod Network CIDR과 일치하도록 `10.244.0.0/16`을 지정한다.

```bash
sudo kubeadm init --pod-network-cidr=10.244.0.0/16
```

여러 Network Interface가 있어 자동 선택한 Address가 적절하지 않다면 Control Plane의 고정 IP를 명시한다.

```bash
sudo kubeadm init \
  --apiserver-advertise-address=192.168.0.100 \
  --pod-network-cidr=10.244.0.0/16
```

초기화에 성공하면 다음 정보가 출력된다.

- 현재 사용자의 Kubeconfig 설정 명령

- CNI 설치 안내

- Worker가 사용할 `kubeadm join` 명령

Join Token은 Node를 Cluster에 참여시킬 수 있는 인증 정보이므로 공개 Repository나 문서에 실제 값을 저장하지 않는다.

### Kubeconfig 설정

Master의 일반 사용자 계정에서 `kubectl`을 사용하도록 설정한다.

```bash
mkdir -p "$HOME/.kube"
sudo cp -i /etc/kubernetes/admin.conf "$HOME/.kube/config"
sudo chown "$(id -u):$(id -g)" "$HOME/.kube/config"
```

API Server 연결을 확인한다.

```bash
kubectl cluster-info
kubectl get nodes
```

CNI 설치 전에는 Node가 `NotReady`로 표시될 수 있다.

## 8 ) Master에서 CNI 설치

---

Kubernetes는 CNI Specification을 제공하지만 Pod Network 구현을 직접 선택하여 설치해야 한다. 이 실습에서는 Flannel을 사용한다.

**실행 위치: Master(Control Plane)**

```bash
kubectl apply -f \
  https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

Flannel Manifest의 기본 Network가 `10.244.0.0/16`이므로 `kubeadm init`의 `--pod-network-cidr`와 일치해야 한다. 다른 CNI를 사용한다면 해당 Plugin이 요구하는 CIDR과 설치 절차를 따른다. Cluster에는 일반적으로 하나의 Pod Network를 설치한다.

상태를 확인한다.

```bash
kubectl get pods --all-namespaces
kubectl get pods -n kube-flannel
kubectl get nodes
```

Pod Network가 정상적으로 구성되면 CoreDNS Pod와 Control Plane Node가 `Running`, `Ready` 상태로 전환된다.

## 9 ) Worker를 Cluster에 연결

---

이 절은 **각 Worker에서 실행**한다. `kubeadm init` 결과에 출력된 Join 명령을 사용한다.

```bash
sudo kubeadm join <CONTROL_PLANE_IP>:6443 \
  --token <TOKEN> \
  --discovery-token-ca-cert-hash sha256:<HASH>
```

예시의 `<CONTROL_PLANE_IP>`, `<TOKEN>`, `<HASH>`는 실제 출력값으로 바꾼다. 실제 Token과 Hash를 문서에 고정하여 저장하지 않는다.

Token이 만료되었거나 Join 명령을 잃어버렸다면 Master에서 다시 생성한다.

```bash
kubeadm token create --print-join-command
```

Worker에서 Join이 완료되면 kubelet은 API Server와 통신하고, Scheduler가 해당 Worker에 배치한 Pod를 Container Runtime으로 실행한다.

## 10 ) Master에서 Cluster 확인

---

Worker Join 이후에는 **Master에서** Cluster 상태를 확인한다.

```bash
kubectl get nodes -o wide
```

예상 구조는 다음과 같다.

```text
NAME      STATUS   ROLES           VERSION
master    Ready    control-plane   v1.36.x
worker1   Ready    <none>          v1.36.x
worker2   Ready    <none>          v1.36.x
```

System Pod가 어느 Node에서 실행되는지도 확인한다.

```bash
kubectl get pods -n kube-system -o wide
kubectl get pods -n kube-flannel -o wide
```

### Master와 Worker의 동작 흐름

```text
관리 사용자
    │ kubectl 요청
    ▼
Master(Control Plane)
    ├── API Server가 요청 검증 및 저장
    ├── Controller가 원하는 상태 조정
    └── Scheduler가 Worker 선택
                    │
                    ▼
Worker
    ├── kubelet이 할당된 Pod 확인
    ├── Container Runtime이 Container 실행
    └── CNI가 Pod Network 구성
```

Master는 Cluster의 상태와 배치를 결정하고 Worker는 실제 Application Pod를 실행한다. Worker의 kubelet은 API Server에서 자신에게 할당된 PodSpec을 관찰하여 실행 상태를 맞춘다.

## 11 ) Node 제거와 Cluster Reset

---

Reset은 Cluster 상태와 Node 설정을 제거하므로 대상 Node와 필요한 Backup을 확인한 뒤 실행한다.

### Worker 제거

먼저 Master에서 대상 Worker의 Workload를 비우고 Node Object를 삭제한다.

```bash
kubectl drain <WORKER_NAME> \
  --ignore-daemonsets \
  --delete-emptydir-data
kubectl delete node <WORKER_NAME>
```

대상 Worker에서 kubeadm 상태를 초기화한다.

```bash
sudo kubeadm reset -f
```

### 전체 학습 Cluster 초기화

Worker를 먼저 Reset한 뒤 Master에서 실행한다.

```bash
sudo kubeadm reset -f
```

`kubeadm reset`은 CNI 설정 Directory와 사용자 Kubeconfig를 자동으로 모두 제거하지 않는다. 같은 Machine을 새 Cluster에 재사용하면서 CNI를 변경한다면 `/etc/cni/net.d`의 내용을 Backup하고 대상을 확인한 후 정리한다.

```bash
sudo rm -rf /etc/cni/net.d
```

Cluster가 더 이상 존재하지 않고 Admin Kubeconfig가 필요하지 않은지 확인한 뒤 현재 사용자의 설정 File을 삭제한다.

```bash
rm -f "$HOME/.kube/config"
```

`/etc/kubernetes/*`, `/var/lib/kubelet/*`, `~/.kube`를 직접 모두 삭제하면 필요한 File까지 광범위하게 제거할 수 있다. `kubeadm reset` 결과와 Machine 재사용 목적을 확인한 뒤 필요한 항목만 정리한다.

## 전체 정리

---

> **최종 정리**
>
> - Host, Kernel, Swap, Container Runtime과 Kubernetes Package 준비는 Master와 Worker 모두에서 수행한다.
>
> - `kubeadm init`, Kubeconfig 설정과 CNI 설치는 Master(Control Plane)에서 수행한다.
>
> - Worker는 Master가 생성한 Token과 CA Hash를 사용하여 `kubeadm join`을 실행한다.
>
> - Master는 API와 Cluster 상태를 관리하고 Worker는 kubelet과 Container Runtime으로 실제 Pod를 실행한다.
>
> - 방화벽 전체를 중지하지 않고 Kubernetes Component와 CNI에 필요한 Port를 허용한다.
>
> - Kubernetes `v1.30`은 지원이 종료되었으므로 이 글의 설치 명령은 `v1.36` Repository를 사용한다.
