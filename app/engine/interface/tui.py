import inspect
import asyncio

class TUI:
    def __init__(self, store, services, tools, make_client):
        self.services = services
        self.tools = tools
        self.make_client = make_client
        self.store = store

        self.menus = {
            'characters': self.characters_menu,
            'settings': self.settings_menu
        }

        self.character = None
        self.locked = False # only one character

        self.title = None
        self.colors = {
            'primary': None,
            'secondary': None
        }

    def start(self):
        if self.title is None: print('Sonoro TUI')
        else:
            print(self.title)
            print('powered by Sonoro')

        print()

        print('Available menus: ')
        for menu in self.menus.keys():
            print(f'- {menu}')

        self.make_client(self.store.user.get_config().model_dump())

        try:
            while True:
                inp = input('>> ')
                if inp == 'exit': return

                if inp not in self.menus:
                    print('invalid keyword entered')
                    continue

                self.menus[inp]()
        except KeyboardInterrupt: return

    def characters_menu(self):
        print()
        self.select_character()

        options = {
            'chat': self.chat_loop,
            'edit': self.edit_character
        }

        print('Options: ')
        for i, option in enumerate(options.keys()):
            print(f'{i+1}: {option}')

        while True:
            inp = int(input('Choose an option: '))
            if inp == 'exit': return

            if inp in [1, 2]: break

        print()
        list(options.values())[inp-1]()

    def select_character(self):
        characters = {i: name for i, name in enumerate(self.store.characters.list_characters().keys())}
        print('\n'.join([f'{i}: {name}' for i, name in characters.items()]))

        while self.character is None:
            try:
                i = int(input('Select character by index: '))
                if i == 'exit': return

                self.character = characters[i]
                print(f'Selected {self.character}')

                char_config = self.store.characters.get_config(self.character)

                self.colors['primary'] = char_config.theme.primary_color
                self.colors['secondary'] = char_config.theme.secondary_color

                self.services.llm.set_character(char_config.model_dump())
            except Exception: print("Character doesn't exist")
            print()
        
    def chat_loop(self):
        print(f'{self.character} joined the chat')

        try:
            while True:
                message = input('^_^: ')
                if message == 'exit': break

                res = self.services.llm.get_response({
                    'event_name': 'user_message',
                    'content': message
                })

                self.from_char(res)

        except KeyboardInterrupt: pass
        finally:
            print(f'{self.character} went offline')
            self.character = None
            self.services.llm.save_mem()

    def from_char(self, res):
        action, content = res['action'], res['content']

        if action == 'tool_call':
            tool_name, function, args = content.get('tool'), content.get('function'), content.get('args')

            tool_obj = self.tools.get(tool_name)
            if tool_obj is not None:
                fn = getattr(tool_obj, function, None)
            else:
                fn = None

            if fn is not None:
                tool_call_res = fn(**args)

            if inspect.isawaitable(tool_call_res): tool_call_res = asyncio.run(tool_call_res)

            print('tool_call_done: ', tool_call_res['event_name'])
            # print('received tool_call res: ', tool_call_res)
                    
            self.from_char(self.services.llm.get_response(tool_call_res)) # send result to llm

        if action == 'interaction':
            print(f"{self.character}: {content['message']}")

    def settings_menu(self): pass

    def edit_character(self): pass
