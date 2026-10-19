import json
import streamlit as st
from groq import Groq
from pypdf import PdfReader

# পেজের লেআউট সেটআপ
st.set_page_config(page_title="বাংলা মডেল টেস্ট জেনারেটর", page_icon="📝", layout="wide")

# আপনার Groq API Key এখানে সেট করা হলো
GROQ_API_KEY = "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"

# সেশন স্টেটে প্রশ্ন ও সাবমিশন ট্র্যাক করা
if "questions" not in st.session_state:
    st.session_state.questions = []
if "submitted" not in st.session_state:
    st.session_state.submitted = False

st.title("📝 বাংলা পাঠ্যবই ভিত্তিক ইন্টারেক্টিভ মডেল টেস্ট অ্যাপ")
st.markdown("আপনার বাংলা পাঠ্যবইয়ের পিডিএফ ফাইল আপলোড করুন এবং এক ক্লিকে ইন্টারেক্টিভ মডেল টেস্টে অংশ নিন।")

# সাইডবারে ফাইল আপলোড ও কন্ট্রোল
with st.sidebar:
    st.header("⚙️ সেটিংস ও ফাইল")
    uploaded_file = st.file_uploader("আপনার বাংলা পাঠ্যবইয়ের PDF আপলোড করুন", type=[".pdf"])
    
    num_questions = st.slider("প্রশ্নের সংখ্যা নির্বাচন করুন", min_value=5, max_value=20, value=10, step=5)
    
    generate_btn = st.button("🚀 নতুন প্রশ্ন তৈরি করুন", type="primary")

# নতুন প্রশ্ন জেনারেট করার লজিক
if generate_btn:
    if uploaded_file is None:
        st.sidebar.error("দয়া করে প্রথমে একটি পিডিএফ ফাইল আপলোড করুন।")
    else:
        st.session_state.submitted = False
        with st.spinner("পিডিএফ ফাইল বিশ্লেষণ করে চমৎকার প্রশ্ন তৈরি করা হচ্ছে... একটু অপেক্ষা করুন।"):
            try:
                # স্থানীয়ভাবে পিডিএফ প্রসেসিং
                reader = PdfReader(uploaded_file)
                extracted_text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"
                
                if not extracted_text.strip():
                    st.error("দুঃখিত, এই পিডিএফ ফাইল থেকে লেখা পড়া যায়নি। অন্য কোনো স্পষ্ট পিডিএফ আপলোড করুন।")
                else:
                    client = Groq(api_key=GROQ_API_KEY)
                    
                    prompt = f"""
                    তুমি একজন অভিজ্ঞ বাংলা শিক্ষক। নিচের পাঠ্যবইয়ের কনটেন্ট ভালোভাবে বিশ্লেষণ করো। 
                    এর থেকে ঠিক {num_questions}টি অত্যন্ত মানসম্মত এবং বোর্ড পরীক্ষার আদলে বহুনির্বাচনি প্রশ্ন (MCQ) তৈরি করো।
                    প্রতিটি প্রশ্নের ঠিক ৪টি অপশন থাকবে।
                    
                    আউটপুটটি অবশ্যই একটি ভ্যালিড JSON অ্যারে (JSON Array) হতে হবে, যার স্ট্রাকচার হবে হুবহু নিচে দেওয়া ফরম্যাটে:
                    [
                      {{
                        "question": "প্রশ্ন এখানে?",
                        "options": ["অপশন ১", "অপশন ২", "অপশন ৩", "অপশন ৪"],
                        "answer": "সঠিক উত্তর (হুবহু অপশনের যেকোনো একটির সাথে মিল থাকতে হবে)"
                      }}
                    ]
                    
                    পাঠ্যবইয়ের অংশ:
                    {extracted_text[:25000]}
                    """
                    
                    # গ্রকের বর্তমান সচল ও অফিশিয়াল মডেল ব্যবহার করা হলো
                    completion = client.chat.completions.create(
                        model="openai/gpt-oss-20b",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that outputs only valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.7
                    )
                    
                    # রেসপন্স থেকে JSON পার্স করা
                    res_content = completion.choices[0].message.content
                    data = json.loads(res_content)
                    
                    # ডেটা ফরম্যাট অ্যাডজাস্ট করা
                    if isinstance(data, dict):
                        for key, val in data.items():
                            if isinstance(val, list):
                                st.session_state.questions = val
                                break
                        if not st.session_state.questions:
                            st.session_state.questions = list(data.values())[0]
                    elif isinstance(data, list):
                        st.session_state.questions = data
                        
                    st.success("সফলভাবে নতুন প্রশ্ন সেট তৈরি করা হয়েছে!")
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
    st.warning("পরীক্ষা শুরু করতে বাম পাশের সাইডবার থেকে আপনার বইয়ের পিডিএফ ফাইল আপলোড করে 'নতুন প্রশ্ন তৈরি করুন' বাটনে ক্লিক করুন।")
