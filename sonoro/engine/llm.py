from inst import instructions, char_desc_inst, summarizer_inst
from openai import OpenAI
import json
import uuid
from data import Data

class Context:
    def __init__(self):
        self.convo_context, self.curr_character = [], ''
        self.recent = {}

    def make_character_sys(self, config):
        name = config['name']
        description = config.get('description')
        lore = config.get('background_lore')
        examples = config.get('convo_examples')

        sys = f'You are {name}.'
        if description is not None: sys += f'\n\nAbout you:\n{description}'
        if lore is not None: sys += f'\n\nLore:\n{lore}'

        animation_list = [f.rstrip('.fbx') for f in Data.get_animation_paths()]

        sys += f'\n\nInstructions:\n{instructions(animation_list, examples)}'

        return {
            'role': 'system',
            'content': sys
        }

    def select_character(self, config):
        sys = self.make_character_sys(config)

        self.reset_context(config['name'], sys)

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
        self.context = Context()
        self.memory = memory

        self.client = None
        self.model = None

    def make_client(self, config):
        llm_config = config.get('llm', {})
        base_url, api_key, model = llm_config.get('base_url'), llm_config.get('api_key'), llm_config.get('model')

        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        ) if base_url and api_key else None

        self.model = model if model and self.client else None

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

        info = {
            'role': 'user',
            'content': f'Recent Conversation Summary:\n{json.dumps(self.context.recent, indent=2)}\nRelated Information from memory:\n{json.dumps(self.memory.react(self.context.curr_character, event['content']))}'
        }
        context = context[:-1] + [info] + [context[-1]]
        # print('info: ', info)

        args = dict(
            model=self.model,
            messages=context,
        )

        if "qwen" in self.model:
            args["reasoning_effort"] = "none"
        
        
        response = self.client.chat.completions.create(**args)

        res = response.choices[0].message.content
        res = res.strip('```').strip('json')
        print('res: ', res)

        self.context.make_context(res, is_llm=True)

        # print('raw_res: ', res)
        return json.loads(res)

    def summarize_context(self, upto=20):
        if len(self.context.convo_context) <= upto + 1: return # + 1 for sys

        convo = ''
        for message in self.context.convo_context[1:]:
            convo += f"{'user' if message['role'] == 'user' else self.context.curr_character}: {message['content']}\n"

        if not convo: return

        print(f'summarizing conversation...')

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

        self.context.convo_context = self.context.convo_context[:1]

    def set_character(self, config):
        self.save_mem()
        self.context.select_character(config)

    def save_mem(self):
        if not self.context.curr_character: return

        print(f"saving memory for {self.context.curr_character}...")
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
