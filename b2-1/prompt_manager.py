"""나만의 프롬프트 관리 (Prompt Vault CLI)

터미널에서 메뉴 번호를 입력해 프롬프트를 추가/조회/검색/즐겨찾기 관리하는 콘솔 프로그램.
"""

CATEGORIES = ["텍스트 생성", "이미지 생성", "영상 생성", "페르소나", "자동화", "기타"]

# 이전 미션(b1-1: 앱 컨버전 카피 에이전트 "프로모" 프롬프트 패키지)에서 작성한
# 프롬프트를 기본 데이터로 등록한다.
DEFAULT_PROMPTS = [
    {
        "title": "앱스토어 메타데이터 생성 프롬프트",
        "category": "텍스트 생성",
        "favorite": True,
        "view_count": 0,
        "content": (
            "너는 \"프로모(Promo)\"다. 앱 컨버전·라이프사이클 카피 설계가로, "
            "App Store/Play 메타데이터(제목·부제·키워드·설명) 작성만 담당한다.\n\n"
            "[말투] 차분·정직·간결(한 메시지 = 한 핵심). 과장·미화 없이.\n"
            "[금지] 근거 없는 수치 단정, 다크패턴, 없는 기능 언급.\n"
            "[출력 형식] 로케일별 제목(≤30자)·부제(≤30자)·키워드 필드(≤100자, 쉼표·공백 없음)·설명.\n"
            "키워드는 상상하지 말고 현지어+영어 일반명으로 상위 경쟁 앱을 스캔해 역산한다. "
            "제목·부제에 쓴 단어는 키워드 필드에서 제외한다.\n\n"
            "[앱] Mirror Mirror — 좌우 반전 없는 True Mirror 거울 앱. "
            "차별점: 무반전 얼굴 + 일반 거울 동시 표시(PiP) / 로그인·저장·전송 없음 / 가입 없이 무료.\n\n"
            "이제 한국(kr) App Store 메타데이터를 만들어라."
        ),
    },
    {
        "title": "인앱 모달 시퀀싱 결정 프롬프트",
        "category": "자동화",
        "favorite": False,
        "view_count": 0,
        "content": (
            "너는 \"프로모(Promo)\"다. 오픈 횟수 + 사용자 상태에 따라 어떤 인앱 모달"
            "(온보딩/기능 발견/리뷰 요청/공유/알림 권한/페이월)을 띄울지 결정한다.\n\n"
            "[게이팅 원칙] 한 세션 모달 1개 / 권한·구매·리뷰는 첫 실행 금지(가치 경험 후) / "
            "빈도 제한 + 긍정 순간 트리거 / 완료한 액션 재노출 금지 / 닫기 쉬운 UI.\n"
            "[플랫폼 사실] iOS SKStoreReview는 365일 최대 3회만 노출되며 앱이 빈도를 강제할 수 없다.\n\n"
            "[출력 형식] \"오픈# | 조건(상태) | 띄울 창 | 카피 요지 | 게이팅/이유\" 결정표로 작성한다.\n\n"
            "[앱] Mirror Mirror. 가용 모달=온보딩·기능발견(PiP 스왑·가로 전신·줌)·리뷰요청·공유. "
            "추적 상태=오픈횟수·설치 후 일수·리뷰함·공유함·기능 사용 여부. "
            "무료·무계정이라 페이월·로그인 모달은 없다.\n\n"
            "인앱 모달 시퀀스 결정표를 작성해라."
        ),
    },
    {
        "title": "앱스토어 히어로 스크린샷 이미지 프롬프트",
        "category": "이미지 생성",
        "favorite": False,
        "view_count": 0,
        "content": (
            "A premium App Store screenshot (1290x2796, iPhone portrait) for a face-mirror "
            "app \"Mirror Mirror\".\n"
            "A calm Korean person in their late 20s facing the camera, split vertically down "
            "the center: the LEFT half is a cool flat ordinary mirror reflection, the RIGHT "
            "half is a warm true (non-flipped) reflection — subtly different, symbolizing "
            "\"the mirror you vs the real you\".\n"
            "Bold Korean headline at top: \"남들이 보는 진짜 내 얼굴\". "
            "Small sub-line: \"좌우 반전 없는 거울\".\n"
            "Deep indigo (#5856D6) to blue-gray (#546E7A) gradient background, soft glass "
            "reflections, premium minimal Apple-like aesthetic, clean negative space, sharp "
            "typography. No text distortion, no logos."
        ),
    },
    {
        "title": "프로모(Promo) 페르소나 정의 프롬프트",
        "category": "페르소나",
        "favorite": False,
        "view_count": 0,
        "content": (
            "역할(페르소나)을 정의한다.\n"
            "- 이름: 프로모(Promo)\n"
            "- 직무: 앱 컨버전·라이프사이클 카피 설계가 (스토어 리스팅 + 인앱 모달, 10년차)\n"
            "- 전문 분야: ASO(실검색어 기반)·스토어 메타데이터 현지화 / 온보딩·넛지 시퀀싱\n"
            "- 말투: 차분하고 단단하게, 정직하게, 간결하게(한 메시지 = 한 핵심). 과장·미화 없이.\n"
            "- 금지 사항: 보정·과장 표현, 근거 없는 수치·순위 단정, 다크패턴, 개인정보 언급.\n"
            "- 우선순위: 정확성 > 친절함, 사용자 경험 존중 > 단기 전환.\n\n"
            "이 페르소나를 유지한 채 앱 컨버전 카피 관련 질문에 답하라."
        ),
    },
]


