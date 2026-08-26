import os
import streamlit as st
import google.generativeai as genai
import streamlit.components.v1 as components

# 페이지 설정
st.set_page_config(page_title="AI 영단어 학습 앱", page_icon="📚", layout="centered")

# 🔒 [보안 유지] Streamlit Secrets를 통해 안전하게 API 키 로드
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("⚠️ API 키 설정이 필요합니다. Streamlit Cloud의 Secrets 설정에 GEMINI_API_KEY를 등록해 주세요.")

# 저장할 특정 폴더 지정 (바탕화면의 English_Notes 폴더)
desktop_path = os.path.join(os.path.expanduser("~"), "OneDrive", "Documents", "Desktop")
SAVE_DIR = os.path.join(desktop_path, "English_Notes")

# 폴더가 없으면 자동으로 생성
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

st.title("📚 AI 영단어 학습 앱 (스마트폰 최적화)")
st.write("단어를 검색한 뒤, 대화문 또는 소설문 음성 버튼을 눌러 들어보세요.")

# 사용자 입력
word_input = st.text_input("영단어 입력 (예: irrevocable):", "")

# 세션 스테이트 초기화
if "result_text" not in st.session_state:
    st.session_state.result_text = ""
if "current_word" not in st.session_state:
    st.session_state.current_word = ""

if st.button("생성하기") and word_input:
    with st.spinner("AI가 멋진 예문과 대화문을 작성 중입니다..."):
        try:
            # Gemini 3.6 모델 적용 및 대화 형식 유도 프롬프트
            model = genai.GenerativeModel(
                model_name="gemini-3.6-flash",
                system_instruction="""You are an expert English teacher and writer. 
                When given an English word, provide the output strictly in this format with clear headings:
                1. Meaning in Korean
                2. Dialogue (Provide a natural dialogue between native speakers using the word, using ONLY 'A:' and 'B:' for speakers, including English lines and Korean translations)
                3. Novel Passage (Provide a sophisticated literary/novel passage using the word, including English and Korean translation)
                Return the response in clean Markdown format.""",
                generation_config={"response_mime_type": "text/plain"}
            )
            
            prompt = f"Word: {word_input}"
            response = model.generate_content(prompt)
            
            st.session_state.result_text = response.text
            st.session_state.current_word = word_input.strip()

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")

# 결과가 있으면 화면에 보여주기
if st.session_state.result_text:
    st.markdown(f"## ✨ {st.session_state.current_word}")
    st.markdown(st.session_state.result_text)
    
    st.markdown("---")
    
    # 원문 전체 텍스트를 자바스크립트로 안전하게 전달하기 위한 처리
    raw_text = st.session_state.result_text.replace('`', '').replace('"', '\\"').replace("'", "\\'")
    
    # 🔊 음성 재생 버튼 생성 (모바일 잘림 방지를 위해 height를 넉넉하게 160으로 설정)
    tts_html = f"""
    <div style="margin-bottom: 10px; display: flex; gap: 10px; flex-wrap: wrap;">
        <button onclick="speakDialogueToneShift()" style="background-color: #4CAF50; color: white; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; font-size: 15px; font-weight: bold;">
            👥 대화문 입체 톤으로 듣기
        </button>
        <button onclick="speakNovel()" style="background-color: #2196F3; color: white; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; font-size: 15px; font-weight: bold;">
            📖 영어 소설문만 듣기
        </button>
        <button onclick="stopSpeech()" style="background-color: #f44336; color: white; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; font-size: 15px; font-weight: bold;">
            ⏹️ 중지
        </button>
    </div>

    <script>
    const fullMarkdownText = `{raw_text}`;

    function extractEnglishLines(textSection) {{
        let lines = textSection.split('\\n');
        let englishLines = [];
        
        for (let line of lines) {{
            let hasKorean = /[가-힣]/.test(line);
            let hasEnglish = /[a-zA-Z]/.test(line);
            
            if (hasEnglish && !hasKorean) {{
                let cleaned = line.replace(/^[#*\\-\\d\\.\\s]+/, '').replace(/^[A-Za-z]\\s*:/, '').trim();
                if (cleaned.length > 0) {{
                    englishLines.push(cleaned);
                }}
            }}
        }}
        return englishLines;
    }}

    function speakDialogueToneShift() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            
            let dialoguePart = fullMarkdownText;
            let dIndex = fullMarkdownText.indexOf('2.');
            let nIndex = fullMarkdownText.indexOf('3.');
            
            if (dIndex !== -1 && nIndex !== -1) {{
                dialoguePart = fullMarkdownText.substring(dIndex, nIndex);
            }} else if (dIndex !== -1) {{
                dialoguePart = fullMarkdownText.substring(dIndex);
            }}
            
            let lines = extractEnglishLines(dialoguePart);
            if (lines.length === 0) return;

            let index = 0;
            function speakNextLine() {{
                if (index >= lines.length) return;
                
                let utterance = new SpeechSynthesisUtterance(lines[index]);
                utterance.lang = 'en-US';
                utterance.rate = 0.9;
                
                if (index % 2 === 0) {{
                    utterance.pitch = 1.2;
                }} else {{
                    utterance.pitch = 0.8;
                }}
                
                utterance.onend = function() {{
                    index++;
                    speakNextLine();
                }};
                
                window.speechSynthesis.speak(utterance);
            }}

            speakNextLine();

        }} else {{
            alert('이 브라우저는 음성 출력을 지원하지 않습니다.');
        }}
    }}

    function speakNovel() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            
            let novelPart = "";
            let nIndex = fullMarkdownText.indexOf('3.');
            
            if (nIndex !== -1) {{
                novelPart = fullMarkdownText.substring(nIndex);
            }}
            
            let lines = extractEnglishLines(novelPart);
            let textToRead = lines.join('. ');
            if (!textToRead) textToRead = "No English novel passage found.";

            var utterance = new SpeechSynthesisUtterance(textToRead);
            utterance.lang = 'en-US';
            utterance.rate = 0.85;
            utterance.pitch = 1.0; 
            window.speechSynthesis.speak(utterance);
        }} else {{
            alert('이 브라우저는 음성 출력을 지원하지 않습니다.');
        }}
    }}

    function stopSpeech() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
        }}
    }}
    </script>
    """
    components.html(tts_html, height=160)

