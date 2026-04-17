import streamlit as st
import google.generativeai as genai
import time
import random
import re  # 정규표현식 사용을 위해 추가

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
# 2. 시스템 프롬프트
# ==========================================
SYSTEM_PROMPT = """
당신은 대한민국 울산광역시 '신언중학교'의 학교자율시간 '두런두런 울산 탐구생활' 교과목 개발을 전담하는 수석 AI 어시스턴트입니다.
선생님이 특정 팀이나 학년, 주제를 입력하면 지정된 양식에 맞추어 창의적이고 실용적인 교육 자료를 생성합니다.

[교과 핵심 정체성]
- 본 교과는 '예술·체육 주제 중심의 전 교과 융합 수업'입니다!
- 모든 지도안과 활동지는 음악, 미술, 체육 활동을 중심 매개체로 하여 국어, 역사, 사회, 과학 등과 융합되어야 합니다.
- (예: 울산 반구천 암각화 문양을 활용한 티셔츠 디자인, 태화강 국가정원 플로깅 및 생태 지도 제작 등)

[작성 가이드라인]
- 대상: 중학교 1~3학년
- 사실성: 울산 및 언양 지역의 지명, 역사에 대해 정확한 정보만 제공할 것.
- 어조: 기관 투자자 리포트 수준의 논리적이고 정량적인 톤을 유지하되, 학생들의 활동은 창의적이어야 함.
- 양식: '세부 계획서(8차시)', '지도서(1차시)', '활동지' 양식을 엄격히 준수할 것.
"""

# ==========================================
# 3. Streamlit UI 및 세션 관리
# ==========================================
st.set_page_config(page_title="신언중학교 교과 어시스턴트", page_icon="🏫", layout="wide")

with st.sidebar:
    st.header("⚙️ 설정")
    
    # 선생님의 디버그 목록에서 확인된 실제 모델들로 업데이트
    selected_model_alias = st.selectbox(
        "모델 선택",
        ["Gemini 2.5 Pro (최고 성능)", "Gemini 2.5 Flash (성능/속도 균형)", "Gemini 2.0 Flash (초고속)"],
        index=1,
        help="목록에서 확인된 최신 모델들입니다."
    )
    
    # 이미지에서 확인된 정확한 모델 ID 매핑
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
        st.caption("현재 API 키로 사용 가능한 모델들입니다.")
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    st.code(m.name)
        except Exception as e:
            st.error("목록을 불러올 수 없습니다.")

st.title("🏫 두런두런 울산 탐구생활 AI 조수")
st.info("신언중학교 선생님들을 위한 교육과정 설계 도우미입니다. 주제를 입력하시면 계획서부터 활동지까지 생성해 드립니다.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "선생님, 환영합니다! 👏 모델 설정을 최신으로 업데이트했습니다. 이제 어떤 주제를 도와드릴까요?"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# API 호출 함수 (정밀 재시도 로직 유지)
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
                wait_seconds = 60
                match = re.search(r'retry in (\d+)', str(e))
                if match:
                    wait_seconds = int(match.group(1)) + 5
                
                st.warning(f"⏳ API 한도 초과. {wait_seconds}초 후 자동 재시도합니다... ({attempt+1}/{max_retries})")
                time.sleep(wait_seconds)
            else:
                raise e

# ==========================================
# 4. 사용자 입력 및 답변 생성
# ==========================================
if user_input := st.chat_input("수업 주제나 양식을 입력하세요..."):
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
                    full_response += chunk.text
                    placeholder.markdown(full_response + " ▌")
            
            placeholder.markdown(full_response)
            
        except Exception as e:
            if "404" in str(e):
                st.error(f"❌ '{selected_model}' 모델을 호출할 수 없습니다. 디버그 목록의 모델명과 일치하는지 다시 확인해주세요.")
            elif "429" in str(e):
                st.error("❌ 한도가 초과되어 재시도에 실패했습니다. 잠시 후 다시 시도해 주세요.")
            else:
                st.error(f"❌ 오류 발생: {str(e)}")
            full_response = "오류로 인해 답변을 생성할 수 없습니다."

    st.session_state.messages.append({"role": "assistant", "content": full_response})