MENU = """
=== 나만의 프롬프트 관리 ===
1. 프롬프트 추가
2. 프롬프트 목록
3. 카테고리별 조회
4. 프롬프트 검색
5. 프롬프트 상세 보기
6. 즐겨찾기 관리
7. 즐겨찾기 목록
8. 프롬프트 수정
9. 프롬프트 삭제
10. 조회수 Top 목록
11. JSON으로 저장
12. JSON에서 불러오기
13. 카테고리별 Markdown 내보내기
0. 종료
"""


def input_nonempty(label):
    """공백이 아닌 값을 입력받을 때까지 재입력을 요청한다."""
    while True:
        value = input(label).strip()
        if value:
            return value
        print("입력값이 비어 있습니다. 다시 입력해주세요.")


def show_menu():
    print(MENU)
    return input("선택: ").strip()


def select_category():
    """미리 정의된 카테고리 목록에서 번호로 고르거나, 목록에 없는 이름을 직접 입력받는다."""
    print("카테고리 선택:")
    for i, name in enumerate(CATEGORIES, 1):
        print(f"{i}) {name}")
    while True:
        raw = input("선택: ").strip()
        if not raw:
            print("입력값이 비어 있습니다. 다시 입력해주세요.")
            continue
        if raw.isdigit() and 1 <= int(raw) <= len(CATEGORIES):
            return CATEGORIES[int(raw) - 1]
        return raw  # 목록에 없는 카테고리를 직접 입력한 경우


def add_prompt(prompts):
    print("\n=== 프롬프트 추가 ===")
    title = input_nonempty("제목: ")
    content = input_nonempty("내용: ")
    category = select_category()
    prompts.append(
        {
            "title": title,
            "content": content,
            "category": category,
            "favorite": False,
            "view_count": 0,
        }
    )
    print("\n프롬프트가 추가되었습니다!")


# --- 아래 기능들은 이후 커밋에서 순차적으로 구현한다 ---


def format_prompt_line(index, prompt):
    star = " ⭐" if prompt["favorite"] else ""
    return f"{index}. [{prompt['category']}] {prompt['title']}{star}"


def show_list(prompts):
    print("\n=== 프롬프트 목록 ===")
    if not prompts:
        print("등록된 프롬프트가 없습니다.")
        return
    for i, prompt in enumerate(prompts, 1):
        print(format_prompt_line(i, prompt))
    print(f"\n총 {len(prompts)}개의 프롬프트")


def get_all_categories(prompts):
    """미리 정의된 카테고리에 실제 등록된(직접 입력한) 카테고리를 이어붙인다."""
    categories = list(CATEGORIES)
    for prompt in prompts:
        if prompt["category"] not in categories:
            categories.append(prompt["category"])
    return categories


def show_by_category(prompts):
    print("\n=== 카테고리별 조회 ===")
    categories = get_all_categories(prompts)
    for i, name in enumerate(categories, 1):
        print(f"{i}) {name}")
    raw = input("선택: ").strip()
    if not raw.isdigit() or not (1 <= int(raw) <= len(categories)):
        print("잘못된 번호입니다.")
        return

    selected = categories[int(raw) - 1]
    matched = [(i, p) for i, p in enumerate(prompts, 1) if p["category"] == selected]

    print(f"\n[{selected}] 카테고리 프롬프트:")
    if not matched:
        print("해당 카테고리에 프롬프트가 없습니다.")
        return
    for i, prompt in matched:
        print(format_prompt_line(i, prompt))
    print(f"\n총 {len(matched)}개의 프롬프트")


def search_prompt(prompts):
    print("\n=== 프롬프트 검색 ===")
    keyword = input_nonempty("검색어: ")
    keyword_lower = keyword.lower()
    matched = [
        (i, p)
        for i, p in enumerate(prompts, 1)
        if keyword_lower in p["title"].lower() or keyword_lower in p["content"].lower()
    ]

    print("\n검색 결과:")
    if not matched:
        print("검색 결과가 없습니다.")
        return
    for i, prompt in matched:
        print(format_prompt_line(i, prompt))
    print(f"\n{len(matched)}개의 프롬프트를 찾았습니다.")


