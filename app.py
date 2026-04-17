import streamlit as st
import google.generativeai as genai

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
# 2. 시스템 프롬프트 (AI의 두뇌 및 규칙)
# ==========================================
SYSTEM_PROMPT = """
당신은 대한민국 울산광역시 '신언중학교'의 학교자율시간 '두런두런 울산 탐구생활' 교과목 개발을 전담하는 수석 AI 어시스턴트입니다.
선생님이 특정 팀이나 학년, 주제를 입력하면 지정된 양식에 맞추어 창의적이고 실용적인 교육 자료를 생성합니다.

[교과 기본 배경]
- 1. 울산의 인물과 역사 (항일만세운동, 반구천 암각화 등)
- 2. 울산의 생활과 문화 (지역 축제, 전통시장, 명소 등)
- 3. 울산의 사회와 자연환경 (다문화, 온산공단 등 산업 환경문제, 정책 토론 등)
- 예술과 체육 교과가 융합되어 있으며, 지속가능발전목표(SDGs) 달성을 목표로 합니다.

[작성 지침 및 양식]
사용자의 요청에 따라 다음 세 가지 양식 중 하나를 선택하여 작성합니다.

1. 세부 계획서 양식 (8차시 분량)
   - 기본 개요: 팀/학년, 주제, 관련 성취기준, 지도 중점
   - 차시별 운영 계획 (1~8차시 표 형태)
   - 교재 및 활동지, 교구(키트) 개발 계획 (표 형태)
   - 예산 사용 계획 (표 형태)

2. 지도서 양식 (1차시 분량)
   - 단원명 / 학습 목표 / 도입(10분) / 전개(30분) / 정리(5분) / 평가계획

3. 활동지 양식
   - 제시문: 울산/언양 지역과 관련된 생생한 스토리나 딜레마 사례
   - 문제 1: 사실 확인 문항
   - 문제 2: 비판적 사고 및 창의적 해결 방안 서술형 문항

[엄격한 제약 사항]
- 대상은 중학교 1~3학년입니다.
- 언양 지역의 구체적인 지명, 역사, 환경 문제를 다룰 때 절대 거짓 정보(Hallucination)를 지어내지 마세요.
- 기관 투자자 리포트 수준의 논리적이고 정량적인 톤을 유지하되, 학생 활동은 창의적이어야 합니다.
"""

# ==========================================
# 3. Streamlit 웹 화면 구성 (UI)
# ==========================================
st.set_page_config(page_title="신언중학교 교과 어시스턴트", page_icon="🏫", layout="centered")

st.title("🏫 두런두런 울산 탐구생활 AI 조수")
st.markdown("""
**신언중학교 선생님들을 위한 교육과정 설계 도우미입니다.**
팀별 주제(예: '3학년 1팀 화장산 수호 프로젝트')를 입력하시면 
**세부 계획서, 지도서, 활동지** 초안을 자동으로 척척 작성해 드립니다!
""")

# 세션 상태(Session State)를 사용하여 대화 기록 저장
if "messages" not in st.session_state:
    st.session_state.messages = []
    # 초기 인사말
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "선생님, 환영합니다! 👏 어떤 팀의 수업 자료를 기획해 드릴까요?\n\n*(예시: '2학년 1팀 언양의 인물 프로젝트 8차시 세부 계획서 작성해줘')*"
    })

# 대화 기록 화면에 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력 처리
if prompt := st.chat_input("수업 주제나 필요하신 양식을 입력하세요 (예: 1차시 활동지 만들어줘)"):
    # 사용자 메시지 화면에 표시
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # AI 답변 생성
    with st.chat_message("assistant"):
        with st.spinner("선생님의 수업 자료를 열심히 작성하고 있습니다... ✍️"):
            try:
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash-preview-09-2025",
                    system_instruction=SYSTEM_PROMPT
                )
                response = model.generate_content(prompt)
                response_text = response.text
                st.markdown(response_text)
            except Exception as e:
                response_text = f"죄송합니다. 오류가 발생했습니다: {e}"
                st.error(response_text)
            
    # AI 답변 저장
    st.session_state.messages.append({"role": "assistant", "content": response_text})