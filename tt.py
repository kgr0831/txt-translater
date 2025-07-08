import os
from google.cloud import translate_v2 as translate
import json
import time 

GOOGLE_APPLICATION_CREDENTIALS = "tidy-tract-434706-d1-bde2489a7281.json" #토큰 파일명

INPUT_FOLDER = "input_texts"  # 번역할 파일
OUTPUT_FOLDER = "translated_texts_google"  # 번역된 파일
CHUNK_SIZE = 100 # 한 청크당 전송할 사이즈
DELAY_BETWEEN_REQUESTS = 0.2 # 지연시간

def translate_text_google_chunk(texts, translator_client):
    if not texts:
        return []

    try:
        results = translator_client.translate(
            texts,
            source_language='en', # 번역어
            target_language='ko', # 번역된 언어
            format_='text'
        )
        return [result['translatedText'] for result in results]
    except Exception as e:
        print(f"Google Translate API 배치 번역 중 오류 발생: {e}")
        return [f"[번역 실패: {t}]" for t in texts]

def main():
    if not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
        print(f"오류: Google Cloud Service Account 키 파일 '{GOOGLE_APPLICATION_CREDENTIALS}'을(를) 찾을 수 없습니다.")
        print("Google Cloud Platform에서 키 파일을 다운로드하여 올바른 경로에 두거나, 코드의 경로를 수정해주세요.")
        return
    
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS
    
    try:
        translator_client = translate.Client()
    except Exception as e:
        print(f"Google Cloud Translation 클라이언트 초기화 실패: {e}")
        print("API 키 파일이 유효한지, 그리고 'Cloud Translation API'가 활성화되었는지 확인해주세요.")
        return

    if not os.path.exists(INPUT_FOLDER):
        print(f"오류: 입력 폴더 '{INPUT_FOLDER}'를 찾을 수 없습니다.")
        print(f"'{INPUT_FOLDER}' 폴더를 생성하고 번역할 텍스트 파일을 넣어주세요.")
        return

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print(f"'{INPUT_FOLDER}' 폴더에서 '.txt' 파일을 찾아 Google 번역으로 번역합니다.")
    print(f"한 번에 {CHUNK_SIZE}줄씩 묶어 번역하며, 각 요청 사이 {DELAY_BETWEEN_REQUESTS}초 지연됩니다.")

    processed_files_count = 0
    for filename in os.listdir(INPUT_FOLDER):
        if filename.endswith(".txt"):
            filepath = os.path.join(INPUT_FOLDER, filename)
            output_filepath = os.path.join(OUTPUT_FOLDER, filename) 
            
            print(f"\n--- 파일 번역 시작: {filename} ---")
            
            translated_lines = []
            lines_to_translate_chunk = []
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    
                    for i, line in enumerate(all_lines):
                        stripped_line = line.strip()
                        
                        if stripped_line:
                            lines_to_translate_chunk.append(stripped_line)
                        else:
                            translated_lines.append(line)
                            continue

                        if len(lines_to_translate_chunk) == CHUNK_SIZE or i == len(all_lines) - 1:
                            if lines_to_translate_chunk:
                                translated_chunk_results = translate_text_google_chunk(lines_to_translate_chunk, translator_client)
                                for translated_segment in translated_chunk_results:
                                    translated_lines.append(translated_segment + '\n') 
                                
                                lines_to_translate_chunk = [] 
                                
                                if DELAY_BETWEEN_REQUESTS > 0:
                                    time.sleep(DELAY_BETWEEN_REQUESTS)
                            
                        if (i + 1) % 50 == 0:
                            print(f"  {i + 1}줄 처리 중...")

                with open(output_filepath, 'w', encoding='utf-8') as f_out:
                    f_out.writelines(translated_lines)
                print(f"--- 파일 번역 완료: {filename} -> {output_filepath} ---")
                processed_files_count += 1

            except FileNotFoundError:
                print(f"오류: 파일 '{filepath}'를 찾을 수 없습니다.")
            except Exception as e:
                print(f"파일 '{filepath}' 처리 중 예상치 못한 오류 발생: {e}")

    if processed_files_count == 0:
        print("번역할 '.txt' 파일을 찾지 못했습니다. 'input_texts' 폴더에 파일을 넣어주세요.")
    else:
        print(f"\n총 {processed_files_count}개의 파일 번역을 완료했습니다.")
        print(f"번역된 파일은 '{OUTPUT_FOLDER}' 폴더에 저장되었습니다.")

if __name__ == "__main__":
    main()