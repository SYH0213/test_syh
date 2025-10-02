# PYANNOTEAI_API_KEY API를 사용하는 코드.

from pyannote.audio import Pipeline

# Precision-2 premium speaker diarization service
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-precision-2", token="PYANNOTEAI_API_KEY")

output = pipeline("data/tiro_Test1_4People.wav")  # runs on pyannoteAI servers

# print the result
for turn, speaker in output.speaker_diarization:
    print(f"start={turn.start:.1f}s stop={turn.end:.1f}s {speaker}")
# start=0.2s stop=1.6s SPEAKER_00
# start=1.8s stop=4.0s SPEAKER_01 
# start=4.2s stop=5.6s SPEAKER_00
# ...