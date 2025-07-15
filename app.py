import streamlit as st
import time
import pyrebase
import datetime

# 🔧 Firebase 설정
firebaseConfig = {
    "apiKey": "AIzaSyDmTJ9efnl_WFVJOw5HKFLyiBgKcB_ZCK0",
    "authDomain": "chart2-2f5d3.firebaseapp.com",
    "projectId": "chart2-2f5d3",
    "storageBucket": "chart2-2f5d3.appspot.com",  # ← 여기 오타 있었음. .**firebasestorage.app** ❌ → **firebaseapp.com** ✅
    "messagingSenderId": "819265321746",
    "appId": "1:819265321746:web:9c035783e7ee8457a3d1cb",
    "measurementId": "G-9K2NLR4LXC",
    "databaseURL": "https://chart2-2f5d3-default-rtdb.firebaseio.com"  # 반드시 필요함


}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()

# 🔐 로그인 함수
def login():
    st.title("Olio 🔐 로그인 / 회원가입")

    tab1, tab2 = st.tabs(["🔑 로그인", "✍️ 회원가입"])

    # 🔑 로그인 탭
    with tab1:
        email = st.text_input("이메일", key="login_email")
        password = st.text_input("비밀번호", type="password", key="login_password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.user = user
                st.success("✅ 로그인 성공!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ 로그인 실패: {str(e)}")  # 정확한 에러 메시지를 보여줌

    # ✍️ 회원가입 탭
    with tab2:
        email_signup = st.text_input("이메일", key="signup_email")
        password_signup = st.text_input("비밀번호 (6자 이상)", type="password", key="signup_password")
        if st.button("회원가입"):
            try:
                user = auth.create_user_with_email_and_password(email_signup, password_signup)
                st.success("✅ 회원가입 성공! 이제 로그인 해보세요.")
            except Exception as e:
                st.error(f"❌ 회원가입 실패: {str(e)}")

# 💻 메인 앱 함수
def app():
    st.title("📋 차트 기록 시스템 Olio")

    tab1, tab2 = st.tabs(["📋 새 차트 작성", "🔍 환자 검색"])

    with tab1:
        st.subheader("📝 새 차팅 작성")

        name = st.text_input("환자 이름")

        birth = st.date_input(
            "생년월일",
            value=datetime.date(2000, 1, 1),
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date.today()
        )

        visit_date = st.date_input(
            "내원일",
            value=datetime.date.today(),
            min_value=datetime.date(2000, 1, 1),
            max_value=datetime.date.today()
        )

        cc = st.text_input("주호소 (Chief Complaint)")
        pi = st.text_area("PI (Present Illness)")
        os = st.text_area("OS (Other Symptoms)")
        etc = st.text_area("기타 소견")
        prescription = st.text_area("처방")
        if st.button("저장하기"):
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
                st.success("✅ 저장되었습니다!")
            except Exception as e:
                st.error(f"❌ 저장 실패: {e}")

    with tab2:
        st.subheader("🔍 환자 검색 및 기록 보기")

        search_name = st.text_input("환자 이름 검색")

    if search_name:
        try:
            all_data = db.child("patients").get(st.session_state.user["idToken"])
            if all_data.each() is None:
                st.warning("❌ 저장된 환자 정보가 없습니다.")
            else:
                results = {
                    r.key(): r.val()
                    for r in all_data.each()
                    if search_name in r.val().get("name", "")
                }

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

                            confirm = st.checkbox(
                                f"🛑 '{r.get('name', '')}' 기록을 삭제하려면 체크하세요", 
                                key=f"confirm_{key}"
                            )
                            if confirm:
                                if st.button("🗑 진짜 삭제하기", key=f"delete_{key}"):
                                    db.child("patients").child(key).remove(st.session_state.user["idToken"])
                                    st.success("✅ 삭제 완료! 페이지가 자동으로 갱신됩니다.")
                                    st.rerun()  # ✅ 여기 수정됨

        except Exception as e:
            st.error(f"❌ 검색 실패: {e}")




# ✅ 실행 조건 분기
if "user" in st.session_state:
    app()
else:
    login()

