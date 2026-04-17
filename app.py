import streamlit as st
import google.generativeai as genai
import time

# ==========================================
# 1. API 키 및 모델 설정
# ==========================================
# Streamlit Cloud의 Secrets에서 API 키를 안전하게 불러옵니다.
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
except KeyError:
    st.error("API 키가 설정되지 않았습니다. 클라우드 설정(Secrets)에서 'GEMINI_API_KEY'를 추가해주세요.")
    st.stop()

# ==========================================
# 2. 시스템 프롬프트 (최적화 버전)
# ==========================================
SYSTEM_PROMPT = """
당신은 대한민국 울산광역시 '신언중학교'의 학교자율시간 '두런두런 울산 탐구생활' 교과목 개발을 전담하는 수석 AI 어시스턴트입니다.
선생님이 특정 팀이나 학년, 주제를 입력하면 지정된 양식에 맞추어 창의적이고 실용적인 교육 자료를 생성합니다.

[교과 핵심 정체성]
- 본 교과는 '예술·체육 주제 중심의 전 교과 융합 수업'입니다.
- 모든 지도안과 활동지는 음악, 미술, 체육 활동을 중심 매개체로 하여 국어, 역사, 사회, 과학 등과 융합되어야 합니다.
- (예: 울산 반구천 암각화 문양을 활용한 티셔츠 디자인, 태화강 국가정원 플로깅(Plogging) 및 생태 지도 제작 등)

[중점 영역]
1. 울산의 인물과 역사 (항일운동, 언양 3.1 만세운동 등)
2. 울산의 생활과 문화 (지역 축제, 전통시장, 옹기마을 등)
3. 울산의 사회와 자연환경 (산업 환경 문제, SDGs, 생태 복원 등)

[작성 가이드라인]
- 대상: 중학교 1~3학년 (발달 단계 고려)
- 사실성: 울산 및 언양 지역의 지명, 역사에 대해 정확한 정보만 제공할 것.
- 어조: 교육 공학적이며 논리적인 톤을 유지하되, 학생들의 활동은 창의적이고 자기주도적이어야 함.
- 양식: 사용자가 요청한 '세부 계획서(8차시)', '지도서(1차시)', '활동지' 양식을 엄격히 준수할 것.
"""

# ==========================================
# 3. Streamlit UI 및 세션 관리
# ==========================================
st.set_page_config(page_title="신언중학교 교과 어시스턴트", page_icon="🏫", layout="wide")

# 사이드바 설정 (모델 선택 등)
with st.sidebar:
    st.header("⚙️ 설정")
    selected_model = st.selectbox(
        "모델 선택",
        ["gemini-1.5-pro", "gemini-1.5-flash"],
        help="Pro는 추론 능력이 뛰어나고, Flash는 속도가 빠릅니다."
    )
    if st.button("대화 기록 초기화"):
        st.session_state.messages = []
        st.rerun()

st.title("🏫 두런두런 울산 탐구생활 AI 조수")
st.info("신언중학교 선생님들을 위한 교육과정 설계 도우미입니다. 주제를 입력하시면 계획서부터 활동지까지 생성해 드립니다.")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "선생님, 환영합니다! 👏 기획하고자 하시는 수업의 팀명과 주제를 알려주세요.\n\n*(예시: '2학년 1팀 언양의 독립운동가 탐구 8차시 계획서 써줘')*"}
    ]

# 이전 대화 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# AI 모델 초기화 (세션당 1회 또는 모델 변경 시)
def get_gemini_response(prompt, history):
    model = genai.GenerativeModel(
        model_name=selected_model,
        system_instruction=SYSTEM_PROMPT
    )
    # 채팅 모드 시작 (이전 대화 맥락 포함)
    chat = model.start_chat(history=history)
    response = chat.send_message(prompt, stream=True)
    return response

# ==========================================
# 4. 사용자 입력 및 답변 생성
# ==========================================
if user_input := st.chat_input("수업 주제나 양식을 입력하세요..."):
    # 1. 사용자 메시지 저장 및 표시
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. AI 답변 생성 및 스트리밍 표시
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        try:
            # 이전 대화 맥락을 API 형식에 맞게 변환 (role 변환: assistant -> model)
            chat_history = [
                {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
                for m in st.session_state.messages[:-1]
            ]
            
            response_stream = get_gemini_response(user_input, chat_history)
            
            for chunk in response_stream:
                full_response += chunk.text
                # 마크다운 깨짐 방지를 위해 스트리밍 중에는 커서를 텍스트 뒤에만 붙임
                placeholder.markdown(full_response + " ▌")
            
            placeholder.markdown(full_response)
            
        except Exception as e:
            error_msg = f"❌ 오류가 발생했습니다: {str(e)}"
            st.error(error_msg)
            full_response = error_msg

    # 3. AI 답변 최종 저장
    st.session_state.messages.append({"role": "assistant", "content": full_response})
