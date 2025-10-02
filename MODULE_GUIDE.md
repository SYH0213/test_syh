1) 모듈 경계(인터페이스) 먼저 고정하기

아래 공통 데이터 모델을 잡아두면, 팀원들이 서로의 내부 구현을 몰라도 JSON/파이프만 맞춰서 테스트 가능해져.

AudioMeta: {id, path, sr, duration}

DiarizationSegment: {start, end, speaker}

Utterance: {start, end, speaker, text}

Transcript: {audio_id, utterances:[Utterance], language}

Corrections: {policy, notes}

SummaryDoc: {meeting_id, bullets[], decisions[], action_items[]}

IndexRef: {collection, doc_id, meta}

QAQuery: {question, constraints?}

QAAnswer: {answer, sources[], grounded:boolean}

👉 이걸 minute_code/schemas.py (Pydantic)로 고정. 각 모듈은 입력/출력 타입만 책임지고, 내부는 자유.

2) 폴더 구조(역할 기반) + 각 폴더에 “단독 실행 스크립트”

현재 구조를 유지하되, 다음 서브패키지를 분리 명확화 + 단독 러너 추가:

minute_code/
├── main_app.py                # Gradio 앱 (최소 로직)
├── ui/
│   └── app_layout.py          # UI 배선만 (서비스 콜)
├── services/                  # 비즈니스 파사드(서비스 계층)
│   ├── audio_service.py       # 입출력·변환 Orchestrator
│   ├── diar_service.py        # 화자 분리 호출(로컬/클라우드)
│   ├── stt_service.py         # STT 호출, 전처리/후처리
│   ├── llm_service.py         # 교정/요약 LLM 호출 (프롬프트는 utils/prompts)
│   ├── rag_service.py         # 임베딩, 인덱싱, 검색
│   ├── crag_service.py        # Route→Retrieve→Grade→Generate→Validate
│   └── export_service.py      # 파일 저장/서식(hwp/md/pdf 등)
├── modules/                   # 순수 기능 모듈(상태X, 외부의존 최소)
│   ├── audio_io.py            # ffmpeg 변환/클리핑
│   ├── diarization.py         # pyannote/resemblyzer 어댑터
│   ├── stt.py                 # whisper/openai API 어댑터
│   ├── textops.py             # 세그먼트 머지, 노이즈 필터, 짧은 구간 제거
│   ├── summarize.py           # 맵리듀스/섹션 요약 전략
│   ├── metadata.py            # 키워드/의사결정/액션아이템 추출
│   ├── vectorstore.py         # Chroma 어댑터(임베딩/업서트/쿼리)
│   ├── crag_steps.py          # Retrieve/Grade/Generate/Validate 세부 단계
│   └── validators.py          # 환각 검증/근거 체크
├── adapters/                  # 외부벤더/모델별 어댑터(교체 가능)
│   ├── pyannote_precision2.py
│   ├── pyannote_local.py
│   ├── whisper_openai.py
│   ├── gemini_llm.py
│   └── gpt_llm.py
├── utils/
│   ├── config.py
│   ├── file_manager.py
│   ├── prompts.py
│   ├── logging.py
│   └── slugify_rules.py
├── schemas.py                 # ★ 공통 데이터 모델 (Pydantic)
└── scripts/                   # ★ 각 기능 단독 테스트 러너(농축)
    ├── run_diar.py
    ├── run_stt.py
    ├── run_correct.py
    ├── run_summary.py
    ├── run_index.py
    ├── run_query.py
    └── smoke_full.py          # 1분짜리 end-to-end 스모크
tests/
├── data_fixtures/             # 짧은 wav, gold 텍스트, 요약 골든파일
├── unit/                      # 모듈 단위 테스트
├── contract/                  # 서비스 계층 입출력 계약검사
└── e2e/                       # 짧은 오디오로 전체 스모크


UI는 서비스 계층만 호출 → 서비스는 모듈을 조합 → 모듈은 어댑터를 경유해 외부 모델 호출.

각 단계는 scripts/ 아래 러너로 독립 실행 가능해야 함.

README에 이미 있는 “입력→처리→요약→저장→검색/CRAG” 흐름을 이 계층 위에서 그대로 배선.

3) “기능별 단독 테스트 러너” 예시

한 파일만 던져도 돌아가게—이게 팀원 교육·검증에 압도적으로 좋음.

(a) 화자 분리

scripts/run_diar.py

python -m minute_code.scripts.run_diar --audio data/sample.wav --adapter pyannote_precision2 --min_silence 0.2
# 출력: diar_segments.json (DiarizationSegment[])

(b) STT

scripts/run_stt.py

