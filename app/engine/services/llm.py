from services.inst import default_sys, char_desc_inst, summarizer_inst, mem_save_inst
from openai import OpenAI
import json
import uuid
from datetime import datetime
from pathlib import Path

class Context:
    def __init__(self, interface_type, animation_paths):
        self.convo_context, self.curr_character = [], ''

        self.recent = {}

        self.interface_type = interface_type
        self.custom_sys = None
        self.animation_paths = animation_paths

    def get_time(self):
        now = datetime.now()

        date = now.strftime("%d-%m-%Y")
        time = now.strftime("%H:%M")
        day = now.strftime("%A") 

        return {
            'date': date,
            'time': time,
            'day': day
        }

    def select_character(self, config):
        sys = self.make_character_sys(config)
        self.reset_context(config['name'], sys)

    def make_character_sys(self, config):
        animation_list = [f.rstrip('.fbx') for f in (self.animation_paths or [])]

        if self.custom_sys is not None:
            sys = self.custom_sys(self.interface_type, config, animation_list)
        else:
            sys = default_sys(self.interface_type, config, animation_list)

        return {
            'role': 'system',
            'content': sys
        }

    def reset_context(self, character_name='', sys=None):
        self.convo_context = []
        self.curr_character = character_name
        if sys is not None: self.convo_context.append(sys)
        
        self.recent = {}
        try:
            with open('recent.json', 'r') as f:
                self.recent = json.loads(f.read())[character_name]
        except Exception: pass

    def make_context(self, message, is_llm=False):
        role = 'assistant' if is_llm else 'user'

        self.convo_context.append({
            'role': role,
            'content': message
        })

        return self.convo_context

class LLM:
    def __init__(self, memory=None):
        self.context = None
        self.memory = memory

        self.client = None
        self.model = None

    def list_models(self):
        models = self.client.models.list().data
        return [m.id for m in models if 'whisper' not in m.id]

    def make_context(self, interface_type, animation_paths=None): # default context setup
        self.context = Context(interface_type, animation_paths)

    def set_custom_sys(self, custom_sys_func):
        # custom_sys_func takes args: interface_type, config and animation_list
        self.context.custom_sys = custom_sys_func

    def make_client(self, config):
        llm_config = config.get('llm', {})
        base_url, api_key, model = llm_config.get('base_url'), llm_config.get('api_key'), llm_config.get('model')

        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        ) if base_url and api_key else None

        self.model = model if model and self.client else None

    def set_character(self, config):
        self.save_mem()
        self.context.select_character(config)

    @staticmethod
    def parse(event):
        event_name = event['event_name']

        if event_name == 'user_message': return event['content']['content']

        content = {json.dumps(event['content'], indent=2)} if type(event['content']) == dict else event['content']

        return f'[{event['event_name']}] {content}'

    def use_llm(self, context): # made this for sdk
        args = dict(
            model=self.model,
            messages=context,
        )

        if "qwen" in self.model:
            args["reasoning_effort"] = "none"

        try:
            response = self.client.chat.completions.create(**args)
        except Exception as e:
            # print('Exception encountered: ', e) # debug
            return '[OpenAIError]'

        return response.choices[0].message.content

    def get_character_description(self, data, web_search=None): # {data: urlORtext, type: urlORtext}
        text = ''

        if data['type'] == 'text': text = data['data']
        elif data['type'] == 'url' and web_search is not None:
            text = web_search.scrape(data['data'])['content']

        if not text: return

        context = [
            {
                "role": "system",
                "content": char_desc_inst
            },
            {
                "role": "user",
                "content": text
            }
        ]

        return self.use_llm(context)

    def get_response(self, event):
        self.summarize_context()
        context = list(self.context.make_context(self.parse(event)))

        info_content = f'Recent Conversation Summary:\n{json.dumps(self.context.recent, indent=2)}'

        if self.memory:
            text = event['content']['content'] if event['event_name'] == 'user_message' else event['content']
            tags = list(set(tag for t in self.context.recent.values() for tag in t['tags'] if tag != 'none')) or None
            # print('tags: ', tags) # debug
            info_content += f'\nRelated Information from memory:\n{json.dumps(self.memory.react(self.context.curr_character, text, tags).get('memories'))}'

        now = self.context.get_time()
        info_content += f"\nTIME: {now['day'], now['date']} | {now['time']}"

        info = {
            'role': 'user',
            'content': info_content
        }
        context = context[:-1] + [info] + [context[-1]]
        # # print('info: ', info) # debug
        # print('context: ', context) # debug

        res = self.use_llm(context)

        if res == '[OpenAIError]':
            return {
                "action": "interaction",
                "content": {
                    "message": "OOPS! You've probably hit your rate limit!"
                }
            }
        
        res = res.strip('```').strip('json')

        if self.context.interface_type == 'webui': print('raw_response: ', res)

        self.context.make_context(res, is_llm=True)
        return json.loads(res)

    def summarize_context(self, upto=6):
        if len(self.context.convo_context) <= upto + 1: return # + 1 for sys

        convo = ''
        for message in self.context.convo_context[1:]:
            convo += f"{'user' if message['role'] == 'user' else self.context.curr_character}: {message['content']}\n"

        if not convo: return

        context = [
            {
                'role': 'system',
                'content': summarizer_inst
            },
            {
                'role': 'user',
                'content': json.dumps({
                    'convo': convo,
                    'existing_summary': self.context.recent
                }, indent=2)
            }
        ]

        res = self.use_llm(context)

        if res == '[OpenAIError]':
            print("[Exception] Couldn't summarize chat because of hitting rate limit")
            return

        print(f'[memory] summarizing conversation...')
    
        res = res.strip('```').strip('json')

        recent = json.loads(res)
        self.context.recent = recent

        self.context.convo_context = self.context.convo_context[:1] # might be kinda aggressive

    def get_mem(self):
        convo = 'CONVERSATION:\n'
        for message in self.context.convo_context[1:]:
            convo += f"{'user' if message['role'] == 'user' else self.context.curr_character}: {message['content']}\n"

        convo += f'\n\nSUMMARY OF RECENT TOPICS:\n{self.context.recent}'
        if not convo: return

        context = [
            {
                'role': 'system',
                'content': mem_save_inst
            },
            {
                'role': 'user',
                'content': convo
            }
        ]

        res = self.use_llm(context)
        if res == '_no_save': return

        try:
            res = json.loads(res)
        except Exception:
            return

        return res

    def save_recent(self):
        print(f"[memory] saving recent context for {self.context.curr_character}")

        try:
            with open('recent.json', 'r') as f:
                r = f.read()
                all_recent = json.loads(r) if r else {}
        except FileNotFoundError:
            all_recent = {}

        all_recent[self.context.curr_character] = self.context.recent

        # print('all_recent: ', all_recent) # debug

        with open('recent.json', 'w') as f:
            f.write(json.dumps(all_recent, indent=2))

    def save_mem(self):
        if self.context.recent: self.save_recent()

        if not self.context.curr_character or not self.memory: return
        to_save = self.get_mem()

        if to_save is not None:
            print(f"[memory] saving memory for {self.context.curr_character}...")

            # print(to_save) # debug
            
            ids = []
            docs = []
            metadatas = []

            temporal_id =  self.context.get_time()['date']

            for data in to_save.values():
                ids.append(str(uuid.uuid4()))
                docs.append(data['summary'])
                metadatas.append({'tags': data['tags'], 'temporal_id': temporal_id})

            self.memory.add(self.context.curr_character, ids, docs, metadatas)
