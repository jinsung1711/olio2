import streamlit as st
import pyrebase
import datetime
import time
from collections import defaultdict
from fpdf import FPDF
from io import BytesIO
import base64
import os

# Firebase 설정
firebaseConfig = {
    "apiKey": "AIzaSyDmTJ9efnl_WFVJOw5HKFLyiBgKcB_ZCK0",
    "authDomain": "chart2-2f5d3.firebaseapp.com",
    "projectId": "chart2-2f5d3",
    "storageBucket": "chart2-2f5d3.appspot.com",
    "messagingSenderId": "819265321746",
    "appId": "1:819265321746:web:9c035783e7ee8457a3d1cb",
    "databaseURL": "https://chart2-2f5d3-default-rtdb.firebaseio.com"
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()

# 세션 초기화
if "user" not in st.session_state:
    st.session_state.user = None
if "login_success" not in st.session_state:
    st.session_state.login_success = False
if "login_error" not in st.session_state:
    st.session_state.login_error = False
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

# 회원가입 함수 추가
def signup():
    st.subheader("🔐 회원가입")
    name = st.text_input("이름", key="signup_name")
    email = st.text_input("이메일", key="signup_email")
    password = st.text_input("비밀번호", type="password", key="signup_pw")

    if st.button("회원가입"):
        try:
            user = auth.create_user_with_email_and_password(email, password)
            user_id = user["localId"]
            db.child("users").child(user_id).set({"name": name, "email": email})
            st.success("✅ 회원가입 성공! 로그인 해주세요.")
        except Exception as e:
            st.error(f"❌ 회원가입 실패: {e}")

# 회원 탈퇴 함수 추가
def delete_account():
    st.subheader("⚠️ 회원 탈퇴")
    confirm = st.checkbox("정말로 탈퇴하시겠습니까?")
    if confirm:
        try:
            user_id = st.session_state.user["localId"]
            db.child("users").child(user_id).remove(st.session_state.user["idToken"])
            db.child("patients").child(user_id).remove(st.session_state.user["idToken"])
            st.session_state.user = None
            st.session_state.login_success = False
            st.session_state.user_name = ""
            st.success("✅ 회원 탈퇴 완료")
            st.rerun()
        except Exception as e:
            st.error(f"❌ 탈퇴 실패: {e}")

def login():
    st.title("🧪 환자 차트 기록 시스템 olio")
    menu = st.radio("메뉴 선택", ["로그인", "회원가입"])

    if menu == "로그인":
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")

        login_clicked = st.button("로그인")

        if login_clicked:
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.user = user
                st.session_state.login_success = True
                st.session_state.login_error = False
                user_id = user["localId"]
                user_info = db.child("users").child(user_id).get().val()
                if user_info and "name" in user_info:
                    st.session_state.user_name = user_info["name"]
                st.rerun()
            except Exception as e:
                st.session_state.login_success = False
                st.session_state.login_error = True
                st.rerun()

        if st.session_state.login_success:
            st.success(f"✅ 로그인 성공! {st.session_state.user_name}님 환영합니다.")

    elif menu == "회원가입":
        signup()

def app():
    st.title("🧪 환자 차트 기록 시스템 olio")

    if st.session_state.user_name:
        st.markdown(f"### 👤 사용자: {st.session_state.user_name}")

    tab1, tab2, tab3, tab4 = st.tabs(["📄 차팅", "🔍 검색", "📋 환자 리스트", "⚠️ 회원 탈퇴"])

    user_id = st.session_state.user["localId"]

    with tab1:
        st.subheader("📝 새 차트 작성")
        with st.form(key="chart_form"):
            name = st.text_input("환자 이름")
            birth = st.date_input("생년월일", value=datetime.date(2000, 1, 1), min_value=datetime.date(1900, 1, 1))
            visit_date = st.date_input("내원일")
            cc = st.text_input("주호소 (Chief Complaint)")
            st.markdown("PI는 현재 질병에 대한 병력입니다. 예: 통증 발생 시기, 양상, 경과 등")
            pi = st.text_area("PI (Present Illness)")
            st.markdown("OS는 기타 증상 또는 과거력 등 참고사항입니다.")
            os = st.text_area("OS (Other Symptoms)")
            etc = st.text_area("기타 소견")
            prescription = st.text_area("처방")
            ht = st.checkbox("고혈압")
            dm = st.checkbox("당뇨")
            hl = st.checkbox("고지혈증")
            hd = st.checkbox("심장 질환")

            submitted = st.form_submit_button("저장하기")
            if submitted:
                data = {
                    "name": name,
                    "birth": str(birth),
                    "visit_date": str(visit_date),
                    "chief_complaint": cc,
                    "pi": pi,
                    "os": os,
                    "etc": etc,
                    "prescription": prescription,
                    "hypertension": ht,
                    "diabetes": dm,
                    "hyperlipidemia": hl,
                    "heart_disease": hd
                }
                try:
                    db.child("patients").child(user_id).push(data, st.session_state.user["idToken"])
                    st.session_state.last_saved_data = data  # ✅ PDF용 저장
                    st.success("✅ 저장 완료")
                except Exception as e:
                    st.error(f"❌ 저장 실패: {e}")

        if "last_saved_data" in st.session_state:
            with st.container():
                col1, col2, col3 = st.columns([1, 1, 2])
                with col3:
                    if st.button("📄 PDF로 저장", key="pdf_save_button"):
                        class PDF(FPDF):
                            def header(self):
                                self.set_font("NanumGothic", "", 14)
                                self.cell(200, 10, "환자 차트 기록", ln=True, align="C")
                                self.ln(10)

                            def chapter_body(self, data):
                                self.set_font("NanumGothic", "", 12)
                                for k, v in data.items():
                                    if isinstance(v, bool):
                                        v = "O" if v else "X"
                                    self.multi_cell(0, 10, f"{k}: {v}")
                                self.ln()

                        FONT_PATH = os.path.join(os.path.dirname(__file__), "NanumGothic.ttf")
                        pdf = PDF()
                        pdf.add_page()
                        pdf.add_font("NanumGothic", "", FONT_PATH, uni=True)
                        pdf.chapter_body(st.session_state.last_saved_data)

                        pdf_output = BytesIO()
                        pdf.output(pdf_output)
                        b64 = base64.b64encode(pdf_output.getvalue()).decode()
                        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{st.session_state.last_saved_data["name"]}_{st.session_state.last_saved_data["visit_date"]}_chart.pdf">📄 PDF 다운로드</a>'
                        st.markdown(href, unsafe_allow_html=True)

    # tab2, tab3, tab4는 기존과 동일
    with tab2:
        st.subheader("🔍 환자 검색 및 기록 보기")
        ...

    with tab3:
        st.subheader("📋 전체 환자 리스트")
        ...

    with tab4:
        delete_account()

# 실행
if st.session_state.user:
    app()
else:
    login()
