import streamlit as st
import pyrebase
import datetime
import time

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

def login():
    st.title("🩺 환자 차트 기록 시스템 olio")
    email = st.text_input("이메일")
    password = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.session_state.user = user
            st.success("✅ 로그인 성공!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"❌ 로그인 실패: {e}")

def app():
    st.title("🩺 환자 차트 기록 시스템 olio")

    tab1, tab2 = st.tabs(["📄 차팅", "🔍 검색"])

    with tab1:
        st.subheader("📝 새 차트 작성")
        with st.form(key="chart_form"):
            name = st.text_input("환자 이름")
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
                    "prescription": prescription
                }
                try:
                    db.child("patients").push(data, st.session_state.user["idToken"])
                    st.success("✅ 저장 완료")
                except Exception as e:
                    st.error(f"❌ 저장 실패: {e}")

    with tab2:
        st.subheader("🔍 환자 검색 및 기록 보기")
        keyword = st.text_input("환자 이름을 입력하세요")

        if st.button("검색하기"):
            try:
                all_data = db.child("patients").get(st.session_state.user["idToken"]).val()
                results = {}

                if all_data:
                    for key, record in all_data.items():
                        if keyword.lower() in record.get("name", "").lower():
                            results[key] = record

                if not results:
                    msg = st.empty()
                    msg.warning("🔍 검색 결과가 없습니다.")
                    time.sleep(3)
                    msg.empty()
                else:
                    for key, r in results.items():
                        with st.expander(f"👤 {r.get('name', '')} ({r.get('birth', '')})"):
                            st.write(f"🗓 내원일: {r.get('visit_date', '')}")
                            st.write(f"📋 주호소 (CC): {r.get('chief_complaint', '')}")
                            st.write(f"📋 PI: {r.get('pi', '')}")
                            st.write(f"🔍 OS: {r.get('os', '')}")
                            st.write(f"🗒 기타 소견: {r.get('etc', '')}")
                            st.write(f"💊 처방: {r.get('prescription', '')}")

                            if st.button(f"❌ 삭제하기 - {r.get('name', '')}", key=f"delete_{key}"):
                                try:
                                    db.child("patients").child(key).remove(st.session_state.user["idToken"])
                                    st.success("✅ 기록이 삭제되었습니다.")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"❌ 삭제 실패: {e}")

            except Exception as e:
                st.error(f"❌ 검색 실패: {e}")

# 실행
if st.session_state.user:
    app()
else:
    login()
