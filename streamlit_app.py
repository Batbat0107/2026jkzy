import streamlit as st
import requests
import json
import os
import dns.resolver
from urllib3.util.connection import create_connection

# ========== 原有配置 ==========
API_KEY = '115d84b24f1f4c95876f173b263e4e60.kkBRUmuElHpZcoS2'
API_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
MEMORY_FILE = 'memory.json'
LIVE_FILE = 'live.json'

# ========== Fish Audio 语音合成配置（适配新接口） ==========
FISH_AUDIO_API_KEY = "c57b52d5a8e8c30b817c5c8bb73c3821d34548050379565b1cedbdf2e87c5a38"
# 修正接口地址：新接口是 /api/open/tts
FISH_AUDIO_API_URL = "https://fishspeech.net/api/open/tts"
FISH_AUDIO_MODEL_ID = "f6e717d9-82c5-4fca-83f7-399c419ce643"  # reference_id（原model_id）

# ========== 自定义DNS解析（解决域名解析失败） ==========
PUBLIC_DNS_SERVERS = ["223.5.5.5", "8.8.8.8", "114.114.114.114"]

def custom_dns_resolve(hostname):
    """使用公共DNS解析域名，避免本地DNS污染"""
    resolver = dns.resolver.Resolver()
    resolver.nameservers = PUBLIC_DNS_SERVERS
    resolver.timeout = 5
    resolver.lifetime = 5
    try:
        answers = resolver.resolve(hostname, 'A')
        return answers[0].address
    except Exception as e:
        st.warning(f"DNS解析失败：{str(e)}，使用系统默认DNS")
        return None

def patched_create_connection(address, *args, **kwargs):
    """替换urllib3的DNS解析逻辑，优先使用公共DNS"""
    host, port = address
    ip = custom_dns_resolve(host)
    if ip:
        return create_connection((ip, port), *args, **kwargs)
    return create_connection(address, *args, **kwargs)

# 应用自定义DNS解析
urllib3.util.connection.create_connection = patched_create_connection

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

# ========== 适配新接口的语音合成函数 ==========
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
    # 过滤空文本或过长文本（避免API报错）
    if not text or len(text) > 1000:
        st.warning("语音合成失败：文本为空或过长（超过1000字符）")
        return None
    
    # 构造请求头（适配新接口）
    headers = {
        "Authorization": f"Bearer {FISH_AUDIO_API_KEY}",
        "Content-Type": "application/json"  # 使用JSON格式（推荐）
    }
    
    # 构造请求参数（严格匹配新接口规范）
    request_data = {
        "reference_id": FISH_AUDIO_MODEL_ID,  # 修正参数名：model_id → reference_id
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
        # 发起请求（保留SSL临时关闭，解决解析/连接问题）
        response = requests.post(
            FISH_AUDIO_API_URL,
            headers=headers,
            json=request_data,
            timeout=60,
            verify=False  # 生产环境建议升级CA证书后移除
        )
        response.raise_for_status()  # 抛出HTTP状态码错误（4xx/5xx）
        
        # 处理响应（区分cache=false/true两种场景）
        content_type = response.headers.get("Content-Type", "").lower()
        
        # 场景1：cache=false → 返回二进制音频流（主流场景）
        if "audio/" in content_type:
            return response.content
        
        # 场景2：cache=true → 返回JSON（含audio_url）
        elif "application/json" in content_type:
            result = response.json()
            if result.get("success") and result.get("audio_url"):
                st.info(f"语音合成成功，字符消耗：{result.get('characters_used', 0)}，剩余配额：{result.get('quota_remaining', 0)}")
                return result["audio_url"]
            else:
                st.error(f"语音合成失败：{result.get('error', '未知错误')}")
                return None
        
        # 未知响应类型
        else:
            st.error(f"未知的响应类型：{content_type}，响应内容：{response.text[:200]}")
            return None
    
    except requests.exceptions.SSLError as e:
        st.error(f"SSL连接错误（语音合成）：{str(e)}")
        return None
    except requests.exceptions.ConnectionError as e:
        st.error(f"网络连接错误（语音合成）：{str(e)}")
        # 额外提示DNS/网络排查
        st.info("建议检查：1. 切换公共DNS（阿里云223.5.5.5）；2. 切换网络（如手机热点）；3. 关闭VPN/代理")
        return None
    except requests.exceptions.Timeout as e:
        st.error(f"语音合成请求超时：{str(e)}")
        return None
    except requests.exceptions.HTTPError as e:
        # 捕获HTTP错误（如401密钥无效、403配额不足等）
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
    page_icon="🔮",
    layout="wide"
)

st.title("薛佳妍 🔮")
st.markdown("---")

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.history = load_memory()

# 显示历史对话
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # 显示语音播放器（兼容二进制/URL）
        if message["role"] == "assistant" and "audio" in message:
            if isinstance(message["audio"], bytes):
                st.audio(message["audio"], format="audio/mp3", label="语音回复")
            elif isinstance(message["audio"], str):
                st.audio(message["audio"], format="audio/mp3", label="语音回复")

# 侧边栏设置（新增TTS版本/情绪等配置）
with st.sidebar:
    st.header("设置")
    
    # 清除对话历史
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
    
    # 语音合成高级设置（适配新接口参数）
    st.subheader("语音合成设置")
    tts_version = st.selectbox(
        "TTS版本",
        options=["s1", "v1", "v2", "v3-turbo", "v3-hd"],
        index=0,
        help="s1=传统版本（推荐）；v3-hd=高清版（支持情绪）"
    )
    tts_speed = st.slider("语速", 0.5, 2.0, 1.0, 0.1)
    tts_volume = st.slider("音量", -20, 20, 0, 1, help="范围-20（静音）~20（最大）")
    
    # V3版本专属配置
    if "v3" in tts_version:
        tts_emotion = st.selectbox(
            "情绪（仅V3支持）",
            options=["auto", "calm", "happy", "sad", "angry", "fearful", "disgusted", "surprised", "fluent"],
            index=1
        )
        tts_language = st.selectbox(
            "语言增强（仅V3支持）",
            options=["auto", "zh", "en"],
            index=0
        )
    else:
        tts_emotion = "auto"
        tts_language = "zh"
    
    # 缓存模式（返回URL/二进制）
    tts_cache = st.checkbox("启用缓存（返回音频URL）", value=False, help="false=直接返回音频文件；true=返回URL（节省带宽）")
    
    st.markdown("---")
    st.caption(f"对话轮数: {len(st.session_state.messages) // 2}")
    st.caption("Powered by GLM-4 & Fish Audio")

# 处理用户输入
if prompt := st.chat_input("聊点什么呢..."):
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 生成助手回复
    with st.chat_message("assistant"):
        with st.spinner("对方正在输入..."):
            # 调用GLM-4生成文本回复
            reply = chat(prompt, st.session_state.history)
            st.markdown(reply)
            
            # 调用新的TTS接口（传入侧边栏配置的参数）
            audio_data = text_to_speech(
                text=reply,
                speed=tts_speed,
                volume=tts_volume,
                version=tts_version,
                emotion=tts_emotion,
                language=tts_language,
                cache=tts_cache
            )
            
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
            
            # 更新对话历史
            st.session_state.history.append({'role': 'user', 'content': prompt})
            st.session_state.history.append({'role': 'assistant', 'content': reply})
            
            # 保存记忆
            save_memory(st.session_state.history)
