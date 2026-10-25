import json
import streamlit as st
from google import genai
from google.genai import types

# পেজের লেআউট সেটআপ
st.set_page_config(page_title="বাংলা মডেল টেস্ট জেনারেটর", page_icon="📝", layout="wide")

# আপনার এপিআই কি এখানে বসানো হলো
API_KEY = "AIzaSyCOVnNlAE5aCPELU7S3QEkMyi3s-1iAGmQ"

# সেশন স্টেটে প্রশ্ন ও সাবমিশন ট্র্যাক করা
if "questions" not in st.session_state:
    st.session_state.questions = []
if "submitted" not in st.session_state:
    st.session_state.submitted = False

st.title("📝 স্ক্যান করা পিডিএফ থেকে বাংলা মডেল টেস্ট জেনারেটর")
st.markdown("আপনার স্ক্যান করা বা ছবির পিডিএফ ফাইল আপলোড করুন—জেমিনি সরাসরি আপনার বইয়ের পাতা পড়ে নিখুঁত প্রশ্ন তৈরি করবে।")

# সাইডবারে ফাইল আপলোড ও কন্ট্রোল
with st.sidebar:
    st.header("⚙️ সেটিংস ও ফাইল")
    uploaded_file = st.file_uploader("আপনার স্ক্যান করা বাংলা পাঠ্যবইয়ের PDF আপলোড করুন", type=[".pdf"])
    
    num_questions = st.slider("প্রশ্নের সংখ্যা নির্বাচন করুন", min_value=5, max_value=20, value=10, step=5)
    
    generate_btn = st.button("🚀 পিডিএফ থেকে প্রশ্ন তৈরি করুন", type="primary")

# নতুন প্রশ্ন জেনারেট করার লজিক
if generate_btn:
    if uploaded_file is None:
        st.sidebar.error("দয়া করে প্রথমে আপনার পিডিএফ ফাইল আপলোড করুন।")
    else:
        st.session_state.submitted = False
        with st.spinner("জেমিনি আপনার স্ক্যান করা পিডিএফ সরাসরি বিশ্লেষণ করে মানসম্মত প্রশ্ন তৈরি করছে... একটু অপেক্ষা করুন।"):
            try:
                client = genai.Client(api_key=API_KEY)
                
                # পিডিএফ বাইটস সরাসরি রিড করা
                pdf_bytes = uploaded_file.read()
                
                prompt = f"""
                তুমি একজন অভিজ্ঞ বাংলা শিক্ষক। সংযুক্ত স্ক্যান করা পাঠ্যবইয়ের পিডিএফ ফাইলটি খুব ভালোভাবে বিশ্লেষণ করো। 
                এর থেকে ঠিক {num_questions}টি অত্যন্ত মানসম্মত এবং বোর্ড পরীক্ষার আদলে বহুনির্বাচনি প্রশ্ন (MCQ) তৈরি করো।
                প্রতিটি প্রশ্নের ঠিক ৪টি অপশন থাকবে।
                
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
                    model='gemini-2.5-flash',
                    contents=[
                        types.Part.from_bytes(
                            data=pdf_bytes,
                            mime_type='application/pdf',
                        ),
                        prompt
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.7
                    )
                )
                
                st.session_state.questions = json.loads(response.text)
                st.success("সফলভাবে আপনার স্ক্যান করা পিডিএফ থেকে প্রশ্ন তৈরি করা হয়েছে!")
            except Exception as e:
                st.error(f"ত্রুটি ঘটেছে: {e}")

# মূল স্ক্রিনে পরীক্ষা দেওয়া ও রেডিও বাটন প্রদর্শন
if st.session_state.questions:
    st.markdown("### ⏰ অনলাইন মডেল টেস্ট পেপার")
    st.info("নির্দেশনা: প্রতিটি প্রশ্নের সঠিক উত্তরে ক্লিক করুন। পরীক্ষা শেষে নিচে জমা দিন।")
    st.divider()
    
    user_answers = {}
    
    with st.form(key="quiz_form"):
        for i, q in enumerate(st.session_state.questions):
            st.markdown(f"**প্রশ্ন {i+1}: {q['question']}**")
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

    # পরীক্ষা সাবমিট করার পর ফলাফল ও উত্তরমালা
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
    st.warning("পরীক্ষা শুরু করতে বাম পাশের সাইডবার থেকে আপনার স্ক্যান করা পিডিএফ ফাইল আপলোড করে 'পিডিএফ থেকে প্রশ্ন তৈরি করুন' বাটনে ক্লিক করুন।")
