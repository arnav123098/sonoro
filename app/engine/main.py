from sonoro import Sonoro
import asyncio

sonoro = Sonoro('../../')
sonoro.set_default_services()

ui = {
    1: 'tui',
    2: 'webui'
}
print('\n'.join([f'{i}. {u}' for i, u in ui.items()]))

ui_type = ui.get(int(input('Interface type: ')))

sonoro.make_interface(ui_type)
sonoro.set_default_handlers()

try:
    asyncio.run(sonoro.start())
except KeyboardInterrupt: pass
finally:
    sonoro.cleanup()