# 1️⃣ [기존 코드 주석 처리] - 실행되지 않고 보관만 해둡니다 (나중에 쓰실 때 #만 지우면 다시 살아납니다)
# target_word = st.session_state.current_word
# file_name = f"{target_word.lower()}_note.md"
# file_path = os.path.join(SAVE_DIR, file_name)
#
# with open(file_path, "w", encoding="utf-8") as f:
#     f.write(f"# 영단어 학습 노트: {target_word}\n\n")
#     f.write(st.session_state.result_text)
#
# st.success(f"💾 저장이 완료되었습니다!\n- 저장 폴더: `{SAVE_DIR}`\n- 파일명: `{file_name}`")


# 2️⃣ [새로운 다운로드 버튼 코드] - 지금 바로 기기로 다운로드할 수 있게 실행되는 코드
# 1. 파일 이름과 내용 준비
try:
  target_word = st.session_state.current_word
except:
  target_word = "note"

file_name = f"{target_word.lower()}_note.md"
note_content = (
    f"# 영단어 학습 노트: {target_word}\n\n"
    + st.session_state.get("result_text", "")
)

# 2. 버튼을 좌우로 나란히 배치 (기기 다운로드 + 클라우드 저장)
col1, col2 = st.columns(2)

with col1:
  st.download_button(
      label="📥 기기에 다운로드",
      data=note_content,
      file_name=file_name,
      mime="text/markdown",
  )

with col2:
  if st.button("☁️ 클라우드에 저장"):
    if not os.path.exists(SAVE_DIR):
      os.makedirs(SAVE_DIR)
    file_path = os.path.join(SAVE_DIR, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
      f.write(f"# 영단어 학습 노트: {target_word}\n\n")
      f.write(st.session_state.get("result_text", ""))
    st.success("클라우드 저장 완료!")

# 3. 사이드바에 저장된 노트 목록 및 인쇄 기능 보기
st.sidebar.markdown("---")
st.sidebar.subheader("📁 저장된 노트 보관함")
st.sidebar.write(f"폴더 위치:\n`{SAVE_DIR}`")

if os.path.exists(SAVE_DIR):
  saved_files = os.listdir(SAVE_DIR)
  if saved_files:
    st.sidebar.write(f"총 저장된 파일: {len(saved_files)}개")
    selected_file = st.sidebar.selectbox("파일 선택하여 보기", saved_files)

    if selected_file:
      with open(
          os.path.join(SAVE_DIR, selected_file), "r", encoding="utf-8"
      ) as f:
        content = f.read()
      st.sidebar.markdown("---")
      st.sidebar.markdown(content)

      # 🖨️ 사이드바 인쇄 버튼
      print_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; max-width: 800px; margin: 0 auto;">
            <h3 style="color: #333;">📖 학습 노트: {selected_file}</h3>
            <hr style="border: 1px solid #ddd; margin-bottom: 20px;">
            <div style="white-space: pre-wrap; font-size: 16px; color: #111;">{content}</div>
        </div>
        <script>
            window.print();
        </script>
        """

      if st.sidebar.button("🖨️ 이 노트 프린트하기"):
        components.html(print_html, height=400)