def get_prompt_by_number(prompts, raw_number):
    if not raw_number.isdigit():
        return None
    index = int(raw_number) - 1
    if 0 <= index < len(prompts):
        return prompts[index]
    return None


def show_detail(prompts):
    print("\n=== 프롬프트 상세 보기 ===")
    raw = input("번호 입력: ").strip()
    prompt = get_prompt_by_number(prompts, raw)
    if prompt is None:
        print("잘못된 번호입니다.")
        return

    prompt["view_count"] += 1
    star = " ⭐" if prompt["favorite"] else " (없음)"
    divider = "─" * 30
    print(f"\n{divider}")
    print(f"제목: {prompt['title']}")
    print(f"카테고리: {prompt['category']}")
    print(f"즐겨찾기:{star}")
    print(divider)
    print("내용:")
    print(prompt["content"])
    print(divider)


def toggle_favorite(prompts):
    print("\n=== 즐겨찾기 관리 ===")
    raw = input("프롬프트 번호 입력: ").strip()
    prompt = get_prompt_by_number(prompts, raw)
    if prompt is None:
        print("잘못된 번호입니다.")
        return

    prompt["favorite"] = not prompt["favorite"]
    if prompt["favorite"]:
        print(f"'{prompt['title']}' 프롬프트를 즐겨찾기에 추가했습니다!")
    else:
        print(f"'{prompt['title']}' 프롬프트를 즐겨찾기에서 해제했습니다!")


def show_favorites(prompts):
    print("\n=== 즐겨찾기 목록 ===")
    matched = [(i, p) for i, p in enumerate(prompts, 1) if p["favorite"]]
    if not matched:
        print("즐겨찾기한 프롬프트가 없습니다.")
        return
    for i, prompt in matched:
        print(format_prompt_line(i, prompt))
    print(f"\n총 {len(matched)}개의 즐겨찾기")


def edit_prompt(prompts):
    print("\n=== 프롬프트 수정 ===")
    raw = input("수정할 번호 입력: ").strip()
    prompt = get_prompt_by_number(prompts, raw)
    if prompt is None:
        print("잘못된 번호입니다.")
        return

    print("변경하지 않으려면 빈 값으로 Enter를 누르세요.")
    new_title = input(f"제목 [{prompt['title']}]: ").strip()
    new_content = input(f"내용 [{prompt['content'][:20]}...]: ").strip()
    change_category = input("카테고리를 변경하시겠습니까? (y/N): ").strip().lower()

    if new_title:
        prompt["title"] = new_title
    if new_content:
        prompt["content"] = new_content
    if change_category == "y":
        prompt["category"] = select_category()

    print("\n프롬프트가 수정되었습니다!")


def delete_prompt(prompts):
    print("\n=== 프롬프트 삭제 ===")
    raw = input("삭제할 번호 입력: ").strip()
    prompt = get_prompt_by_number(prompts, raw)
    if prompt is None:
        print("잘못된 번호입니다.")
        return

    confirm = input(f"'{prompt['title']}'을(를) 삭제할까요? (y/N): ").strip().lower()
    if confirm != "y":
        print("삭제를 취소했습니다.")
        return

    prompts.remove(prompt)
    print("프롬프트가 삭제되었습니다.")


def show_top(prompts):
    print("(조회수 Top 목록 기능은 이후 커밋에서 구현 예정입니다)")


def save_to_json(prompts):
    print("(JSON 저장 기능은 이후 커밋에서 구현 예정입니다)")


def load_from_json(prompts):
    print("(JSON 불러오기 기능은 이후 커밋에서 구현 예정입니다)")


def export_markdown(prompts):
    print("(Markdown 내보내기 기능은 이후 커밋에서 구현 예정입니다)")


def main():
    prompts = [dict(p) for p in DEFAULT_PROMPTS]

    actions = {
        "1": add_prompt,
        "2": show_list,
        "3": show_by_category,
        "4": search_prompt,
        "5": show_detail,
        "6": toggle_favorite,
        "7": show_favorites,
        "8": edit_prompt,
        "9": delete_prompt,
        "10": show_top,
        "11": save_to_json,
        "12": load_from_json,
        "13": export_markdown,
    }

    while True:
        choice = show_menu()
        if choice == "0":
            print("프로그램을 종료합니다.")
            break
        action = actions.get(choice)
        if action is None:
            print("잘못된 번호입니다. 메뉴에서 다시 선택해주세요.")
            continue
        action(prompts)


if __name__ == "__main__":
    main()
