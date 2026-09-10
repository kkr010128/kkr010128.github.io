---
title: Git 이력 관리와 Branch 작업
description: SourceTree와 Git CLI를 연결하여 Commit 조회, Tag, Diff, Restore, Reset, Revert, Stash, Merge와 Rebase를 다루는 방법
date: 2026-09-10
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Git
---

[Version Control과 Git 기본 작업 흐름](/cloud-native-42-git-version-control-basics/)에서 Working Tree, Staging Area와 Local Repository의 관계를 살펴봤다. 이 글에서는 저장된 Commit을 조회하고 비교하는 방법부터 변경 복구, Branch 통합까지 다룬다.

SourceTree를 사용해도 Git의 상태와 History는 CLI를 사용할 때와 같다. GUI 조작과 명령을 함께 확인하면 버튼을 눌렀을 때 Repository에서 무엇이 바뀌는지 이해할 수 있다.

## 1 ) SourceTree와 Git CLI

---

SourceTree는 Git Repository를 시각적으로 다루는 GUI Client이다. File 상태, Commit Graph와 Branch 관계를 화면에 표시하고 선택한 작업에 해당하는 Git 명령을 실행한다.

| Git 작업 | SourceTree에서 확인할 영역 | CLI |
|---|---|---|
| Repository 생성 | Local Repository 생성 | `git init` |
| File 상태 확인 | File Status·Working Copy | `git status` |
| Stage | Stage 대상 선택 | `git add`, `git restore --staged` |
| Commit | Commit Message 입력 영역 | `git commit` |
| History | Commit Graph·History | `git log --graph` |
| Tag | Commit의 Tag 메뉴 | `git tag` |
| Branch 전환 | Branch 목록 | `git switch` |
| 통합 | Merge·Rebase 메뉴 | `git merge`, `git rebase` |
| 임시 보관 | Stash 메뉴 | `git stash` |

버튼 이름과 화면 배치는 SourceTree Version과 운영체제에 따라 달라질 수 있다. 조작 후 `git status`, `git log`와 `git branch`로 실제 Repository 상태를 확인하면 GUI 표시와 Git 개념을 연결할 수 있다.

## 2 ) Local Repository에서 Version 생성

---

### Repository 준비

SourceTree에서는 Local Repository 생성 화면에서 작업 Directory를 선택한다. CLI에서는 같은 Directory로 이동해 `git init`을 실행한다.

```bash
mkdir git-history-lab
cd git-history-lab
git init --initial-branch=main
```

초기 상태를 확인한다.

```bash
git status
```

### 첫 번째 Commit

`a.txt`, `b.txt`, `c.txt`를 만들고 각각 `A`, `B`, `C`를 기록한다. File 작성 방식은 사용하는 Editor에 따라 달라지므로 여기서는 Git 상태 변화에 집중한다.

```text
git-history-lab/
├── a.txt
├── b.txt
└── c.txt
```

새 File은 Untracked 상태이다.

```bash
git status
```

세 File을 다음 Commit 대상으로 Stage한다.

```bash
git add a.txt b.txt c.txt
git diff --staged
git status
```

SourceTree에서는 Unstaged File 목록에서 대상을 선택하여 Staged File 영역으로 옮긴다. Commit 전에는 Staged Diff를 읽어 의도한 내용만 포함됐는지 확인한다.

```bash
git commit -m "docs: add initial text files"
```

### 두 번째 Commit

`a.txt`를 수정하고 `c.txt`를 삭제하면 두 File 모두 Working Tree 변경으로 표시된다. 삭제도 Git이 추적하는 변경이다.

```bash
git status
git diff
```

변경을 Stage하고 두 번째 Commit을 만든다.

```bash
git add a.txt c.txt
git diff --staged
git commit -m "docs: update A and remove C"
```

`git add .`은 현재 Directory 아래의 추가, 수정과 삭제를 한꺼번에 Stage할 수 있다. 범위가 넓으므로 사용 직후 `git diff --staged`로 Commit 대상을 확인한다.

```bash
git add .
git diff --staged
```

이미 추적 중인 File의 수정과 삭제를 Stage하면서 Commit까지 수행할 때는 `-a`를 사용할 수 있다.

