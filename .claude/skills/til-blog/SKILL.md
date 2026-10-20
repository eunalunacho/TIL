---
name: til-blog
description: Use when the user runs /til-blog with an _inbox folder name followed by free-form notes, or asks to write and publish a Review (후기·회고·참여기) post with photos to the TIL blog (eunalunacho.github.io/TIL).
---

# TIL 블로그 후기 글 작성·배포

## 개요

`/til-blog <폴더명>` 뒤에 생각나는 대로 쓴 메모와 `_inbox/<폴더명>/`의 사진으로 Review 글을 만든다.
초안을 로컬 미리보기로 보여 주고, 사용자가 OK하면 배포한다. **OK 전에는 커밋·push하지 않는다.**

입력 예:
```
/til-blog hackathon-2026
해커톤에 다녀왔다. 솔직히 이거 될까 싶긴 했는데 선착순이라길래 되겠거니 했다. 근데 가보니까 ...
```
첫 단어가 폴더명, 나머지 전부가 메모다. 폴더가 없으면 `_inbox/` 목록을 보여 주고 묻는다.

## 진행 순서

1. **사진 확인**: `_inbox/<폴더명>/`의 사진을 Read로 전부 본다. 각 사진에 무엇이 있는지 메모와 연결한다.
2. **순서·대표 사진 정하기**: 글 흐름에 맞춰 순서를 정한다. **첫 사진이 목록 썸네일(대표 이미지)이 된다.**
   대표 사진 기준: 행사·장소 전체가 보이는 사진, 주제가 한눈에 보이는 사진 > 인물 클로즈업 > 화면·문서 캡처.
   흔들리거나 어둡거나 글씨만 있는 사진은 첫 사진으로 쓰지 않는다.
3. **슬러그 정하기**: 영문 소문자, 하이픈 1개 이상 (예: `hackathon-2026-review`). 3~5단어.
4. **현재 시각 확인**: PowerShell `Get-Date -Format 'yyyy-MM-dd HH:mm'`. Git Bash의 `TZ=Asia/Seoul date`는 UTC를 돌려주므로 쓰지 않는다.
5. **사진 변환**: `python .claude/skills/til-blog/scripts/prepare_images.py _inbox/<폴더명> <슬러그> . --order 파일1,파일2,...`
   (HEIC 변환, 1600px·300KB 압축, GPS 등 EXIF 제거 → `assets/images/posts/<슬러그>/01.jpg ...`)
6. **글 작성**: `_posts/Blog/<날짜>-<슬러그>.md` (아래 형식·말투·구조)
7. **검사**: `python .claude/skills/til-blog/scripts/check_post.py <글 경로> .` 통과할 때까지 고친다.
8. **미리보기**: `python .claude/skills/til-blog/scripts/build_preview.py <글 경로> . _inbox/<폴더명>/preview.html` 후 `start` 로 연다.
   사용자에게 미리보기를 열었다고 알리고, 아래 "초안 메모"가 있으면 함께 보여 준다.
9. **수정 반복**: 사용자 요청대로 고치고 7~8을 다시 한다.
10. **배포 (OK 받은 뒤에만)**: 글 파일과 `assets/images/posts/<슬러그>/`만 add → 커밋 → push.
    `curl`로 `https://eunalunacho.github.io/TIL/<슬러그>/`를 한 번 확인한다. 아직 404면 Pages 배포 대기 중이라고 알리고 링크를 준다. 반복 폴링하지 않는다.

`_inbox/`는 `.gitignore` 대상이다. 원본 사진과 preview.html은 지우지 않고 남긴다.

## 글 형식

```markdown
---
title: "제목"
date: 2026-10-20 21:30:00 +0900
categories: [Review]
tags: [TIL, 해커톤]
permalink: /hackathon-2026-review/
header:
  teaser: /assets/images/posts/hackathon-2026-review/01.jpg
---

본문 ...

![행사장 입구]({{ "/assets/images/posts/hackathon-2026-review/01.jpg" | relative_url }})
```

- `date`는 글 쓰는 시각(4번에서 확인한 값). 이미지 대체 텍스트는 짧게 쓰고, 사진 아래 캡션은 넣지 않는다.
- 소제목은 `####`을 쓴다.

## 말투 (gookid.tistory.com/2 기준)

- 평서형 `~다`체. 메모가 반말 구어체여도 글은 `~다`체로 정리한다.
- 첫 문단에 계기와 이 글에서 다룰 범위를 쓴다.
- 기대와 달랐던 점, 막혔던 점을 꾸미지 않고 그대로 쓴다. ("솔직히 될까 싶었다")
- 직접 겪은 것은 단정형, 들은 것은 `~라고 한다`, 내 해석은 `~로 이해했다`로 구분한다.
- 여러 항목은 글머리표보다 문장 속 `1) 2) 3)`로 나열한다.
- 참고 링크가 있으면 끝에 `Ref.` 목록으로 붙인다.
- 감탄사·이모지·"~에 대해 알아보겠습니다" 같은 안내 문장을 쓰지 않는다.

## 내용 범위

- **메모에 있는 사실만 쓴다.** 인원, 기간, 수상, 기술 이름, 느낌을 추측으로 채우지 않는다. 메모가 짧으면 글도 짧게 쓴다.
- 메모의 동사와 수치를 그대로 쓴다. "참가했다"를 "주도했다"로, "140명 정도"를 "140명"으로 바꾸지 않는다.
- 사용자에게 추가 질문을 하지 않는다. 단, 아래 두 경우는 초안 아래 **초안 메모**로 한 번에 알린다.
  1) 메모끼리 서로 맞지 않는 내용 (예: "3일"과 "이틀")
  2) 글과 연결되지 않은 사진, 또는 사진이 필요한데 없는 장면

## 구조 (Review)

메모에 해당 내용이 있는 부분만 쓴다. 없는 부분은 소제목째로 뺀다.

1. 도입: 계기와 개요
2. 무엇을 했나: 사용한 기술, 내 역할
3. 기억에 남는 순간
4. 배운 점·아쉬운 점

## 흔한 실수

| 실수 | 바로잡기 |
|---|---|
| OK 전에 커밋·push | 배포는 10단계에서만 |
| `_inbox/` 원본을 add | 글 파일과 변환된 이미지 폴더만 add |
| 미래 시각 date | 4번의 PowerShell 시각 사용, check_post가 잡아냄 |
| 첫 사진을 시간순으로만 고름 | 2번 기준으로 대표 사진을 맨 앞에 |
| 메모에 없는 소감 추가 | 메모 범위 안에서만 |
