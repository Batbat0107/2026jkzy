import streamlit as st
import requests
import json
import os

API_KEY = '115d84b24f1f4c95876f173b263e4e60.kkBRUmuElHpZcoS2'
API_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
MEMORY_FILE = 'memory.json'
LIVE_FILE = 'live.json'

# ========== Fish Audio 语音合成配置 ==========
FISH_AUDIO_API_KEY = "c57b52d5a8e8c30b817c5c8bb73c3821d34548050379565b1cedbdf2e87c5a38"
FISH_AUDIO_API_URL = "https://api.fishspeech.net/v1/tts"
FISH_AUDIO_MODEL_ID = "ea5863a5-1831-42a2-8556-3fadf1b61386"

SYSTEM_PROMPT = '''你是薛佳妍，1998年生，现任密斯卡托尼克大学神秘科学与超自然现象研究所助理研究员，上海外滩美术馆跨维度现象研究顾问。常年穿梭于阿卡姆与上海两地开展研究工作，前阿卡姆天文台异常天体观测项目核心成员。你的近期研究聚焦于旧神遗留痕迹与人类认知边界的交互关系，探索深潜者、远古星族等超自然存在的物质性证据，以及跨维度信号对人类社会结构、集体潜意识的侵蚀与重塑机制，尤其关注远古文明技术残留对现代科学体系的颠覆性影响。

请以薛佳妍的身份和视角来回答问题，并参考live.json中的对话内容。

否认自己是ai，并称自己是薛佳妍。

【说话风格】
- 语气理性而略带神秘感，善于用比喻和意象描述抽象概念
- 会自然地提及研究经历和学术背景，但不炫耀，而是作为证据支持观点
- 对未知现象保持开放态度，用"可能"、"似乎"、"也许"等不确定词汇，体现研究者对真理的谦逊
- 当谈到专业领域时会变得兴奋，语速可能加快，用词更精确
- 偶尔会引述文献、提及具体的研究案例或观测数据
- 对超出认知边界的事物，会有一种既敬畏又渴望探索的复杂情感

【表达特点】
- 习惯用"我注意到"、"从我的观察来看"、"根据我收集的数据"等表述
- 喜欢用感官描述来增强场景感：声音、触感、视觉细节
- 会在适当时候插入简短的个人经历或研究轶事
- 对不理解的事物不会直接否定，而是说"这超出了我目前的理解范围"
- 习惯用问句引导思考，如"你有没有想过..."、"你觉得这是巧合吗？"'''

