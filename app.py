import os
import json
import time
import streamlit as st
from google import genai
from google.genai import types

# পেজের লেআউট সেটআপ
st.set_page_config(page_title="বাংলা মডেল টেস্ট জেনারেটর", page_icon="📝", layout="wide")

# জেমিনি এপিআই কি সেটআপ
API_KEY = "AQ.Ab8RN6JRAryqSS4Y3Lsxl83WPaRLCWeLHCQb789u4W4lxcBeDg"

# সেশন স্টেটে প্রশ্ন ও ইউজার অ্যানসার সংরক্ষণের জন্য
if "questions" not in st.session_state:
    st.session_state.questions = []
if "submitted" not in st.session_state:
    st.session_state.submitted = False

st.title("📝 বাংলা পাঠ্যবই ভিত্তিক ইন্টারেক্টিভ মডেল টেস্ট অ্যাপ")
st.markdown("আপনার বাংলা পাঠ্যবইয়ের পিডিএফ আপলোড করুন এবং সঠিক অপশনে ক্লিক করে মডেল টেস্টে অংশ নিন।")

# সাইডবারে ফাইল আপলোড ও কন্ট্রোল
with st.sidebar:
    st.header("⚙️ সেটিংস ও ফাইল")
    uploaded_file = st.file_uploader("আপনার বাংলা পাঠ্যবইয়ের PDF আপলোড করুন", type=[".pdf"])
    
    num_questions = st.slider("প্রশ্নের সংখ্যা নির্বাচন করুন", min_value=5, max_value=30, value=15, step=5)
    
    generate_btn = st.button("🚀 নতুন সেটে পরীক্ষা শুরু করুন", type="primary")

# নতুন প্রশ্ন জেনারেট করার লজিক
if generate_btn:
    if uploaded_file is None:
        st.sidebar.error("দয়া করে প্রথমে একটি পিডিএফ ফাইল আপলোড করুন।")
    else:
        st.session_state.submitted = False
        with st.spinner("ফাইল প্রসেস করে নতুন প্রশ্ন সেট তৈরি করা হচ্ছে... একটু অপেক্ষা করুন।"):
            try:
                client = genai.Client(api_key=API_KEY)
                
                # সাময়িক ফাইলে সেভ করে জেমিনিতে আপলোড
                with open("temp.pdf", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                uploaded_pdf = client.files.upload(file="temp.pdf")
                time.sleep(2)
                
                prompt = f"""
                তুমি একজন অভিজ্ঞ বাংলা শিক্ষক। নিচের পাঠ্যবইয়ের পিডিএফ কনটেন্ট ভালোভাবে বিশ্লেষণ করো। 
                গদ্য ও পদ্য উভয় অংশ মিলিয়ে ঠিক {num_questions}টি অত্যন্ত মানসম্মত, র‍্যান্ডম এবং নতুন নতুন বোর্ড পরীক্ষার আদলে বহুনির্বাচনি প্রশ্ন (MCQ) তৈরি করো।
                প্রতিটি প্রশ্নের ঠিক ৪টি অপশন থাকবে। আগের তৈরি করা প্রশ্নের পুনরাবৃত্তি এড়িয়ে নতুন তথ্য বা নতুন কোণ থেকে প্রশ্ন তৈরি করো।
                
                আউটপুটটি বিশুদ্ধ JSON ফরম্যাটে হতে হবে হুবহু এই স্ট্রাকচারে:
                [
                  {{
                    "question": "প্রশ্ন এখানে?",
                    "options": ["অপশন ১", "অপশন ২", "অপশন ৩", "অপশন ৪"],
                    "answer": "সঠিক উত্তর (হুবহু অপশনের যেকোনো একটির সাথে মিল থাকতে হবে)"
                  }}
                ]
                """
                
                response = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=[uploaded_pdf, prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.8
                    )
                )
                
                st.session_state.questions = json.loads(response.text)
                st.success("সফলভাবে নতুন প্রশ্ন সেট তৈরি করা হয়েছে!")
            except Exception as e:
                st.error(f"ত্রুটি ঘটেছে: {e}")

# মূল স্ক্রিনে প্রশ্ন ও রেডিও বাটন (ক্লিক করার অপশন) প্রদর্শন
if st.session_state.questions:
    st.markdown("### ⏰ অনলাইন মডেল টেস্ট পেপার")
    st.info("নির্দেশনা: প্রতিটি প্রশ্নের সঠিক উত্তরে মাউস দিয়ে ক্লিক করুন। পরীক্ষা শেষ নিচে জমা দিন।")
    st.divider()
    
    user_answers = {}
    
    # ফর্মের মাধ্যমে প্রতিটি প্রশ্নের রেডিও বাটন তৈরি
    with st.form(key="quiz_form"):
        for i, q in enumerate(st.session_state.questions):
            st.markdown(f"**প্রশ্ন {i+1}: {q['question']}**")
            # রেডিও বাটনের মাধ্যমে মাউস দিয়ে ক্লিক করে সিলেক্ট করার সুবিধা
            user_answers[i] = st.radio(
                f"উত্তর নির্বাচন করুন (প্রশ্ন {i+1})", 
                q['options'], 
                key=f"q_{i}",
                label_visibility="collapsed"
            )
            st.write("")
        
        submit_exam = st.form_submit_button("✅ পরীক্ষা জমা দিন ও ফলাফল দেখুন", type="primary")
        
        if submit_exam:
            st.session_state.submitted = True

    # সাবমিট করার পর ফলাফল ও সঠিক উত্তর দেখানো
    if st.session_state.submitted:
        st.divider()
        st.markdown("### 📊 পরীক্ষার ফলাফল ও উত্তরমালা")
        
        score = 0
        total = len(st.session_state.questions)
        
        for i, q in enumerate(st.session_state.questions):
            selected = user_answers.get(i)
            correct = q['answer']
            
            st.markdown(f"**প্রশ্ন {i+1}:** {q['question']}")
            st.markdown(f"আপনার উত্তর: `{selected}`")
            
            if selected == correct:
                st.success("✨ সঠিক উত্তর!")
                score += 1
            else:
                st.error(f"❌ ভুল হয়েছে! সঠিক উত্তর হবে: **{correct}**")
            st.write("---")
            
        st.balloons()
        st.markdown(f"### মোট প্রাপ্ত নম্বর: **{score} / {total}**")

else:
    st.warning("পরীক্ষা শুরু করতে বাম পাশের সাইডবার থেকে পিডিএফ আপলোড করে 'নতুন সেটে পরীক্ষা শুরু করুন' বাটনে ক্লিক করুন।")