```bash
git commit -am "docs: update tracked files"
```

`git commit -am`은 Untracked File을 포함하지 않는다. 새 File은 먼저 `git add`로 추적 대상에 포함해야 한다.

## 3 ) Commit History 조회

---

SourceTree의 History 화면은 Commit을 Graph로 표시한다. CLI에서는 목적에 따라 `git log` Option을 조합한다.

```bash
# 상세 History
git log

# 한 Commit을 한 줄로 표시
git log --oneline

# Commit별 Patch 포함
git log --patch

# Branch와 Tag를 함께 표시
git log --oneline --graph --decorate --all
```

Commit을 선택하면 작성자, 시각, Message, Parent와 변경된 File을 확인할 수 있다. CLI에서는 `git show`를 사용한다.

```bash
git show <commit>
git show --stat <commit>
git show --name-status <commit>
```

Commit 개수는 작업을 나눈 방식에 따라 크게 달라진다. 많은 Commit이 Project 품질이나 기여 수준을 자동으로 증명하지 않으므로 변경 내용과 Message, Review 결과를 함께 봐야 한다.

## 4 ) Tag로 Version 표시

---

> **Tag**
>
> 특정 Git Object를 읽기 쉬운 이름으로 가리키는 Reference이다. Release Version을 표시할 때 주로 Commit에 연결한다.

Commit Object ID는 Git이 Content와 Metadata를 바탕으로 생성한다. 사용자가 원하는 문자열로 Object ID를 정할 수 없으므로 `v1.0.0` 같은 Tag를 별도로 붙인다.

### Lightweight Tag

현재 Commit을 직접 가리키는 Lightweight Tag를 생성한다.

```bash
git tag v1.0.0
```

### Annotated Tag

Annotated Tag에는 작성자, 생성 시각과 Message가 별도 Tag Object로 기록된다. Release 표시에는 Annotated Tag가 적합하다.

```bash
git tag -a v1.0.0 -m "release v1.0.0"
```

특정 Commit에 Tag를 붙이려면 Commit을 함께 지정한다.

```bash
git log --oneline
git tag -a v0.9.0 <commit> -m "release v0.9.0"
```

Tag 목록과 대상을 확인한다.

```bash
git tag --list
git show v1.0.0
```

Local Tag를 삭제한다.

```bash
git tag --delete v1.0.0
```

Tag는 기본 `git push`에 항상 포함되지 않는다. Remote에 특정 Tag를 올리거나 삭제하는 작업은 명시적으로 수행한다.

```bash
git push origin v1.0.0
git push origin --delete v1.0.0
```

SourceTree에서는 History에서 대상 Commit을 선택해 Tag를 만들 수 있다. 생성 후 Local Tag인지 Remote에도 Push된 Tag인지 구분해서 확인한다.

## 5 ) Version 비교

---

`git diff`는 어떤 두 상태를 비교하는지에 따라 출력 범위가 달라진다.

| 비교 대상 | 명령 | 확인하는 내용 |
|---|---|---|
| Working Tree ↔ Staging Area | `git diff` | 아직 Stage하지 않은 변경 |
| Staging Area ↔ `HEAD` | `git diff --staged` | 다음 Commit에 들어갈 변경 |
| Commit ↔ Commit | `git diff <commit-a> <commit-b>` | 두 Commit의 Snapshot 차이 |
| Branch ↔ Branch | `git diff <branch-a>..<branch-b>` | 두 Branch Tip의 Snapshot 차이 |

```bash
git diff
git diff --staged
git diff HEAD~1 HEAD
git diff main..feature/login
```

SourceTree에서는 Commit 두 개를 선택하여 변경 File과 Diff를 비교할 수 있다. 다중 선택에 사용하는 보조 Key는 운영체제에 따라 다르므로 선택된 두 Commit의 ID를 화면에서 확인한다.

### `HEAD`, `^`와 `~`

`HEAD`는 현재 Checkout한 위치를 가리킨다. Branch에 정상적으로 연결된 상태에서는 현재 Branch의 Tip Commit을 가리킨다.

