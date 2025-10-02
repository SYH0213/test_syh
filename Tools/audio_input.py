import os
from datetime import datetime
import logging
from pydub import AudioSegment


def convert_wav(file_obj, data_dir):
    """파일을 업로드하고 WAV로 변환합니다."""
    if file_obj is None:
        return None

    original_path = file_obj
    filename = os.path.basename(original_path)
    filename_base, ext = os.path.splitext(filename)
    wav_path = os.path.join(data_dir, f"{filename_base}.wav")

    print(original_path)
    print(wav_path)

    try:
        audio = AudioSegment.from_file(original_path)
        audio.export(wav_path, format="wav")
        status = f"'{filename}'이(가) '{os.path.basename(wav_path)}'(으)로 변환되어 저장되었습니다."
    except Exception as e:
        status = f"파일 변환 중 오류 발생: {e}"
        logging.error(status)

    return status


if __name__ == "__main__":
    # 변환할 오디오 파일 경로
    data_dir = "data"
    input_file = "data/project_4p_4m.m4a"  # MP3, M4A, AAC 등 다양한 형식 사용 가능
    # 저장할 WAV 파일 경로

    result = convert_wav(input_file, data_dir)
    if result is not None:
        print(result)
    else:
        print("변환 실패")
    

   