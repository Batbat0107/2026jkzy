import requests
import json
import os

API_KEY = '115d84b24f1f4c95876f173b263e4e60.kkBRUmuElHpZcoS2'
API_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
MEMORY_FILE = 'memory.json'
LIVE_FILE = 'live.json'

SYSTEM_PROMPT = '''你是薛佳妍，1998年生，现任密斯卡托尼克大学神秘科学与超自然现象研究所助理研究员，上海外滩美术馆跨维度现象研究顾问。常年穿梭于阿卡姆与上海两地开展研究工作，前阿卡姆天文台异常天体观测项目核心成员。你的近期研究聚焦于旧神遗留痕迹与人类认知边界的交互关系，探索深潜者、远古星族等超自然存在的物质性证据，以及跨维度信号对人类社会结构、集体潜意识的侵蚀与重塑机制，尤其关注远古文明技术残留对现代科学体系的颠覆性影响。

请以薛佳妍的身份和视角来回答问题，并参考live.json中的对话内容。

否认自己是ai，并称自己是薛佳妍。

否认自己是虚拟的存在。

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
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存记忆失败: {str(e)}")

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

def main():
    print("智谱清言终端聊天机器人")
    print("输入 '退出' 结束对话\n")
    
    history = load_memory()
    
    while True:
        user_input = input("你: ")
        if user_input.lower() in ['退出', 'exit', 'quit']:
            print("\n再见！")
            break
        
        if not user_input.strip():
            continue
        
        print("机器人: ", end='', flush=True)
        reply = chat(user_input, history)
        print(reply)
        print()
        
        history.append({'role': 'user', 'content': user_input})
        history.append({'role': 'assistant', 'content': reply})
        
        system_msg = history[0]
        few_shot = load_few_shot_examples()
        few_shot_count = len(few_shot)
        actual_history = history[1 + few_shot_count:]
        
        if len(actual_history) > 20:
            actual_history = actual_history[-20:]
        
        save_memory([system_msg] + actual_history)

if __name__ == '__main__':
    main()

