import streamlit as st
import pyrebase
import time
import datetime
from firebase_config import firebaseConfig

# Firebase 초기화
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()

# 자동 로그인 세션 처리
if "user" not in st.session_state:
    st.session_state.user = None

# 로그인 함수
def login():
    st.title("🔐 로그인")
    email = st.text_input("이메일")
    password = st.text_input("비밀번호", type="password")
    
    if st.button("로그인"):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.session_state.user = user
            st.success("✅ 로그인 성공")
            st.rerun()
        except:
            st.error("❌ 로그인 실패: 이메일 또는 비밀번호를 확인하세요")

# 앱 본문
def app():
    st.title("📋 환자 차트 기록 시스템")
    tab1, tab2 = st.tabs(["차트 작성", "차트 검색/삭제"])

    with tab1:
        st.subheader("📝 새 차팅 작성")

        with st.form("chart_form"):
            name = st.text_input("이름")
            birth = st.date_input("생년월일", value=datetime.date(2000, 1, 1), min_value=datetime.date(1900, 1, 1))
            visit_date = st.date_input("내원일")
            cc = st.text_input("주호소 (Chief Complaint)")
            pi = st.text_area("PI")
            os = st.text_area("OS")
            etc = st.text_area("기타 소견")
            prescription = st.text_area("처방")

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
                }
                db.child("patients").push(data, st.session_state.user['idToken'])
                st.success("✅ 저장 완료")

    with tab2:
        st.subheader("🔍 환자 검색 및 기록 보기")
        search_name = st.text_input("이름으로 검색")
        if st.button("검색하기"):
            try:
                results = db.child("patients").get(st.session_state.user['idToken']).val()
                if not results:
                    msg = st.empty()
                    msg.warning("🔍 검색 결과가 없습니다.")
                    time.sleep(3)
                    msg.empty()
                else:
                    found = False
                    for key, r in results.items():
                        if r.get("name", "").strip() == search_name.strip():
                            found = True
                            with st.expander(f"👤 {r.get('name')} ({r.get('birth')})"):
                                st.write(f"🗓 내원일: {r.get('visit_date')}")
                                st.write(f"📋 주호소 (CC): {r.get('chief_complaint')}")
                                st.write(f"📄 PI: {r.get('pi')}")
                                st.write(f"🔍 OS: {r.get('os')}")
                                st.write(f"🗒 기타: {r.get('etc')}")
                                st.write(f"💊 처방: {r.get('prescription')}")
                                if st.button("삭제하기", key=key):
                                    db.child("patients").child(key).remove(st.session_state.user['idToken'])
                                    st.success("🗑 삭제 완료")
                                    st.rerun()
                    if not found:
                        st.warning("🔍 해당 이름의 환자가 없습니다.")
            except Exception as e:
                st.error(f"❌ 검색 실패: {e}")

# 실행
if st.session_state.user:
    app()
else:
    login()