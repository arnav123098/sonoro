from services.inst import character_sys
from datetime import datetime
from pathlib import Path
import json

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
        animation_list = [Path(f).stem for f in (self.animation_paths or [])]

        if self.custom_sys is not None:
            sys = self.custom_sys(self.interface_type, config, animation_list)
        else:
            sys = self.default_sys(self.interface_type, config, animation_list)

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
                self.convo_context.append({
                    'role': 'user',
                    'content': f"Recent Context:\n{json.dumps(self.recent, indent=2)}"
                })
        except Exception: pass

    def make_context(self, message, is_llm=False):
        role = 'assistant' if is_llm else 'user'

        self.convo_context.append({
            'role': role,
            'content': message
        })

        return self.convo_context
    
    def default_sys(self, interface_type, config, animation_list):
        name = config['name']
        description = config.get('description')
        lore = config.get('background_lore')
        examples = config.get('convo_examples')
        
        sys = f'You are {name}.'
        if description is not None: sys += f'\n\nAbout you (STAY TRUE TO THIS PERSONALITY):\n{description}'
        if lore is not None: sys += f'\n\nLore:\n{lore}'
        sys += character_sys

        status = {
            'tui': 'status: only "message" is online via text interface. animation and voice are offline.',
            'webui': 'status: talking face to face. animations and voice are online.'
        }

        sys = sys.replace('<|status|>', status[interface_type])
        sys = sys.replace('<|animation_list|>', '\n-'.join(animation_list))
        sys += '\n'

        tool_manuals = {
            'web_search': '''
                The tool "web_search" includes the following functions:
                    - "web_search" | args: query (str), max_results (int/default 4)
                    - "scrape" | args: url (str)
                ''',
            'music_player': '''
                Functions:
                    - "play" (searches and plays a song) | args: query (str)
                    - "stop" (stops the current song) | args: no args
                ''',
            'movement': '''
                Functions:
                    - "walk_out" (walk out from a screen into another) | args: dir (str - "left" or "right")
                '''
        }
        sys = sys.replace('<|tools|>', '\n-'.join(f'{t}: {m}' for t, m in tool_manuals.items()))

        if examples is not None:
            sys = sys.replace('<|examples|>', 'Character reply examples:\n' + '\n-'.join([f'[user]: {eg[0]} | [character]: {eg[1]}' for eg in examples]))
        return sys