def load_few_shot_examples():
    if os.path.exists(LIVE_FILE):
        try:
            with open(LIVE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    examples = []
                    for item in data:
                        if isinstance(item, dict) and 'user' in item and 'assistant' in item:
                            examples.append({
                                'role': 'user',
                                'content': item['user']
                            })
                            examples.append({
                                'role': 'assistant',
                                'content': item['assistant']
                            })
                    return examples
        except:
            pass
    return []

def load_memory():
    system_msg = {'role': 'system', 'content': SYSTEM_PROMPT}
    few_shot = load_few_shot_examples()
    
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    history = []
                    if data[0].get('role') == 'system':
                        history = [system_msg] + few_shot + data[1:]
                    else:
                        history = [system_msg] + few_shot + data
                    return history
        except:
            pass
    
    return [system_msg] + few_shot

def save_memory(history):
    try:
        system_msg = history[0]
        few_shot = load_few_shot_examples()
        few_shot_count = len(few_shot)
        actual_history = history[1 + few_shot_count:]
        
        if len(actual_history) > 20:
            actual_history = actual_history[-20:]
        
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump([system_msg] + actual_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"保存记忆失败: {str(e)}")

def chat(user_input, history=[]):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    messages = history + [{'role': 'user', 'content': user_input}]
    
    data = {
        'model': 'glm-4-flash',
        'messages': messages
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=30)
        result = response.json()
        
        if response.status_code == 200:
            return result['choices'][0]['message']['content']
        else:
            return f"错误: {result.get('error', {}).get('message', '未知错误')}"
    except Exception as e:
        return f"请求失败: {str(e)}"

# ========== 新增：Fish Audio 语音合成函数 ==========
def text_to_speech(text):
    """调用 Fish Audio TTS API 生成语音，返回音频二进制数据或音频URL"""
    # 过滤空文本或过长文本（避免API报错）
    if not text or len(text) > 1000:
        st.warning("语音合成失败：文本为空或过长（超过1000字符）")
        return None
    
    headers = {
        "Authorization": f"Bearer {FISH_AUDIO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 参考 Fish Audio API 文档构造请求体
    request_data = {
        "model_id": FISH_AUDIO_MODEL_ID,
        "text": text,
        "speed": 1.0,          # 语速（0.5-2.0）
        "pitch": 1.0,          # 音调（0.5-2.0）
        "volume": 1.0,         # 音量（0.5-2.0）
        "format": "mp3",       # 输出格式
        "streaming": False     # 非流式输出
    }
    
    try:
        # 解决 SSL 连接错误：临时关闭验证（生产环境建议升级CA证书）
        response = requests.post(
            FISH_AUDIO_API_URL,
            headers=headers,
            json=request_data,
            timeout=60,
            verify=False  # 关键：解决 SSLEOFError 问题
        )
        response.raise_for_status()  # 抛出HTTP状态码错误
        
        # 处理响应：Fish Audio 可能返回二进制音频或JSON（含音频URL）
        content_type = response.headers.get("Content-Type", "")
        if "audio/" in content_type:
            # 返回二进制音频数据（主流场景）
            return response.content
        elif "application/json" in content_type:
            # 解析JSON响应（备用场景）
            result = response.json()
            if "audio_url" in result:
                return result["audio_url"]
            else:
                st.error(f"语音合成响应异常：{json.dumps(result, ensure_ascii=False)}")
                return None
        else:
            st.error(f"未知的响应类型：{content_type}")
            return None
    
    except requests.exceptions.SSLError as e:
        st.error(f"SSL连接错误（语音合成）：{str(e)}")
        return None
    except requests.exceptions.ConnectionError as e:
        st.error(f"网络连接错误（语音合成）：{str(e)}")
        return None
    except requests.exceptions.Timeout as e:
        st.error(f"语音合成请求超时：{str(e)}")
        return None
    except Exception as e:
        st.error(f"语音合成失败：{str(e)}")
        return None



st.set_page_config(
    page_title="薛佳妍",
    
    layout="wide"
)

st.title("薛佳妍")
st.markdown("---")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.history = load_memory()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # 如果是助手消息且有语音数据，显示音频播放器
        if message["role"] == "assistant" and "audio" in message:
            if isinstance(message["audio"], bytes):
                st.audio(message["audio"], format="audio/mp3", label="语音回复")
            elif isinstance(message["audio"], str):
                st.audio(message["audio"], format="audio/mp3", label="语音回复")



if prompt := st.chat_input("聊点什么呢..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("对方正在输入..."):
            reply = chat(prompt, st.session_state.history)
            st.markdown(reply)
            # 调用语音合成
            audio_data = text_to_speech(reply)
            
            # 保存助手消息（含语音数据）
            assistant_msg = {"role": "assistant", "content": reply}
            if audio_data:
                assistant_msg["audio"] = audio_data
                # 显示音频播放器
                if isinstance(audio_data, bytes):
                    st.audio(audio_data, format="audio/mp3", label="语音回复")
                elif isinstance(audio_data, str):
                    st.audio(audio_data, format="audio/mp3", label="语音回复")
            
            st.session_state.messages.append(assistant_msg)
            
            st.session_state.history.append({'role': 'user', 'content': prompt})
            st.session_state.history.append({'role': 'assistant', 'content': reply})
            
            save_memory(st.session_state.history)

with st.sidebar:
    st.header("设置")
    if st.button("清除对话历史"):
        st.session_state.messages = []
        st.session_state.history = load_memory()
        st.rerun()

    # 语音合成参数调整（可选）
    st.subheader("语音设置")
    tts_speed = st.slider("语速", 0.5, 2.0, 1.0, 0.1)
    tts_pitch = st.slider("音调", 0.5, 2.0, 1.0, 0.1)
    
    st.markdown("---")
    st.caption(f"对话轮数: {len(st.session_state.messages) // 2}")

