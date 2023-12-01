import openai
from streamlit_option_menu import option_menu
import streamlit as st
from st_audiorec import st_audiorec
import datetime

# Hide Footer(Made with Streamlit) & Main Menu
hide_st_style = '''
    <style>
        #MainMenu {visibility : hidden;}
        footer {visibility : hidden;}
    </style>
    '''
st.markdown(hide_st_style, unsafe_allow_html = True)

# Nav Bar Setting
with st.sidebar:
    selected = option_menu(
        menu_title = "Menu",
        menu_icon = "menu-button-fill",
        options = ["Record", "Upload", "Transcribe", "Summary", "Q&A"],
        icons = ["mic", "upload", "book", "blockquote-left", "chat-right-dots"],
        #orientation = "horizontal",
        default_index = 1,
    )

# Variables
API_Key = st.secrets["openai_key"] #API Key from OpenAI (Whisper)
openai.api_key = API_Key # Accessing API Key Globally(ChatGPT)

# Session State
if 'transcribe_response' not in st.session_state:
    st.session_state['transcribe_response'] = None
if 'summary_response' not in st.session_state:
    st.session_state['summary_response'] = None

# Function
def transcribe_audio():
    if media_file is not None:
        transcribe_response = openai.Audio.transcribe(
            api_key = API_Key,
            model = model_id,
            file = media_file,
            response_format = 'text'  # text, json, srt, vtt
        )
        return transcribe_response

def summarize_audio(tr_response):
    if media_file is not None:
        summary_response = openai.ChatCompletion.create(
            model = 'gpt-3.5-turbo',
            messages = [
                {"role": "system", "content": "你是個得力的文書處理助手。"},
                {"role": "assistant", "content": "我是一個基於人工智慧的語言模型，設計來幫助處理各種文書處理任務。如果您有任何需要，不論是文字處理、文件編輯、資訊檢索或其他任何事情，請隨時告訴我，我會盡力提供幫助。請問您有什麼特定的問題或工作，我可以協助您處理嗎？"},
                {"role": "user", "content": "幫我把會議紀錄根據內容整理成段落，再根據段落整理成兩個表格。第一個表格內容須顯示段落主題、約50字摘要，並在表個最後一列顯示最終結論；第二個表格顯示待辦事項、執行者，若沒有則填寫無"},
                {"role": "assistant", "content": "當然可以幫您進行這項任務。請提供會議紀錄的內容，我將根據您的要求整理成表格。請提供會議紀錄的文本或內容，我將嘗試協助您處理。"},
                {"role": "user", "content": "把以下會議記錄按照上面的要求彙整"+ tr_response}
            ]
        )
        return summary_response

# Record Page
if selected == "Record":
    st.title('Record')
    
    wav_audio_data = st_audiorec()

    if wav_audio_data is not None:
        st.audio(wav_audio_data, format='audio/wav')

# Upload Page
if selected == "Upload":
    st.title('Upload')
    
    model_id = 'whisper-1' 
    
    media_file = st.file_uploader('Upload Audio', type = ('wav', 'mp3', 'mp4'))
    
    if media_file is not None:  # Check if a file has been uploaded
        if st.button("Transcribe Audio"):
            transcribe_response = transcribe_audio()
            st.write("Transcription Completed!")
            st.session_state['transcribe_response'] = transcribe_response
            summary_response = summarize_audio(transcribe_response)
            st.write("Summarizing Completed!")
            st.session_state['summary_response'] = summary_response['choices'][0]['message']['content']

# Transcribe Page
if selected == "Transcribe":
    st.title('Transcribe')
    if st.session_state['transcribe_response'] == None:
        st.write("Please Upload & Transcribe Audio First!")
    else:
        st.write(st.session_state['transcribe_response'])

# Summary Page
if selected == "Summary":
    st.title('Summary')
    if st.session_state['summary_response'] == None:
        st.write("Please Upload & Transcribe Audio First!")
    else:
        st.write(st.session_state['summary_response'])

# Q&A Page
if selected == "Q&A":
    if st.session_state['transcribe_response'] == None:
        st.write("Please Upload & Transcribe Audio First!")
    else:
        preset_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "assistant", "content": "Please upload your transcription"},
            {"role": "user", "content": st.session_state['transcribe_response']},
            {"role": "assistant", "content": "So from the transcription you have uploaded, what question do you have?"}
        ]
        
        if "messages" not in st.session_state:
            st.session_state.messages = preset_messages
    
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        if prompt := st.chat_input("What do you want to know?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                for response in openai.ChatCompletion.create(
                    model = "gpt-3.5-turbo",
                    messages = [{"role": m["role"], "content": m["content"]}
                              for m in st.session_state.messages], stream=True):
                                  
                    full_response += response.choices[0].delta.get("content", "")
                    message_placeholder.markdown(full_response + "▌")
                                  
                message_placeholder.markdown(full_response)
                
            st.session_state.messages.append({"role": "assistant", "content": full_response})