| 표현 | 의미 |
|---|---|
| `HEAD` | 현재 Checkout한 Commit |
| `HEAD^` | `HEAD`의 첫 번째 Parent |
| `HEAD^2` | Merge Commit인 `HEAD`의 두 번째 Parent |
| `HEAD~2` | 첫 번째 Parent를 두 번 따라간 Commit |

일직선 History에서는 `HEAD^`와 `HEAD~1`이 같은 Commit을 가리킨다. Parent가 여러 개인 Merge Commit에서는 `^<번호>`로 어느 Parent를 선택하는지 지정할 수 있다.

## 6 ) File 변경 복구

---

File 복구는 Staging Area만 되돌리는 작업과 Working Tree의 내용을 폐기하는 작업을 구분해야 한다.

### Stage 취소

다음 명령은 File의 Staged 상태를 `HEAD` 기준으로 되돌린다. Working Tree의 수정 내용은 유지한다.

```bash
git restore --staged <file>
git status
```

SourceTree에서는 Staged File을 Unstaged 영역으로 옮기는 동작에 해당한다.

### Working Tree 변경 폐기

다음 명령은 Working Tree의 File을 Staging Area의 내용으로 복원한다.

```bash
git diff -- <file>
git restore <file>
```

저장하지 않은 변경은 사라질 수 있다. 실행 전에 `git diff`를 확인하고 보존할 내용이 있으면 Commit이나 Stash로 저장한다.

특정 Commit의 File만 가져올 수도 있다.

```bash
git restore --source=<commit> -- <file>
```

이 명령은 Branch 전체를 해당 Commit으로 이동시키지 않고 선택한 File의 Working Tree 내용만 바꾼다.

## 7 ) Commit 되돌리기

---

`reset`과 `revert`는 결과가 비슷해 보이지만 History 처리 방식이 다르다.

| 명령 | 현재 Branch Tip | Staging Area | Working Tree | 공유 Branch 사용 |
|---|---|---|---|---|
| `reset --soft` | 대상 Commit으로 이동 | 유지 | 유지 | History가 달라지므로 주의 |
| `reset --mixed` | 대상 Commit으로 이동 | 대상 Commit 기준으로 초기화 | 유지 | History가 달라지므로 주의 |
| `reset --hard` | 대상 Commit으로 이동 | 대상 Commit 기준으로 초기화 | 대상 Commit 기준으로 변경 | 저장하지 않은 변경 손실 가능 |
| `revert` | 새 Commit 추가 | 새 Commit 과정에 따라 반영 | 취소 결과 반영 | 기존 History를 보존하므로 적합 |

### Soft Reset

Commit만 취소하고 변경 내용을 Staging Area와 Working Tree에 유지한다.

```bash
git reset --soft <target-commit>
git status
git diff --staged
```

### Mixed Reset

Option을 생략한 `git reset`은 기본적으로 Mixed Mode이다. Branch를 대상 Commit으로 옮기고 Staging Area를 초기화하지만 Working Tree 변경은 유지한다.

```bash
git reset <target-commit>
git status
git diff
```

### Hard Reset

```bash
git reset --hard <target-commit>
```

Hard Reset은 Branch, Staging Area와 추적 중인 Working Tree File을 대상 Commit 상태에 맞춘다. Commit하지 않은 변경이 사라질 수 있으므로 다음 내용을 먼저 확인한다.

```bash
git status
git diff
git diff --staged
git log --oneline --decorate -n 10
```

필요하면 현재 위치를 임시 Branch로 보존한 뒤 Reset한다.

```bash
git branch backup-before-reset
```

### Revert

`git revert`는 취소할 Commit의 반대 변경을 적용한 새 Commit을 만든다.

```bash
git revert <commit-to-cancel>
```

기존 Commit이 History에 남으므로 이미 Remote에 공유한 Branch에서 변경을 취소할 때 사용하기 쉽다. 충돌이 발생하면 File을 수정하고 Stage한 뒤 작업을 계속하거나 중단한다.

```bash
git add <resolved-file>
git revert --continue
```

```bash
git revert --abort
```

## 8 ) Stash로 변경 임시 보관

---

Stash는 Commit하기 이른 Working Tree와 Staging Area의 변경을 임시로 저장하고 현재 Branch의 작업 공간을 정리할 때 사용한다.

```bash
git stash push -m "temporary work"
git status
```

