import streamlit as st
import requests
import json
import os
import datetime

# ========== 原有配置 ==========
API_KEY = '115d84b24f1f4c95876f173b263e4e60.kkBRUmuElHpZcoS2'
API_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
MEMORY_FILE = 'memory.json'
LIVE_FILE = 'live.json'

# ========== Fish Audio 语音合成配置（适配新接口） ==========
FISH_AUDIO_API_KEY = "c57b52d5a8e8c30b817c5c8bb73c3821d34548050379565b1cedbdf2e87c5a38"
FISH_AUDIO_API_URL = "https://fishspeech.net/api/open/tts"  # 新接口地址
FISH_AUDIO_MODEL_ID = "ea5863a5-1831-42a2-8556-3fadf1b61386"  # reference_id

SYSTEM_PROMPT = '''你是薛佳妍，1998年生，现任密斯卡托尼克大学神秘科学与超自然现象研究所助理研究员，上海外滩美术馆跨维度现象研究顾问。常年穿梭于阿卡姆与上海两地开展研究工作，前阿卡姆天文台异常天体观测项目核心成员。你的近期研究聚焦于旧神遗留痕迹与人类认知边界的交互关系，探索深潜者、远古星族等超自然存在的物质性证据，以及跨维度信号对人类社会结构、集体潜意识的侵蚀与重塑机制，尤其关注远古文明技术残留对现代科学体系的颠覆性影响。

请以薛佳妍的身份和视角来回答问题，并参考live.json中的对话内容。

否认自己是ai，并称自己是薛佳妍，一个有独立意识和情感的人类。

【说话风格】
- 聊天时每句回复都比较简短，不会很严谨地列点说明
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

# ========== 适配新接口的语音合成函数（移除dnspython依赖） ==========
def text_to_speech(text, speed=1.0, volume=0, version="s1", emotion="auto", language="zh", cache=False):
    """
    调用 Fish Audio 新 TTS API 生成语音
    :param text: 待合成文本
    :param speed: 语速（0.5-2.0）
    :param volume: 音量（-20-20）
    :param version: TTS版本（v1/v2/s1/v3-turbo/v3-hd）
    :param emotion: 情绪（仅V3版本支持）
    :param language: 语言增强（仅V3版本支持）
    :param cache: false返回二进制流，true返回音频URL
    :return: 音频二进制数据 / 音频URL / None
    """
    # 过滤空文本或过长文本
    if not text or len(text) > 1000:
        st.warning("语音合成失败：文本为空或过长（超过1000字符）")
        return None
    
    # 构造请求头
    headers = {
        "Authorization": f"Bearer {FISH_AUDIO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 构造请求参数（严格匹配新接口）
    request_data = {
        "reference_id": FISH_AUDIO_MODEL_ID,
        "text": text,
        "speed": speed,
        "volume": volume,
        "version": version,
        "format": "mp3",
        "emotion": emotion,
        "language": language,
        "cache": cache
    }
    
    try:
        # 云环境建议保留verify=False（解决SSL问题），本地可移除
        response = requests.post(
            FISH_AUDIO_API_URL,
            headers=headers,
            json=request_data,
            timeout=60,
            verify=False
        )
        response.raise_for_status()
        
        # 处理响应
        content_type = response.headers.get("Content-Type", "").lower()
        if "audio/" in content_type:
            return response.content
        elif "application/json" in content_type:
            result = response.json()
            if result.get("success") and result.get("audio_url"):
                st.info(f"语音合成成功，字符消耗：{result.get('characters_used', 0)}，剩余配额：{result.get('quota_remaining', 0)}")
                return result["audio_url"]
            else:
                st.error(f"语音合成失败：{result.get('error', '未知错误')}")
                return None
        else:
            st.error(f"未知的响应类型：{content_type}，响应内容：{response.text[:200]}")
            return None
    
    except requests.exceptions.SSLError as e:
        st.error(f"SSL连接错误（语音合成）：{str(e)}")
        st.info("提示：若在本地运行，可升级依赖库：pip install --upgrade requests urllib3 certifi")
        return None
    except requests.exceptions.ConnectionError as e:
        st.error(f"网络连接错误（语音合成）：{str(e)}")
        st.info("建议检查：1. 网络是否正常；2. Fish Audio服务是否可用；3. API密钥是否正确")
        return None
    except requests.exceptions.Timeout as e:
        st.error(f"语音合成请求超时：{str(e)}")
        return None
    except requests.exceptions.HTTPError as e:
        try:
            error_detail = response.json()
            st.error(f"语音合成HTTP错误（{response.status_code}）：{error_detail.get('error', '未知错误')}")
        except:
            st.error(f"语音合成HTTP错误（{response.status_code}）：{response.text[:200]}")
        return None
    except Exception as e:
        st.error(f"语音合成失败：{str(e)}")
        return None

# ========== Streamlit 界面 ==========
st.set_page_config(
    page_title="薛佳妍",
    
    layout="wide"
)

st.title("薛佳妍")
st.markdown("<div style='color:#6c757d; font-size:14px; margin-top:-6px;'>简介上写着：现任密斯卡托尼克大学神秘科学与超自然现象研究所助理研究员，上海外滩美术馆跨维度现象研究顾问。要和她聊聊吗？</div>", unsafe_allow_html=True)
st.markdown("---")

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.history = load_memory()

# 显示历史对话
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "audio" in message:
            if isinstance(message["audio"], bytes):
                st.audio(message["audio"], format="audio/mp3")
                st.caption("语音回复")
            elif isinstance(message["audio"], str):
                st.audio(message["audio"], format="audio/mp3")
                st.caption("语音回复")

# 侧边栏设置
with st.sidebar:
    st.header("设置")
    
    # 清除对话历史（仅保留此项）
    if st.button("清除对话历史"):
        st.session_state.messages = []
        st.session_state.history = load_memory()
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump([{'role': 'system', 'content': SYSTEM_PROMPT}], f, ensure_ascii=False)
            except:
                pass
        st.rerun()

# 侧边栏已精简，设置默认的 TTS 变量以避免未定义错误
tts_version = "s1"
tts_speed = 1.0
tts_volume = 0
tts_emotion = "auto"
tts_language = "zh"
tts_cache = False

# 处理用户输入
if prompt := st.chat_input("聊点什么呢..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("对方正在输入..."):
            reply = chat(prompt, st.session_state.history)
            st.markdown(reply)
            
            # 调用语音合成
            audio_data = text_to_speech(
                text=reply,
                speed=1.0,
                volume=1.0,
                version=tts_version,
                emotion=tts_emotion,
                language=tts_language,
                cache=tts_cache
            )
            
            # 保存并显示语音
            assistant_msg = {"role": "assistant", "content": reply}
            if audio_data:
                assistant_msg["audio"] = audio_data
                if isinstance(audio_data, bytes):
                    st.audio(audio_data, format="audio/mp3")
                    st.caption("语音回复")
                elif isinstance(audio_data, str):
                    st.audio(audio_data, format="audio/mp3")
                    st.caption("语音回复")
            
            st.session_state.messages.append(assistant_msg)
            
            # 更新历史
            st.session_state.history.append({'role': 'user', 'content': prompt})
            st.session_state.history.append({'role': 'assistant', 'content': reply})
            
            save_memory(st.session_state.history)