python -m minute_code.scripts.run_stt --audio data/sample.wav --lang ko --force_lang --min_segment 1.0
# 출력: transcript.json (Transcript)


1초 미만 세그먼트 제외, 한국어 강제 등 현재 수정/정책을 러너 옵션으로 노출.

(c) 교정/요약

scripts/run_correct.py, scripts/run_summary.py

python -m minute_code.scripts.run_correct --transcript results/transcript.json --llm gemini
python -m minute_code.scripts.run_summary --transcript results/transcript.json --strategy mapreduce
# 출력: corrected.json, summary.json (SummaryDoc)

(d) 인덱싱 / 질의응답 (CRAG)

scripts/run_index.py, scripts/run_query.py

python -m minute_code.scripts.run_index --doc results/corrected.json --collection "proj_meeting_2025_10_02"
python -m minute_code.scripts.run_query --collection "proj_meeting_2025_10_02" --q "액션아이템 뭐였지?"
# 출력: answers.json (QAAnswer, sources 포함, grounded flag)


내부 단계는 modules/crag_steps.py에 세분화(질문 경로 판단→Retrieve→Relevance Grader→Generate→Hallucination Check). 지금 파이프라인 단계화를 그대로 반영.

4) 팀원이 “코드 안 읽고도” 검증 가능하게: 계약(Contract) & 골든 테스트

계약 테스트 (tests/contract/): 각 서비스의 입력/출력 스키마만 확인.
예: stt_service.transcribe(audio_meta) -> Transcript 가 필수 키/타입을 지키는지.

골든 파일 테스트 (tests/data_fixtures/):

짧은 30–60초 wav 3개(회의/전화/잡음).

기대 출력(golden): 화자 분리 json, Transcript json, 요약 bullet 5개.

회귀 테스트: “어제와 오늘 결과 차이”를 Diff로 보여주기(허용 오차: 예/아니오 기준 or 레벤슈타인 간단 임계).

환각/근거 검증 테스트:

answers.json에 grounded=true가 아니면 실패.

sources에 최소 N개의 본문 스팬이 있어야 통과.

성능 스모크 (scripts/smoke_full.py):

1분 오디오로 End-to-End 2분 내 완료, 결과파일 전부 생성되면 OK.

5) 의존성 주입으로 “빠른 로컬 테스트”

adapters/를 LLM/MODEL 별로 나눴으니, 테스트에선 MockAdapter로 교체:

MockSTT: 세그먼트별로 고정 텍스트 리턴

MockLLM: 정해진 요약/교정 샘플 반환

MockVS: 검색 시 고정 문단 반환
→ 네트워크 끊겨도 unit·contract는 100% 가능.

6) 프롬프트/정책의 버전 고정

utils/prompts.py에 버전 태그를 붙여서(예: SUM_V1, SUM_V2)

결과 파일 메타에 prompt_version을 저장 → 리그레션 원인 추적 쉬워짐. (README/작업기록에 이미 프롬프트 분리 및 CRAG 통합 흐름이 명시됨)

7) 파일/컬렉션 명명 규칙 단일화

utils/slugify_rules.py로 한글→로마자 슬러그 + Chroma 규칙 만족 + UUID 폴백 공통화. (작업기록의 개선사항을 유틸로 승격)

8) 개발자 UX: “테스트 가이드 카드”를 리포에 동봉

CONTRIBUTING.md 최상단에 다음 6개만 적기:

python -m minute_code.scripts.run_diar --audio ...

python -m minute_code.scripts.run_stt --audio ...

python -m minute_code.scripts.run_correct --transcript ...

python -m minute_code.scripts.run_summary --transcript ...

python -m minute_code.scripts.run_index --doc ...

python -m minute_code.scripts.run_query --collection ... --q "..."
→ 역할 담당자별 최소 커버리지와 성공 기준(파일 생성, 스키마 통과, 골든 차이 < 임계)을 명문화.

9) CI(선택): 빠른 신뢰도 확보

PR마다 tests/unit + tests/contract는 항상 돌리고,

tests/e2e는 라벨 달린 PR에서만 실행(외부 API Key 필요 시 스킵).

결과 산출물(요약, 액션아이템)은 artifacts로 업로드해 리뷰어가 직접 눈으로 비교.

핵심 요약

스키마(Pydantic)로 모듈 경계를 먼저 못 박아라.

services(파사드) 계층을 도입해 UI/모듈 사이 결합도를 0에 가깝게 낮춰라.

각 기능은 scripts/ 러너로 단독 실행/단독 디버그 가능하게 하라.

골든·계약 테스트를 넣어 “읽지 않고도 검증”이 가능하게 하라.

프롬프트/정책/슬러그 규칙은 버전·유틸로 고정해 회귀를 잡아라.