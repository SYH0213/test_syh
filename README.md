# 모듈화

기존에 만들었던 코드를 분해하여 모듈화하고 코드에 문제가 생겼을 시 모듈별로 테스팅 할 수 있도록 합니다.


gpu 사용 안될시
!pip uninstall torch torchvision torchaudio -y
!pip cache purge
!pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

minute_code_alpha/CODE_REVIEW_GUIDE.md에 코드 검토 가이드 있음.

---

## Minute Factory 리팩토링: `minute_code_alpha`

이 프로젝트는 기존 'Minute Factory' 애플리케이션의 코드를 기능별 모듈로 재구성하여 **테스트 용이성, 유지보수성, 확장성**을 높이는 것을 목표로 합니다. `minute_code_alpha` 폴더는 이 리팩토링의 결과물입니다.

### 주요 디렉토리 구조

-   `audio/`: 음성 처리 (화자 분리, STT) 관련 기능
-   `chatbot/`: 회의록 기반 Q&A 챗봇(RAG) 기능
-   `core/`: 파일 입출력 등 핵심 공통 기능
-   `llm/`: LLM을 활용한 텍스트 처리 (교정, 요약, 키워드 추출) 기능
-   `pipelines/`: 전체 작업 흐름을 관리하는 메인 파이프라인
-   `ui/`: Gradio 기반의 사용자 인터페이스(UI)
-   `main.py`: 애플리케이션 실행을 위한 진입점

---

### 실행 방법 (Setup & Run)

#### 1. 가상환경 활성화

프로젝트 실행에 필요한 라이브러리들을 독립된 환경에서 관리합니다. 아래 명령어를 사용하여 가상환경을 활성화하세요.

```bash
# Windows
.\sesacproject\Scripts\activate
```

#### 2. 필요 라이브러리 설치

`requirements.txt` 파일에 명시된 모든 의존성 라이브러리를 설치합니다.

```bash
pip install -r requirements.txt
```

#### 3. 환경 변수 설정 (`.env` 파일)

LLM 및 기타 API를 사용하기 위해 API 키 설정이 필요합니다. 프로젝트 루트(`Module/`)에 있는 `.env` 파일을 열어 아래와 같은 형식으로 자신의 API 키를 입력하세요.

*(만약 `.env` 파일이 없다면, 새로 생성하여 아래 내용을 추가하세요.)*

```
# .env

# 예시: OpenAI API 키
OPENAI_API_KEY="sk-..."

# Hugging Face 토큰 (Pyannote.audio 등)
HF_TOKEN="hf_..."

# 기타 필요한 API 키
# DEEPGRAM_API_KEY="..."
```

#### 4. 애플리케이션 실행

모든 설정이 완료되면, `main.py`를 실행하여 애플리케이션을 시작합니다.

```bash
python main.py
```

애플리케이션이 실행되면, 터미널에 출력되는 URL (예: `http://127.0.0.1:7860`)을 웹 브라우저에서 열어 확인할 수 있습니다.
