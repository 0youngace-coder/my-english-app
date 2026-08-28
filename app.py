import os
import json
import io
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
    st.error("⚠ API 키 설정이 필요합니다. Streamlit Cloud의 Secrets 설정에 GEMINI_API_KEY를 등록해 주세요.")
    st.stop()

# 저장할 특정 폴더 지정 (바탕화면의 English_Notes 폴더)
desktop_path = os.path.join(os.path.expanduser("~"), "OneDrive", "Documents", "Desktop")
SAVE_DIR = os.path.join(desktop_path, "English_Notes")
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR, exist_ok=True)

st.title("📚 AI 영단어 학습 앱 (스마트폰 최적화)")
st.write("단어를 검색한 뒤, 대화문 또는 소설문 음성 버튼을 눌러 들어보세요.")

word_input = st.text_input("영단어 입력 (예: irrevocable):", "")
if "result_text" not in st.session_state:
    st.session_state.result_text = ""
if "current_word" not in st.session_state:
    st.session_state.current_word = ""

if st.button("생성하기") and word_input:
    with st.spinner("AI가 멋진 예문과 대화문을 작성 중입니다..."):
        try:
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

# Word 2007(docx) 생성 함수
def create_docx_bytes(word, content):
    from docx import Document
    from docx.shared import Pt
    doc = Document()
    title = doc.add_heading(f'영단어 학습 노트: {word}', 1)
    # 본문
    for line in content.split('\n'):
        if line.strip():
            p = doc.add_paragraph(line)
            p.style.font.size = Pt(11)
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()

# 결과가 있으면 화면에 보여주기
if st.session_state.result_text:
    st.markdown(f"## ✨ {st.session_state.current_word}")
    st.markdown(st.session_state.result_text)
    st.markdown("---")

    safe_text_json = json.dumps(st.session_state.result_text)
    tts_html = f"""
    <div style="margin-bottom: 10px; display: flex; gap: 10px; flex-wrap: wrap;">
        <button onclick="speakDialogueToneShift()" style="background-color: #4CAF50; color: white; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; font-size: 15px; font-weight: bold;">👥 대화문 입체 톤으로 듣기</button>
        <button onclick="speakNovel()" style="background-color: #2196F3; color: white; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; font-size: 15px; font-weight: bold;">📖 영어 소설문만 듣기</button>
        <button onclick="stopSpeech()" style="background-color: #f44336; color: white; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; font-size: 15px; font-weight: bold;">⏹ 중지</button>
    </div>
    <script>
    const fullMarkdownText = {safe_text_json};
    function extractEnglishLines(textSection) {{
        let lines = textSection.split('\\n'); let englishLines = [];
        for (let line of lines) {{
            let hasKorean = /[가-힣]/.test(line); let hasEnglish = /[a-zA-Z]/.test(line);
            if (hasEnglish &&!hasKorean) {{
                let cleaned = line.replace(/^[#*\\-\\d\\.\\s]+/, '').replace(/^[A-Za-z]\\s*:/, '').trim();
                if (cleaned.length > 0) englishLines.push(cleaned);
            }}
        }}
        return englishLines;
    }}
    function speakDialogueToneShift() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            let dialoguePart = fullMarkdownText; let dIndex = fullMarkdownText.indexOf('2.'); let nIndex = fullMarkdownText.indexOf('3.');
            if (dIndex!== -1 && nIndex!== -1) dialoguePart = fullMarkdownText.substring(dIndex, nIndex);
            else if (dIndex!== -1) dialoguePart = fullMarkdownText.substring(dIndex);
            let lines = extractEnglishLines(dialoguePart); if (lines.length === 0) return; let index = 0;
            function speakNextLine() {{
                if (index >= lines.length) return;
                let utterance = new SpeechSynthesisUtterance(lines[index]); utterance.lang = 'en-US'; utterance.rate = 0.9; utterance.pitch = (index % 2 === 0)? 1.2 : 0.8;
                utterance.onend = function() {{ index++; speakNextLine(); }}; window.speechSynthesis.speak(utterance);
            }} speakNextLine();
        }}
    }}
    function speakNovel() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel(); let novelPart = ""; let nIndex = fullMarkdownText.indexOf('3.');
            if (nIndex === -1) nIndex = fullMarkdownText.indexOf('3'); if (nIndex!== -1) novelPart = fullMarkdownText.substring(nIndex); else novelPart = fullMarkdownText;
            let lines = extractEnglishLines(novelPart); let textToRead = lines.join('. '); if (!textToRead || textToRead.trim().length < 2) return;
            var utterance = new SpeechSynthesisUtterance(textToRead); utterance.lang = 'en-US'; utterance.rate = 0.85; window.speechSynthesis.speak(utterance);
        }}
    }}
    function stopSpeech() {{ if ('speechSynthesis' in window) window.speechSynthesis.cancel(); }}
    </script>
    """
    components.html(tts_html, height=160)

    # --- 저장 버튼 (사진과 동일 구조) ---
    target_word = st.session_state.current_word or "note"
    file_name_md = f"{target_word.lower()}_note.md"
    file_name_docx = f"{target_word.lower()}_note.docx"
    note_content_md = f"# 영단어 학습 노트: {target_word}\n\n" + st.session_state.result_text

    col1, col2 = st.columns(2)
    with col1:
        # 기기에 다운로드 = Word 2007(.docx)로 자동 지정
        try:
            docx_bytes = create_docx_bytes(target_word, st.session_state.result_text)
            st.download_button(
                label="📥 기기에 다운로드",
                data=docx_bytes,
                file_name=file_name_docx,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        except Exception as e:
            # python-docx 없으면 기존 md로 폴백
            st.download_button(
                label="📥 기기에 다운로드",
                data=note_content_md,
                file_name=file_name_md,
                mime="text/markdown",
            )

    with col2:
        if st.button("☁ 클라우드에 저장"):
            file_path = os.path.join(SAVE_DIR, file_name_md)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(note_content_md)
            st.success(f"클라우드 저장 완료!\n`{file_path}`")

# 사이드바 보관함 + 인쇄 (원본 그대로)
st.sidebar.markdown("---")
st.sidebar.subheader("📁 저장된 노트 보관함")
st.sidebar.write(f"폴더 위치:\n`{SAVE_DIR}`")

if os.path.exists(SAVE_DIR):
    saved_files = os.listdir(SAVE_DIR)
    if saved_files:
        st.sidebar.write(f"총 저장된 파일: {len(saved_files)}개")
        selected_file = st.sidebar.selectbox("파일 선택하여 보기", saved_files)
        if selected_file:
            with open(os.path.join(SAVE_DIR, selected_file), "r", encoding="utf-8") as f:
                content = f.read()
            st.sidebar.markdown("---")
            st.sidebar.markdown(content)
            print_html = f"""
                <div style="font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; max-width: 800px; margin: 0 auto;">
                    <h3 style="color: #333;">📖 학습 노트: {selected_file}</h3>
                    <hr style="border: 1px solid #ddd; margin-bottom: 20px;">
                    <div style="white-space: pre-wrap; font-size: 16px; color: #111;">{content}</div>
                </div>
                <script>window.print();</script>
            """
            if st.sidebar.button("🖨 이 노트 프린트하기"):
                components.html(print_html, height=400)
