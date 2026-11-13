import asyncio
import time

# only chat works in tui with usual tool use
# tui is intended mainly for quick testing purposes
# it's plain boring and minimal for the same purpose

class TUI:
    def __init__(self, store, services):
        self.services = services
        self.tools = services.tools.tools
        self.store = store
        self.tool_call = None

        self.session = None

        self.title = None

        # SONORO HANDLERS
        self.on_from_user = None

        self.ext_id = None

    def start(self):
        time.sleep(1)

        if self.title is None: print('\nSONORO TUI ^_^')
        else:
            print(self.title)
            print('powered by Sonoro')

        print()

        self.services.make_client(self.store.user.get_config().model_dump())

        try:
            self.characters_menu()
        except KeyboardInterrupt: pass
        finally:
            self.services.server.should_exit = True
            return

    def characters_menu(self):
        print('=== CHARACTERS ===')
        self.select_character()
        if self.session.character:
            self.chat_loop()
            self.characters_menu()
        
    def select_character(self):
        characters = {i: name for i, name in enumerate(self.store.characters.list_characters().keys())}
        print('\n'.join([f'{i}: {name}' for i, name in characters.items()]))

        while self.session.character is None:
            try:
                i = input('\nSelect character by index: ')
                if i == 'exit': return

                i = int(i)

                if i not in characters:
                    print("Character doesn't exist\n")
                    continue

                self.session.character = characters[i]
                print(f'Selected {self.session.character}')

                char_config = self.store.characters.get_config(self.session.character)

                self.services.llm.set_character(char_config.model_dump())
            except ValueError:
                print('Invalid input. Try again.\n')
                continue
            print()
        
    def chat_loop(self):
        print(f'{self.session.character} joined the chat')

        self.responded = True
        try:
            while True:
                if not self.responded:
                    time.sleep(0.5)
                    continue

                message = input('>>> ')
                if message == 'exit': break

                data = {'type': 'text', 'content': message}

                self.responded = False

                try:
                    asyncio.run(self.on_from_user({
                        'event_name': 'user_message',
                        'content': data
                    }))
                except Exception as e:
                    print(f'[TUI Error] {e}')
                    self.responded = True

        except KeyboardInterrupt: pass
        finally:
            print(f'{self.session.character} went offline')
            self.session.character = None
            self.services.llm.save_mem()

    def to_ui(self, content):
        print(f"{self.session.character}: {content['message'] if content['message'] != '_silence' else '*Remained quiet*'}")
        self.responded = True

    async def default_from_char(self, res):
        action, content = res['action'], res['content']

        if action == 'interaction':
            self.to_ui(content)
        elif action == 'tool_call':
            await self.tool_call(content['tool'], content.get('function'), content.get('args'))
