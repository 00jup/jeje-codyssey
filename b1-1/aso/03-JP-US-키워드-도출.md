# JP·US ASO — 키워드·메타데이터 (v2/프로모 실행 · 실데이터 기반)

> 대상: **Mirror Mirror** (id `6760839672`) · 시장: 일본(jp/ja) · 미국(us/en-US)
> 실행: 시스템 프롬프트 `prompts/system-prompt-v2.md` (프로모/v2), 모델 Claude Opus 4.8 · 근거: 2026-06-23 경쟁 스캔(iTunes Search API)
> 키워드 필드 글자 수는 실제 카운트로 검증(100자 규칙).

---

## 🇯🇵 일본 (jp / ja)

**진단**
- 현재 제목: `鏡 · Mirror · 反転した私と本当の私を同時に` → 이미 색인: 鏡·Mirror·反転.
- 검색 성격(실측): `鏡`·`ミラー` 상위는 **Health & Fitness**(化粧直し·ヘアチェック·身だしなみ) — 얼굴 거울 의도가 **가장 깨끗**. 영어 `mirror`는 화면 미러링 혼입.
- 경쟁사 반복어: 手鏡/ハンドミラー, 化粧直し, ヘアチェック, 身だしなみ, メイク, 自撮り/セルフィ, 高画質/4K, 拡大, ナイトモード, ポケットミラー.

**제목(유지 권장)**: `鏡 · Mirror · 反転した私と本当の私を同時に`
**부제안(18/30)**: `すっぴん・メイク・自撮りに、本当の顔` — すっぴん·メイク·自撮り를 색인 부제에 직접 배치.
**키워드 필드(92/100, 쉼표·공백없음)** — 제목 단어(鏡·Mirror·反転) 제외:
```
手鏡,化粧直し,すっぴん,メイク,自撮り,セルフィ,ヘアチェック,身だしなみ,高画質,拡大,前髪,顔,デート,証明写真,面接,ナイトモード,ポケットミラー,左右,全身,4K,コンパクト
```
**설명 방향(전환용)**: 身だしなみ·化粧直し 상황 훅 → 反転없는 진짜 얼굴 + 일반 거울 동시(PiP) → 保存・送信なし(프라이버시) → 無料・登録不要. (일본어로 작성, 단순 번역 금지.)

---

## 🇺🇸 미국 (us / en-US)

**진단**
- 현재 제목: `Mirror · Mirror: Unflipped You` → 이미 색인: Mirror·Unflipped·You.
- 검색 성격(실측): `mirror` 단독은 **화면 미러링(Utilities)과 혼입**. 얼굴 거울 의도는 `selfie mirror`·`real mirror`·`true mirror`로 분리해야 깨끗(True Mirror!·True Visage·Makeup Mirror·Mirror + Selfie 등).
- 경쟁사 반복어: selfie, makeup, pocket/hand mirror, true/real mirror, symmetry, beauty, zoom, brow, grooming, HD, vanity.

**제목(유지)**: `Mirror · Mirror: Unflipped You` (Unflipped/True 차별점 보유)
**부제안(30/30)**: `Selfie, makeup, symmetry check` — selfie·makeup·symmetry를 색인 부제에 직접 배치.
**키워드 필드(99/100, 쉼표·공백없음, 단어 단위)** — 제목 단어(Mirror·Unflipped·You) 제외. Apple이 제목의 "mirror"와 키워드 "true/real"을 조합해 "true mirror"·"real mirror"로 색인:
```
selfie,makeup,pocket,hand,true,real,symmetry,beauty,zoom,brow,face,light,reverse,hd,grooming,vanity
```
**설명 방향(전환용)**: "Your selfies look off?" 훅 → unflipped True Mirror + regular mirror in PiP → no login, no saving, no sending → free, no sign-up. (영어로 작성.)

---

## 공통 메모

- iOS는 설명을 검색 색인하지 않음 → 설명은 전환용. Google Play 동시 출시 시 위 키워드를 본문 설명에 자연스럽게 녹인다.
- 부제는 **스토어에서 현재값 확인 후** 교체(부제는 API 미제공). 키워드 필드 글자 수는 모두 100자 이내로 검증 완료(JP 92 / US 99).
- 다음 시장 확장 시 동일 절차: `prompts/system-prompt-v2.md`의 로케일 레퍼런스·검색 URL → 현지어+영어 2종 스캔 → 장르 혼입 진단 → 키워드 도출.
