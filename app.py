import streamlit as st
import google.generativeai as genai
import time

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

[중점 영역]
1. 울산의 인물과 역사 (항일운동, 언양 3.1 만세운동 등)
2. 울산의 생활과 문화 (지역 축제, 전통시장, 옹기마을 등)
3. 울산의 사회와 자연환경 (산업 환경 문제, SDGs, 생태 복원 등)

[작성 가이드라인]
- 대상: 중학교 1~3학년 (발달 단계 고려)
- 사실성: 울산 및 언양 지역의 지명, 역사에 대해 정확한 정보만 제공할 것.
- 어조: 기관 투자자 리포트 수준의 논리적이고 정량적인 톤을 유지하되, 학생들의 활동은 창의적이고 자기주도적이어야 함.
- 양식: 사용자가 요청한 '세부 계획서(8차시)', '지도서(1차시)', '활동지' 양식을 엄격히 준수할 것.
"""

# ==========================================
# 3. Streamlit UI 및 세션 관리
# ==========================================
st.set_page_config(page_title="신언중학교 교과 어시스턴트", page_icon="🏫", layout="wide")

with st.sidebar:
    st.header("⚙️ 설정")
    # 최신 실존 모델로 라인업 구성
    selected_model_alias = st.selectbox(
        "모델 선택",
        ["Gemini 1.5 Pro (심층 분석용)", "Gemini 2.0 Flash (초고속 응답)"],
        index=0,
        help="Pro는 복잡한 교육과정 설계에 적합하며, Flash는 빠른 초안 작성에 유리합니다."
    )
    
    # 들여쓰기 오류가 났던 부분: model_id_map 정의
    model_id_map = {
        "Gemini 1.5 Pro (심층 분석용)": "gemini-1.5-pro",
        "Gemini 2.0 Flash (초고속 응답)": "gemini-2.0-flash"
    }
    selected_model = model_id_map[selected_model_alias]
    
    if st.button("대화 기록 초기화"):
        st.session_state.messages = []
        st.rerun()

st.title("🏫 두런두런 울산 탐구생활 AI 조수")
st.info("신언중학교 선생님들을 위한 교육과정 설계 도우미입니다. 주제를 입력하시면 계획서부터 활동지까지 생성해 드립니다.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "선생님, 환영합니다! 👏 어떤 주제의 수업 자료를 기획해 드릴까요?"}
    ]

# 이전 대화 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def get_gemini_response(prompt, history):
    model = genai.GenerativeModel(
        model_name=selected_model,
        system_instruction=SYSTEM_PROMPT
    )
    chat = model.start_chat(history=history)
    response = chat.send_message(prompt, stream=True)
    return response

# ==========================================
# 4. 사용자 입력 및 답변 생성
# ==========================================
if user_input := st.chat_input("수업 주제나 양식을 입력하세요..."):
    # 사용자 메시지 표시
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # AI 답변 생성 및 스트리밍
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        try:
            # API 형식에 맞게 대화 기록 변환
            chat_history = []
            for m in st.session_state.messages[:-1]:
                role = "user" if m["role"] == "user" else "model"
                chat_history.append({"role": role, "parts": [m["content"]]})
            
            response_stream = get_gemini_response(user_input, chat_history)
            
            for chunk in response_stream:
                if chunk.text:
                    full_response += chunk.text
                    placeholder.markdown(full_response + " ▌")
            
            placeholder.markdown(full_response)
            
        except Exception as e:
            if "404" in str(e):
                error_msg = f"❌ 모델 호출 오류: 현재 환경에서 '{selected_model}'을(를) 찾을 수 없습니다. (pip install -U google-generativeai 확인 필요)"
            else:
                error_msg = f"❌ 오류 발생: {str(e)}"
            st.error(error_msg)
            full_response = error_msg

    # 답변 저장
    st.session_state.messages.append({"role": "assistant", "content": full_response})