기본 Stash에는 추적 중인 File의 Staged·Unstaged 변경이 들어간다. Untracked File은 기본 대상이 아니며 필요할 때 `-u`를 명시한다.

```bash
git stash push -u -m "include untracked files"
```

저장된 목록과 변경 내용을 확인한다.

```bash
git stash list
git stash show --patch stash@{0}
```

`apply`는 Stash를 적용한 뒤 목록에 남긴다. Stage 상태까지 복원하려면 `--index`를 사용할 수 있다.

```bash
git stash apply stash@{0}
git stash apply --index stash@{0}
```

더 이상 필요하지 않은 Stash를 삭제한다.

```bash
git stash drop stash@{0}
```

`pop`은 적용에 성공하면 해당 Stash를 목록에서 제거한다.

```bash
git stash pop stash@{0}
```

Stash 적용 중에도 현재 Branch의 변경과 충돌할 수 있다. 적용 후 `git status`와 Diff를 확인한다.

## 9 ) Branch와 `HEAD`

---

> **Branch**
>
> Commit을 가리키며 새 Commit이 만들어질 때 함께 이동하는 Reference이다.

Branch는 Project File을 통째로 복사한 Directory가 아니다. 여러 작업 흐름이 서로 다른 Commit을 가리키도록 분기한다.

```text
              D──E  feature/login
             /
A──B──C───────────  main
```

현재 Branch와 목록을 확인한다.

```bash
git branch --show-current
git branch
```

Branch를 만들고 전환한다.

```bash
git branch feature/login
git switch feature/login
```

생성과 전환을 동시에 수행할 수 있다.

```bash
git switch -c feature/payment
```

기존 환경에서는 다음 `checkout` 명령도 계속 볼 수 있다.

```bash
git checkout feature/login
git checkout -b feature/payment
```

`checkout`은 Branch 전환과 File 복구를 모두 담당하는 오래된 범용 명령이다. 새 문서에서는 의도가 분명한 `switch`와 `restore`를 우선 사용한다.

특정 Commit을 직접 Checkout하면 `HEAD`가 Branch가 아닌 Commit을 가리키는 Detached HEAD 상태가 될 수 있다. 이 상태에서 만든 Commit을 보존하려면 해당 위치에서 Branch를 생성한다.

```bash
git switch -c save-detached-work
```

### Branch 삭제

현재 Checkout한 Branch는 삭제할 수 없다. 다른 Branch로 이동한 뒤 병합이 끝난 Branch를 삭제한다.

```bash
git switch main
git branch -d feature/login
```

`-d`는 병합되지 않은 Commit이 있으면 삭제를 거절한다. `-D`는 이를 무시하는 강제 삭제이므로 보존할 Commit이 없는지 확인하지 않고 사용하지 않는다.

## 10 ) Merge

---

Merge는 현재 Branch에 다른 Branch의 History를 통합한다. `feature/login`을 `main`에 합치려면 결과를 받을 `main`으로 먼저 이동한다.

```bash
git switch main
git merge feature/login
```

### Fast-forward Merge

Branch가 분기된 뒤 `main`에 새 Commit이 없다면 `main` Reference를 `feature/login`의 Tip까지 앞으로 이동할 수 있다.

```text
병합 전

A──B  main
    \
     C──D  feature/login

병합 후

A──B──C──D  main, feature/login
```

Fast-forward Merge는 별도 Merge Commit을 만들지 않아도 된다.

### Merge Commit

두 Branch가 각각 새 Commit을 가진 경우 Git은 공통 조상을 기준으로 변경을 통합하고 Merge Commit을 만들 수 있다.

```text
       C──D  feature/login
      /    \
A──B──E─────M  main
```

특정 Commit을 `git merge <commit>` 대상으로 지정할 수 있지만 해당 Commit 하나의 Patch만 적용하는 작업은 아니다. Git은 지정한 Commit까지 이어지는 History를 현재 Branch와 병합한다. 하나의 Commit 변경만 적용하려는 경우에는 목적을 확인한 뒤 `git cherry-pick <commit>`을 검토한다.

### Merge 충돌

서로 다른 Branch가 같은 File의 같은 영역을 다르게 수정하면 Git이 결과를 자동으로 결정하지 못할 수 있다.

