import base64
import json
import fitz  # PyMuPDF
import streamlit as st
from groq import Groq

# পেজের লেআউট সেটআপ
st.set_page_config(page_title="বাংলা মডেল টেস্ট জেনারেটর", page_icon="📝", layout="wide")

# আপনার Groq API Key
GROQ_API_KEY = "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"

# সেশন স্টেটে প্রশ্ন ও সাবমিশন ট্র্যাক করা
if "questions" not in st.session_state:
    st.session_state.questions = []
if "submitted" not in st.session_state:
    st.session_state.submitted = False

st.title("📝 আপনার আপলোড করা পিডিএফ থেকে ইন্টারেক্টিভ মডেল টেস্ট")
st.markdown("আপনার স্ক্যান করা পিডিএফ ফাইল আপলোড করুন—এআই সরাসরি পাতাগুলো বিশ্লেষণ করে নিখুঁত প্রশ্ন তৈরি করবে।")

# সাইডবারে ফাইল আপলোড ও কন্ট্রোল
with st.sidebar:
    st.header("⚙️ সেটিংস ও ফাইল")
    uploaded_file = st.file_uploader("আপনার বাংলা পাঠ্যবইয়ের PDF আপলোড করুন", type=[".pdf"])
    
    num_questions = st.slider("প্রশ্নের সংখ্যা নির্বাচন করুন", min_value=5, max_value=20, value=10, step=5)
    
    generate_btn = st.button("🚀 পিডিএফ থেকে প্রশ্ন তৈরি করুন", type="primary")

# নতুন প্রশ্ন জেনারেট করার লজিক (অপ্টিমাইজড ভিশন এআই)
if generate_btn:
    if uploaded_file is None:
        st.sidebar.error("দয়া করে প্রথমে আপনার পিডিএফ ফাইল আপলোড করুন।")
    else:
        st.session_state.submitted = False
        with st.spinner("পিডিএফ ফাইল অপ্টিমাইজ ও স্ক্যান করে প্রশ্ন তৈরি করা হচ্ছে... একটু অপেক্ষা করুন।"):
            try:
                # PyMuPDF দিয়ে পিডিএফ পেজগুলোকে অপ্টিমাইজড ইমেজ করা (সাইজ ছোট রাখতে)
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                image_contents = []
                
                # সাইজ এরর এড়াতে প্রথম ২-৩টি পেজ টার্গেট করা হলো
                max_pages = min(len(doc), 3)
                for page_num in range(max_pages):
                    page = doc[page_num]
                    pix = page.get_pixmap(dpi=96)  # কম রেজোলিউশন কিন্তু স্পষ্ট
                    # JPEG ফরম্যাটে কম্প্রেস করা যাতে 413 error না আসে
                    img_bytes = pix.tobytes("jpeg", jpg_quality=65)
                    base64_img = base64.b64encode(img_bytes).decode('utf-8')
                    image_contents.append(base64_img)
                
                client = Groq(api_key=GROQ_API_KEY)
                
                messages_content = [
                    {
                        "type": "text",
                        "text": f"""তুমি একজন অভিজ্ঞ বাংলা শিক্ষক। সংযুক্ত পিডিএফ পাতার ছবিগুলো দেখে এই কন্টেন্ট থেকে ঠিক {num_questions}টি অত্যন্ত মানসম্মত এবং বোর্ড পরীক্ষার আদলে বহুনির্বাচনি প্রশ্ন (MCQ) তৈরি করো।
                        প্রতিটি প্রশ্নের ঠিক ৪টি অপশন থাকবে।
                        
                        আউটপুটটি অবশ্যই একটি ভ্যালিড JSON অ্যারে (JSON Array) হতে হবে, যার স্ট্রাকচার হবে হুবহু নিচে দেওয়া ফরম্যাটে:
                        [
                          {{
                            "question": "প্রশ্ন এখানে?",
                            "options": ["অপশন ১", "অপশন ২", "অপশন ৩", "অপশন ৪"],
                            "answer": "সঠিক উত্তর (হুবহু অপশনের যেকোনো একটির সাথে মিল থাকতে হবে)"
                          }}
                        ]"""
                    }
                ]
                
                for b64 in image_contents:
                    messages_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}"
                        }
                    })
                
                completion = client.chat.completions.create(
                    model="llama-3.2-11b-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": messages_content
                        }
                    ],
                    temperature=0.7,
                    max_tokens=4000
                )
                
                res_content = completion.choices[0].message.content
                
                if "```json" in res_content:
                    res_content = res_content.split("```json")[1].split("```")[0]
                elif "```" in res_content:
                    res_content = res_content.split("```")[1].split("```")[0]
                
                data = json.loads(res_content.strip())
                
                if isinstance(data, dict):
                    for key, val in data.items():
                        if isinstance(val, list):
                            st.session_state.questions = val
                            break
                    if not st.session_state.questions:
                        st.session_state.questions = list(data.values())[0]
                elif isinstance(data, list):
                    st.session_state.questions = data
                    
                st.success("সফলভাবে আপনার পিডিএফ ফাইল থেকে প্রশ্ন তৈরি করা হয়েছে!")
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
    st.warning("পরীক্ষা শুরু করতে বাম পাশের সাইডবার থেকে আপনার বাংলা বইয়ের পিডিএফ ফাইল আপলোড করে 'পিডিএফ থেকে প্রশ্ন তৈরি করুন' বাটনে ক্লিক করুন।")
