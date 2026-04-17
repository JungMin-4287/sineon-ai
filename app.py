import streamlit as st
import google.generativeai as genai
import time
import random
import re

# ==========================================
# 1. API 키 및 모델 설정
# ==========================================
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
except KeyError:
    st.error("API 키가 설정되지 않았습니다. 클라우드 설정(Secrets)에서 'GEMINI_API_KEY'를 추가해주세요.")
    st.stop()

# ==========================================
# 2. 시스템 프롬프트 (이미지 양식 기반 최적화)
# ==========================================
SYSTEM_PROMPT = """
당신은 울산 '신언중학교'의 '두런두런 울산 탐구생활' 교과 개발 전담 AI입니다. 
선생님의 요청에 따라 '융합프로젝트 개발상황표' 양식에 맞춘 핵심 내용만 간결하게 생성합니다.

[교과 핵심 정체성]
- 예술·체육(음악, 미술, 체육)이 중심 매개체가 되는 전 교과 융합 수업.
- 울산/언양 지역 연계 (인물, 역사, 생활, 문화, 자연환경).

[출력 지침 - 반드시 준수]
1. **간결성**: 불필요한 설명은 빼고 표와 리스트 위주로 작성하세요.
2. **HTML 태그 금지**: <br>, <b> 등의 HTML 태그를 절대 사용하지 마세요. 줄바꿈은 마크다운 형식을 사용합니다.
3. **지도안 틀 구성**: 아래 [양식]의 항목만 포함하여 작성하세요.

[양식: 융합프로젝트 개발상황표]
1. 기본정보: 프로젝트 주제, 융합교과, 팀원, 핵심 질문
2. 수업 소개: (1, 2, 3번으로 요약)
3. 핵심 아이디어 & 학습목표: (3가지 내외)
4. 성취기준: [교과 코드] 형태의 명확한 문장
5. 개발 내용체계: 지식 및 이해 / 기능 및 과정 / 가치 및 태도 (표 형태)
6. 성취수준: 상/중/하 핵심 요약
7. 수업 흐름도: (차시, 수업 주제, 세부 활동 내용, 담당 교사 요약)

[톤앤매너]
- 교육 공학적이며 논리적인 톤.
- 중학교 1~3학년 수준에 적합한 활동.
"""

# ==========================================
# 3. Streamlit UI 및 세션 관리
# ==========================================
st.set_page_config(page_title="신언중학교 교과 어시스턴트", page_icon="🏫", layout="wide")

with st.sidebar:
    st.header("⚙️ 설정")
    selected_model_alias = st.selectbox(
        "모델 선택",
        ["Gemini 2.5 Pro (최고 성능)", "Gemini 2.5 Flash (성능/속도 균형)", "Gemini 2.0 Flash (초고속)"],
        index=1
    )
    
    model_id_map = {
        "Gemini 2.5 Pro (최고 성능)": "models/gemini-2.5-pro",
        "Gemini 2.5 Flash (성능/속도 균형)": "models/gemini-2.5-flash",
        "Gemini 2.0 Flash (초고속)": "models/gemini-2.0-flash"
    }
    selected_model = model_id_map[selected_model_alias]
    
    if st.button("대화 기록 초기화"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    with st.expander("🛠️ 디버그: 사용 가능한 모델 목록"):
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    st.code(m.name)
        except:
            st.error("목록 불가")

st.title("🏫 두런두런 울산 탐구생활 AI 조수")
st.info("이미지 양식에 맞춘 '융합프로젝트 개발상황표' 핵심 요약을 생성합니다.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "선생님, 반갑습니다! 👏 프로젝트 주제를 말씀해 주시면 이미지의 개발상황표 양식에 맞춰 핵심만 정리해 드릴게요."}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# API 호출 함수
def get_gemini_response_with_retry(prompt, history):
    model = genai.GenerativeModel(
        model_name=selected_model,
        system_instruction=SYSTEM_PROMPT
    )
    chat = model.start_chat(history=history)
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = chat.send_message(prompt, stream=True)
            return response
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                wait_seconds = 30
                match = re.search(r'retry in (\d+)', str(e))
                if match:
                    wait_seconds = int(match.group(1)) + 2
                st.warning(f"⏳ 대기 중... {wait_seconds}초 후 재시도")
                time.sleep(wait_seconds)
            else:
                raise e

# ==========================================
# 4. 사용자 입력 및 답변 생성
# ==========================================
if user_input := st.chat_input("주제를 입력하세요 (예: 1학년 1팀 마두희 축제 탐구)"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        try:
            chat_history = []
            for m in st.session_state.messages[:-1]:
                role = "user" if m["role"] == "user" else "model"
                chat_history.append({"role": role, "parts": [m["content"]]})
            
            response_stream = get_gemini_response_with_retry(user_input, chat_history)
            
            for chunk in response_stream:
                if chunk.text:
                    # <br> 태그 등이 섞여 나올 경우 제거 로직 추가
                    text = chunk.text.replace("<br>", "\n").replace("<BR>", "\n")
                    full_response += text
                    placeholder.markdown(full_response + " ▌")
            
            placeholder.markdown(full_response)
            
        except Exception as e:
            st.error(f"❌ 오류 발생: {str(e)}")
            full_response = "답변 생성 실패."

    st.session_state.messages.append({"role": "assistant", "content": full_response})