```bash
git status
```

충돌 File에는 다음과 같은 Marker가 생길 수 있다.

```text
<<<<<<< HEAD
현재 Branch의 내용
=======
병합하는 Branch의 내용
>>>>>>> feature/login
```

적용할 내용을 결정하고 Marker를 제거한 뒤 File을 Stage한다.

```bash
git add <resolved-file>
git commit
```

Merge를 완료하지 않고 시작 전으로 돌아가려면 다음 명령을 사용한다.

```bash
git merge --abort
```

`ours`와 `theirs`는 현재 진행 중인 작업 종류와 방향에 따라 가리키는 쪽을 정확히 확인해야 한다. 이름만 보고 자동으로 한쪽 전체를 선택하지 않는다.

## 11 ) Rebase

---

Rebase는 현재 Branch의 Commit을 새로운 Base 위에 다시 적용한다.

```text
변경 전

A──B──C  main
    \
     D──E  feature/login

변경 후

A──B──C  main
       \
        D'──E'  feature/login
```

`feature/login`을 최신 `main` 위로 옮긴다.

```bash
git switch feature/login
git rebase main
```

Rebase는 `D`와 `E`를 그대로 이동하지 않는다. 같은 변경을 새 Parent 위에 적용하여 `D'`, `E'`라는 새 Commit을 만들기 때문에 Object ID가 달라진다.

충돌이 발생하면 File을 수정하고 Stage한 뒤 다음 Commit 적용을 계속한다.

```bash
git status
git add <resolved-file>
git rebase --continue
```

현재 Rebase를 중단하고 시작 전 상태로 돌아간다.

```bash
git rebase --abort
```

이미 여러 사람이 사용하는 Remote Branch의 Commit을 Rebase하면 기존 History와 다른 Commit ID가 만들어진다. 공유하기 전의 개인 작업 Branch에서 사용하는 범위와 팀의 History 정책을 먼저 확인한다.

## 12 ) Non-fast-forward Push와 Merge의 차이

---

Remote Branch에 Local이 가지고 있지 않은 Commit이 있으면 Push가 `non-fast-forward`로 거절될 수 있다.

```text
Local main       A──B──L
                     
Remote main      A──B──R
```

이 오류는 Fast-forward Merge 기능의 실패가 아니다. Remote Branch를 Local Commit까지 단순 이동하면 `R`이 History에서 빠질 수 있으므로 Server가 Update를 거절한 것이다.

Remote 상태를 먼저 가져와 History를 확인한다.

```bash
git fetch origin
git log --oneline --graph --decorate --all
```

팀 정책에 따라 Remote 변경을 Merge하거나 Rebase한 뒤 충돌을 해결하고 다시 Push한다.

```bash
git merge origin/main
```

또는 다음과 같이 현재 Commit을 Remote Branch 위에 다시 적용할 수 있다.

```bash
git rebase origin/main
```

원격 Repository 연결과 Push 전체 흐름은 [GitHub Remote Repository 작업 흐름](/cloud-native-44-github-remote-workflow/)에서 다룬다.

## 전체 정리

---

> **최종 정리**
>
> - SourceTree와 CLI는 같은 Git Repository와 상태를 다루므로 GUI 작업 뒤에도 Git 명령으로 결과를 확인할 수 있다.
>
> - Tag는 Commit Object ID를 바꾸지 않고 특정 Version을 읽기 쉬운 이름으로 가리킨다.
>
> - `git diff`는 Working Tree, Staging Area, Commit과 Branch 중 어떤 두 상태를 비교하는지 구분해야 한다.
>
> - `restore`는 File, `reset`은 Branch와 Index, `revert`는 기존 Commit을 취소하는 새 Commit을 다룬다.
>
> - 기본 Stash는 추적 중인 변경을 저장하며 Untracked File을 포함하려면 `-u`가 필요하다.
>
> - Merge는 History를 통합하고 Rebase는 현재 Branch의 Commit을 새 Base 위에 다시 적용한다.
>
> - Non-fast-forward Push 거절은 Remote에 Local이 가지지 않은 Commit이 있을 때 History 손실을 막기 위해 발생한다.
