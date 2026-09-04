import inspect
import asyncio
import time

class TUI:
    def __init__(self, store, services):
        self.services = services
        self.tools = services.tools.tools
        self.store = store
        self.tool_call = None

        self.menus = {
            'characters': self.characters_menu,
            'settings': self.settings_menu
        }

        self.session = None

        self.title = None
        self.colors = {
            'primary': None,
            'secondary': None
        }

        # SONORO HANDLERS
        self.on_from_user = None

        self.ext_id = None

    def start(self):
        print('starting tui...')
        time.sleep(2)

        if self.title is None: print('Sonoro TUI')
        else:
            print(self.title)
            print('powered by Sonoro')

        print()

        print('Available menus: ')
        for menu in self.menus.keys():
            print(f'- {menu}')

        self.services.make_client(self.store.user.get_config().model_dump())

        try:
            while True:
                inp = input('>> ')
                if inp == 'exit': break

                if inp not in self.menus:
                    print('invalid keyword entered')
                    continue

                self.menus[inp]()
        except KeyboardInterrupt: pass
        finally:
            self.services.server.should_exit = True
            return

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

        while self.session.character is None:
            try:
                i = int(input('Select character by index: '))
                if i == 'exit': return

                self.session.character = characters[i]
                print(f'Selected {self.session.character}')

                char_config = self.store.characters.get_config(self.session.character)

                self.colors['primary'] = char_config.theme.primary_color
                self.colors['secondary'] = char_config.theme.secondary_color

                self.services.llm.set_character(char_config.model_dump())
            except Exception: print("Character doesn't exist")
            print()
        
    def chat_loop(self):
        print(f'{self.session.character} joined the chat')

        try:
            while True:
                message = input('^_^: ')
                if message == 'exit': break

                data = {'type': 'text', 'content': message}

                asyncio.run(self.on_from_user({
                    'event_name': 'user_message',
                    'content': data
                }))

        except KeyboardInterrupt: pass
        finally:
            print(f'{self.session.character} went offline')
            self.session.character = None
            self.services.llm.save_mem()

    def to_ui(self, content):
        print(f"{self.session.character}: {content['message']}")

    async def default_from_char(self, res):
        action, content = res['action'], res['content']

        if action == 'interaction':
            self.to_ui(content)
        elif action == 'tool_call':
            await self.tool_call(content['tool'], content.get('function'), content.get('args'))

    def settings_menu(self): pass

    def edit_character(self): pass
