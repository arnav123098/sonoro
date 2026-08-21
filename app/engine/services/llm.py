from services.inst import default_sys, char_desc_inst, summarizer_inst
from openai import OpenAI
import json
import uuid

class Context:
    def __init__(self, interface_type, animation_paths):
        self.convo_context, self.curr_character = [], ''
        self.recent = {}

        self.interface_type = interface_type
        self.custom_sys = None
        self.animation_paths = animation_paths

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
        self.recent = {}
        self.convo_context = []
        self.curr_character = character_name

        if sys is not None: self.convo_context.append(sys)

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

    def make_context(self, interface_type, animation_paths=None):
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

        if event_name == 'user_message':
            return event['content']

        content = {json.dumps(event['content'], indent=2)} if type(event['content']) == dict else event['content']

        return f'[{event['event_name']}] {content}'

    def get_character_description(self, data, web_search=None): # {data: urlORtext, type: urlORtext}
        text = ''

        if data['type'] == 'text': text = data['data']
        elif data['type'] == 'url' and web_search is not None: text = web_search.scrape(data['data'])

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

        args = dict(
            model=self.model,
            messages=context,
        )

        if "qwen" in self.model:
            args["reasoning_effort"] = "none"

        response = self.client.chat.completions.create(**args)
        desc = response.choices[0].message.content

        return desc

    def get_response(self, event):
        self.summarize_context()
        context = list(self.context.make_context(self.parse(event)))

        info_content = f'Recent Conversation Summary:\n{json.dumps(self.context.recent, indent=2)}'
        if self.memory: info_content += f'\nRelated Information from memory:\n{json.dumps(self.memory.react(self.context.curr_character, event['content']))}'

        info = {
            'role': 'user',
            'content': info_content
        }
        context = context[:-1] + [info] + [context[-1]]
        # print('info: ', info)

        args = dict(
            model=self.model,
            messages=context,
        )

        if "qwen" in self.model:
            args["reasoning_effort"] = "none"
        
        try:
            response = self.client.chat.completions.create(**args)
        except OpenAI.APIStatusError:
            return {
                "message": "You've probably hit your rate limit!"
            }

        res = response.choices[0].message.content
        res = res.strip('```').strip('json')

        if self.context.interface_type == 'webui': print('raw_response: ', res)

        self.context.make_context(res, is_llm=True)

        return json.loads(res)

    def summarize_context(self, upto=20):
        if len(self.context.convo_context) <= upto + 1: return # + 1 for sys

        convo = ''
        for message in self.context.convo_context[1:]:
            convo += f"{'user' if message['role'] == 'user' else self.context.curr_character}: {message['content']}\n"

        if not convo: return

        print(f'[memory] summarizing conversation...')

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

        args = dict(
            model=self.model,
            messages=context,
        )

        if "qwen" in self.model:
            args["reasoning_effort"] = "none"

        response = self.client.chat.completions.create(**args)

        res = response.choices[0].message.content
        res = res.strip('```').strip('json')

        recent = json.loads(res)
        self.context.recent = recent

        self.context.convo_context = self.context.convo_context[:1] # might be kinda aggressive

    def save_mem(self):
        if not self.context.curr_character or not self.memory: return

        print(f"[memory] saving memory for {self.context.curr_character}...")
        self.summarize_context(0)

        if self.context.recent:
            ids = []
            docs = []
            metadatas = []

            temporal_id =  str(uuid.uuid4())

            for data in self.context.recent.values():
                ids.append(str(uuid.uuid4()))
                docs.append(data['summary'])
                metadatas.append({'tags': data['tags'], 'temporal_id': temporal_id})

            self.context.recent = {}

            self.memory.add(self.context.curr_character, ids, docs, metadatas)
