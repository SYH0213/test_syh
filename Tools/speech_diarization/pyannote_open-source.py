import torch
import os
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()
HF_TOKEN = os.getenv("HUGGINGFACE_ACCESS_TOKEN")
print("HF_TOKEN:", HF_TOKEN)

# Community-1 open-source speaker diarization pipeline
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token=HF_TOKEN
)

# CUDA가 있으면 GPU, 없으면 CPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
pipeline.to(device)

# 현재 실행 중인 코드 파일 기준 절대경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
audio_file = os.path.join(BASE_DIR, "audio.wav")

# 실행
with ProgressHook() as hook:
    output = pipeline(audio_file, hook=hook)

# 결과 출력
for turn, _, speaker in output.itertracks(yield_label=True):
    print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")
