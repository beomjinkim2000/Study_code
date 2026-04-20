# check-progress — 프로젝트 구현 체크 업데이트

> 사용법: `/check-progress $ARGUMENTS`
> 예: `/check-progress 과제5`

---

## 실행 순서

1. **프로젝트 이름 결정**
   - `$ARGUMENTS` 값을 project_name으로 사용

2. **코드 파일 읽기**
   - `projects/{project_name}/code/` 내 파일 전체 읽기

3. **구현 체크 판단**
   - `study/projects/{project_name}/README.md`의 구현 체크 항목 기준
   - 코드에 해당 구현이 존재하는지 확인
   - `[ ]` / `[x]` 업데이트

4. **README 저장**
   - `study/projects/{project_name}/README.md` 업데이트

5. **결과 출력**
   ```
   [project_name] 구현 체크 결과
   ✅ 완료: N항목
   ⬜ 미완료: N항목
   ```

---

## 판단 기준

고정된 패턴 사용 금지. 아래 순서로 판단:

1. README의 각 `- [ ]` 항목 텍스트를 읽는다
2. 코드 파일에서 그 항목이 설명하는 내용이 실제로 구현되어 있는지 확인한다
3. 구현되어 있으면 `[x]`, 아니면 `[ ]`

미완료로 처리하는 경우:
- 해당 코드 자체가 없음
- `pass`, `...`, `TODO`, `raise NotImplementedError` 등 stub 상태
- 함수/클래스 정의만 있고 본문이 비어있음

---

## 금지

- 코드 내용 수정
- 구현 가이드(구현 순서/단계) 변경 → 플랜모드 필요
