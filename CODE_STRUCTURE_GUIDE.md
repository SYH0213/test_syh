schemas.py
-> modules/
 1. `E:\github\Minute\minute_code\core_processing\`
   2. `E:\github\Minute\minute_code\chatbot\`
   3. `E:\github\Minute\minute_code\ui\`
   4. `E:\github\Minute\minute_code\utils\`


# 리팩토링 아키텍처 가이드

## 1. 문제 인식: 왜 이 구조가 필요한가?

기존 코드는 LLM이 생성한 초기 프로토타입을 기반으로 빠르게 기능을 확장하고 파이프라인을 구축했습니다. 이로 인해 다음과 같은 문제가 발생했습니다.

- **검증의 어려움**: 각 기능이 단일 책임 원칙을 따르지 않고 강하게 결합되어 있어, 특정 기능 하나만 독립적으로 테스트하기가 매우 어렵습니다.
- **유지보수의 어려움**: 코드 한 부분의 수정이 예상치 못한 다른 부분에 영향을 미치는 '사이드 이펙트'가 발생할 확률이 높습니다.
- **확장의 어려움**: 새로운 기능(예: 다른 STT 모델)을 추가하거나 기존 기능을 교체하려면 코드의 여러 부분을 동시에 수정해야 합니다.

이 가이드는 이러한 문제를 해결하고, **지속 가능하고, 테스트 가능하며, 확장하기 쉬운 코드 구조**를 만들기 위해 작성되었습니다.

---

## 2. 핵심 원칙: 어떻게 코드를 채워야 하는가?

각 파일과 폴더는 명확한 '역할'을 가집니다. 코드를 작성할 때, "이 코드는 어떤 역할을 하는가?"를 기준으로 적절한 위치에 작성해야 합니다.

### 📜 `schemas.py`: 데이터 명세서 (공통 언어)

- **역할**: 프로젝트의 모든 부분에서 사용될 데이터의 '형태'와 '구조'를 정의합니다. Pydantic 모델을 사용하여 각 데이터가 어떤 필드와 타입을 가져야 하는지 명시합니다.
- **코드 형태**:
  ```python
  # from pydantic import BaseModel, Field
  # from typing import List

  # class Utterance(BaseModel):
  #     start: float
  #     end: float
  #     speaker: str
  #     text: str

  # class Transcript(BaseModel):
  #     audio_id: str
  #     utterances: List[Utterance]
  ```
- **핵심**: 이곳의 모델들은 모듈과 서비스 간의 '계약서'입니다. 모든 데이터는 이 약속된 형태로 오고 가야 합니다.

### 🧱 `modules/`: 순수 기능 블록 (단일 기능)

- **역할**: "계산을 수행하는 순수한 함수"들의 모음입니다. 외부 세계(파일 시스템, 네트워크, DB)에 직접 접근하지 않으며, 상태를 가지지 않습니다.
- **코드 형태**: 입력(Input)을 받아 계산을 수행하고, 결과(Output)를 반환하는 간단한 함수입니다.
  ```python
  # in modules/textops.py
  # def merge_short_segments(transcript: Transcript, min_duration: float) -> Transcript:
  #     # 짧은 발화들을 합치는 로직
  #     new_utterances = []
  #     # ... 계산 로직 ...
  #     return Transcript(audio_id=transcript.audio_id, utterances=new_utterances)
  ```
- **핵심**: 이 폴더의 함수들은 예측 가능하고 테스트하기 매우 쉽습니다. 동일한 입력에 대해 항상 동일한 출력을 보장해야 합니다.

### 🔌 `adapters/`: 외부 세계와의 연결 통로

- **역할**: 외부 라이브러리나 API(Pyannote, Whisper, OpenAI, ChromaDB 등)를 직접 호출하는 '구체적인 구현 코드'를 포함합니다.
- **코드 형태**: 특정 라이브러리의 함수를 호출하고, 그 결과를 우리 프로젝트의 `schemas.py`에 정의된 데이터 모델로 변환하여 반환합니다.
  ```python
  # in adapters/whisper_openai.py
  # from openai import OpenAI
  # from schemas import Utterance

  # client = OpenAI(api_key="...")

  # def transcribe_audio_chunk(audio_path: str) -> List[Utterance]:
  #     # response = client.audio.transcriptions.create(...)
  #     # ... OpenAI API 호출 및 결과 파싱 ...
  #     # utterances = [Utterance(start=..., text=...), ...]
  #     return utterances
  ```
- **핵심**: 외부 기술이 변경되면 이 폴더 안의 파일만 수정하면 됩니다. 예를 들어, `whisper_openai.py`를 `whisper_local.py`로 교체할 수 있습니다.

###  orchestrator `services/`: 기능들을 엮어 비즈니스 로직 실행

- **역할**: `modules`의 순수 함수와 `adapters`의 외부 연동 코드를 조합하여 의미 있는 비즈니스 로직(워크플로우)을 완성합니다.
- **코드 형태**: 클래스(Class) 형태로 작성되며, 생성자(`__init__`)를 통해 필요한 모듈이나 어댑터를 '주입(Inject)'받습니다.
  ```python
  # in services/stt_service.py
  # from modules import audio_io, textops
  # from adapters import whisper_openai
  # from schemas import Transcript

  # class STTService:
  #     def __init__(self, stt_adapter, audio_module):
  #         self.stt_adapter = stt_adapter # e.g., whisper_openai
  #         self.audio_module = audio_module # e.g., audio_io

  #     def transcribe(self, audio_path: str) -> Transcript:
  #         # 1. 오디오 자르기 (모듈 호출)
  #         chunks = self.audio_module.split_into_chunks(audio_path)
          
  #         # 2. 각 조각을 STT (어댑터 호출)
  #         all_utterances = []
  #         for chunk in chunks:
  #             all_utterances.extend(self.stt_adapter.transcribe_audio_chunk(chunk))

  #         # 3. 결과 정리 (모듈 호출)
  #         # final_transcript = textops.merge_short_segments(...)
  #         return final_transcript
  ```
- **핵심**: "어떤 순서로, 어떤 데이터를 가지고" 각 기능(모듈, 어댑터)을 호출할지 결정하는 '지휘자'입니다.

### 🖥️ `ui/` 및 `main_app.py`: 사용자 인터페이스

- **역할**: 사용자로부터 입력을 받고, `services` 계층을 호출한 뒤, 그 결과를 사용자에게 보여주는 역할만 합니다.
- **코드 형태**: Gradio의 버튼 클릭, 파일 업로드 등의 이벤트 핸들러가 `STTService.transcribe(...)`와 같은 서비스의 메소드를 호출합니다.
- **핵심**: **절대 비즈니스 로직을 포함해서는 안 됩니다.** 오직 `services`를 호출하는 역할만 수행합니다.

### 🧪 `scripts/`: 독립 실행 및 테스트 스크립트

- **역할**: 각 `service`나 `module`의 기능을 독립적으로 실행하고 테스트하기 위한 커맨드 라인 인터페이스(CLI) 스크립트입니다.
- **코드 형태**: `argparse`나 `typer` 같은 라이브러리를 사용하여 커맨드 라인 인자(예: `--audio-path`)를 받고, 해당 `service`를 초기화하여 실행합니다.
  ```python
  # in scripts/run_stt.py
  # import argparse
  # from services.stt_service import STTService
  # from adapters import whisper_openai
  # from modules import audio_io

  # if __name__ == "__main__":
  #     # 1. 인자 파싱 (어떤 오디오? 어떤 모델?)
  #     # 2. 의존성 조립 (STTService에 필요한 어댑터와 모듈을 생성)
  #     stt_service = STTService(stt_adapter=whisper_openai, audio_module=audio_io)
  #     # 3. 서비스 실행
  #     transcript = stt_service.transcribe("path/from/args")
  #     # 4. 결과 출력 (JSON 파일로 저장 등)
  ```
- **핵심**: UI 없이도 각 기능을 빠르게 테스트하고 검증할 수 있게 해주는 '개발자의 가장 친한 친구'입니다.

### ✅ `tests/`: 자동화된 테스트 코드

- **역할**: 코드의 정확성을 자동으로 검증하는 테스트 케이스들을 포함합니다.
- **코드 형태**: `pytest`와 같은 프레임워크를 사용합니다.
  - `unit/`: `modules`의 순수 함수들을 테스트합니다. (예: `test_merge_short_segments`)
  - `contract/`: `services`의 입출력이 `schemas.py`의 약속을 지키는지 검사합니다.
  - `e2e/`: `scripts`를 실행하여 전체 파이프라인이 정상적으로 동작하는지 확인합니다.

---

## 3. 요약: 코드 작성 워크플로우

1.  **데이터 정의 (`schemas.py`)**: 기능에 필요한 데이터 구조를 먼저 정의합니다.
2.  **핵심 로직 구현 (`modules/`)**: 순수한 계산/처리 함수를 만듭니다.
3.  **외부 연동 구현 (`adapters/`)**: 외부 API/라이브러리 호출 코드를 작성합니다.
4.  **비즈니스 로직 완성 (`services/`)**: 모듈과 어댑터를 엮어 서비스 클래스를 만듭니다.
5.  **독립 실행기 작성 (`scripts/`)**: 방금 만든 서비스를 테스트할 수 있는 CLI 스크립트를 만듭니다.
6.  **UI 연결 (`ui/`)**: 서비스가 정상 동작하는 것을 확인한 후, UI에 연결합니다.
7.  **자동화 테스트 작성 (`tests/`)**: 코드의 안정성을 보장하기 위해 자동화된 테스트를 추가합니다.

이 구조를 따르면 각자 맡은 역할(UI, 핵심 로직, 챗봇 등)에 집중하면서도, 전체 프로젝트의 안정성과 품질을 크게 향상시킬 수 있습니다.
