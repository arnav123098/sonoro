from tools.web_search import WebSearch
from tools.music_player import MusicPlayer

import inspect

class Tools:
    def __init__(self):
        self.tools = {
            'web_search': WebSearch(),
            'music_player': MusicPlayer()
        }

    async def call(self, tool_name, function, args):
        tool_obj = self.tools.get(tool_name)
        if tool_obj is not None:
            fn = getattr(tool_obj, function, None)
        else:
            fn = None

        if fn is not None:
            tool_call_res = fn(**args)
        else:
            print(f'tool call {tool_name}.{function}({args}) is invalid')
            return

        if inspect.isawaitable(tool_call_res): tool_call_res = await tool_call_res

        return tool_call_res

    def make_tool(self, name, obj):
        self.tools[name] = obj

    def make_client(self, config):
        for tool in self.tools.values():
            if hasattr(tool, 'make_client'):
                tool.make_client(config)

    def cleanup(self):
        for tool in self.tools.values():
            if hasattr(tool, 'cleanup'):
                tool.cleanup()
