# 냠냠건강탐험대 (YumYum Health Explorer)

서울여자대학교 바롬설계프로젝트 4조 **'올바롬'**이 만든 식품 건강 교육 사이드스크롤 러닝 게임.

학생 캐릭터가 학교 → 길거리 → 놀이터 → 집까지 달리며 건강한 음식은 먹고 정크푸드는 피하는 게임입니다. Python + pygame-ce로 제작되었습니다.

---

## 🎮 게임 특징

- **25종 음식 시스템** — 4개 스테이지(학교/길거리/놀이터/집) × 건강 3종·정크 3종 + 어디서나 등장하는 생수
- **물게이지(갈증) 시스템** — 시간이 지나면 물게이지가 감소, 생수로 회복
- **50개 업적 시스템** — 10개 카테고리(진행·콤보·음식·물·HP·스킬·점수 등)
- **4종 랜덤 스킬** — 무적 질주 / 시간 감속 / 젤리 파티 / 점수 폭발
- **음식 도감** — 먹어본 음식은 컬러로, 안 먹은 음식은 흑백 ??? 표시
- **다국어 지원** — 한국어 / English / Tiếng Việt
- **이스터에그 2종** — 타이틀 7번 클릭(교복 색 사이클), 소희 캐릭터 24번 클릭(데이터 초기화)

---

## 🚀 실행 방법

### 1) 빌드된 실행 파일로 실행 (Windows 권장)

[Releases](../../releases) 페이지에서 최신 `냠냠건강탐험대.exe`를 다운로드 → 더블클릭.

> Windows에서 "PC 보호" 경고가 뜨면 **추가 정보 → 실행** 클릭 (미서명 앱이라 정상).

### 2) 소스코드로 직접 실행

```bash
# Python 3.12 이상 권장
pip install -r requirements.txt
python main.py
```

### 3) 직접 빌드하기

```bash
pip install pyinstaller
python -m PyInstaller main.spec --noconfirm
# 결과물: dist/냠냠건강탐험대.exe
```

---

## 🕹 조작법

| 키 | 동작 |
|---|---|
| `SPACE` / `↑` | 점프 (공중에서 한 번 더 누르면 더블점프) |
| `↓` / `S` | 슬라이드 (누르고 있는 동안 유지) |
| `Z` | 스킬 발동 (냠냠게이지 가득 찼을 때) |
| `P` | 일시정지 |
| `ESC` | 메뉴 / 이전 화면 |
| 마우스 휠 / `W`·`S` | 도감·업적 화면 스크롤 |

자세한 게임 정보는 [docs/플레이가이드.md](docs/플레이가이드.md) 참고.
음식 데이터 마스터 시트는 [docs/젤리정보문서.xlsx](docs/젤리정보문서.xlsx).

---

## 📁 프로젝트 구조

```
YumYumHealthExplorer/
├── main.py                  # 진입점
├── game.py                  # Game 클래스, 상태머신
├── player.py                # 플레이어 캐릭터
├── ui.py                    # HUD, 메뉴, 도감, 업적 화면
├── background.py            # 4종 스테이지 배경
├── obstacle.py              # 장애물
├── collectible.py           # 25종 음식 + 하트
├── skill.py                 # 4종 스킬 시스템
├── achievement.py           # 50개 업적
├── debuff.py                # 11종 지속 효과
├── power_up.py              # 자석/방어막
├── particles.py             # 파티클 이펙트
├── sound_manager.py         # 사운드
├── lang.py                  # ko/en/vi 다국어
├── main.spec                # PyInstaller 빌드 스펙
├── team_mate/               # 팀원·캐릭터 일러스트
├── fonts_license/           # 번들 폰트 라이선스
└── docs/                    # 플레이가이드 + 음식 데이터 시트
```

---

## 🛠 기술 스택

- **언어**: Python 3.12+
- **엔진**: pygame-ce 2.5.7
- **빌드**: PyInstaller (단일 .exe 패키징, ~12.6MB)
- **플랫폼**: Windows (소스 자체는 크로스플랫폼)

---

## 👥 크레딧

- **개발·기획·설계·디자인**: 이소희
- **팀**: 서울여자대학교 바롬설계프로젝트 4조 **올바롬**
  - 내영 / 서하 (팀장) / 서현 / 수민 / 투타오

### 번들 폰트
- **학교안심 시간표 R (Hakgyoansim Siganpyo R)** — Tlab신영복체 / 박윤정엔타이포랩 (OFL)
- **Quicksand** — Andrew Paglinawan, Google Fonts (OFL)

---

## 📄 라이선스

이 프로젝트는 **듀얼 라이선스**로 배포됩니다.

- **소스코드** (`.py` 파일, `main.spec` 등): **MIT License** — [LICENSE](LICENSE) 참조
- **게임 에셋** (일러스트, 아이콘, 인게임 그래픽, 향후 음원 등): **CC BY-NC 4.0** — [LICENSE-ASSETS](LICENSE-ASSETS) 참조
- **번들 폰트**: 원 라이선스(SIL Open Font License) 유지 — [fonts_license/](fonts_license/) 참조

상업적 사용 또는 라이선스 외 별도 권한이 필요한 경우 저장소 소유자에게 문의해주세요.
