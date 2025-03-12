import streamlit as st
import azure.cognitiveservices.speech as speechsdk
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import os
import time
import tempfile

st.set_page_config(
    page_title="CareCenter",
    page_icon="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRzDlRoVrd80cb1RgMTedi7zXqX3zKbZyshfw&s",
    layout="centered"
)

def speech_to_text(audio_file):
    subscription_key = "FKnTVDn6dNgyjJ5JtuSHKUylfwCFT5NOLIHTuIvABp7HDgia5PmFJQQJ99BCACYeBjFXJ3w3AAAAACOG8KSL"
    region = "eastus"
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
    speech_config.speech_recognition_language = "th-TH"
    MAX_DURATION = 300
    done = False
    all_text = []

    def handle_result(evt):
        if evt.result.text:
            all_text.append(evt.result.text)

    def stop_cb(evt):
        nonlocal done
        done = True

    def canceled_cb(evt):
        nonlocal done
        done = True

    audio_config = speechsdk.audio.AudioConfig(filename=audio_file)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    speech_recognizer.recognized.connect(handle_result)
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(canceled_cb)
    speech_recognizer.start_continuous_recognition()
    
    start_time = time.time()
    
    while not done and (time.time() - start_time) < MAX_DURATION:
        time.sleep(0.5)
    
    speech_recognizer.stop_continuous_recognition()
    
    final_text = " ".join(all_text)
    if not final_text:
        return "Speech recognition failed or no speech detected"

    # Display transcribed text with animation
    message_placeholder = st.empty()
    for i in range(len(final_text)):
        message_placeholder.markdown(final_text[:i+1])
        time.sleep(0.09)
    
    return final_text

def analyze_text_for_scam(text):
    llm = ChatOpenAI(
        openai_api_key="sk-GqA4Uj6iZXaykbOzIlFGtmdJr6VqiX94NhhjPZaf81kylRzh",
        openai_api_base="https://api.opentyphoon.ai/v1",
        model_name="typhoon-v2-70b-instruct",
    )
    template = """
        วิเคราะห์ข้อความต่อไปนี้เพื่อหาสัญญาณที่อาจเป็นการหลอกลวงเท่านั้น 
        ถ้าหากเป็นข้อความที่กำกวมภาษาที่ไม่ชัดเจนและซ้ำซ้อนอาจทำให้เกิดความสับสน จะไม่นับเป็นการหลอกลวงหรือไม่มีความเสี่ยง :
        {text}

        กรุณาระบุ:
        1. คำ ประโยค วลีหรือรูปแบบของข้อความที่น่าสงสัย
        2. ระดับความเสี่ยง (ไม่มีความเสี่ยง/ต่ำ/กลาง/สูง)
        3. ประเภทของการหลอกลวงที่อาจเกิดขึ้น (ถ้ามี)
        4. เหตุผลสำหรับการประเมิน

        การตอบกลับ :
    """
    
    prompt = PromptTemplate(
        input_variables=["text"],
        template=template
    )
    
    chain = prompt | llm
    response = chain.invoke({"text": text})
    
    return response.content

def main():
    st.title("CareCenter scam detection")
    st.write("Upload an audio file to detect potential scams")
    uploaded_file = st.file_uploader("Choose an audio file", type=['wav', 'm4a', 'mp3'])
    
    if uploaded_file is not None:
        st.audio(uploaded_file)
        progress_bar = st.progress(0)
        status_text = st.empty()
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        try:
            status_text.text("Transcribing audio...")
            progress_bar.progress(30)
            transcribed_text = speech_to_text(tmp_file_path)
            
            if transcribed_text:
                status_text.text("Analyzing for potential scams...")
                progress_bar.progress(60)
                analysis_result = analyze_text_for_scam(transcribed_text)
                progress_bar.progress(100)
                status_text.text("Anomaly Founded!") 
                st.subheader("Scam Analysis Result: ")
                st.markdown(analysis_result)
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
        
        finally:
            os.unlink(tmp_file_path)

if __name__ == "__main__":
    main()    
