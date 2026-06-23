# 모델실행결과 — 3종 LLM 실행 결과 모음

> 여기에 각 모델의 **동일 입력 실행 결과**를 넣는다. 채점은 `../01-모델비교-선정보고서.md` 점수표로 모인다.
> 동일 입력 원본: `../프롬프트-GPT-Gemini-붙여넣기.md` (STEP 1 → STEP 2)

| 모델 | 채널 | 결과 파일 | 상태 |
|---|---|---|---|
| Claude Opus 4.8 | API (이 세션) | `claude-결과.md` | ✅ 완료(실측, 27/30) |
| GPT-5 (Codex) | **Codex CLI** | `codex-결과.md` | ✅ 완료(실측, 27/30*·비용 임시) |
| Gemini 3.1 Pro (High) | API / Antigravity IDE | `gemini-결과.md` | ✅ 완료(실측, 26/30) |

## 순서
1. `codex-결과.md` / `gemini-결과.md`를 열어 STEP 1·2 실행 결과를 붙여넣고 재현성 표를 채운다.
2. 각 파일 하단 채점표(6축 1~5 + 근거)를 채운다.
3. `../01-모델비교-선정보고서.md`의 GPT·Gemini 칸과 `../README.md` 재현성 표에 점수·기록을 옮긴다.

> 공정성: 세 모델 모두 STEP 1 동일 입력으로 돌린다. Codex/Gemini는 `~/.agents/skills/app-promotion-strategist/SKILL.md`로 프로모가 자동 트리거되지만, **비교 측정은 STEP 1 통째 입력**으로 통일한다.
