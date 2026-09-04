class Movement:
    def __init__(self, sio):
        self.sio = sio
        self.char_conn = []
        self.char_pos = None

    def reset(self):
        self.char_conn = []
        self.char_pos = None

    async def setup(self, sid):
        self.char_conn.append(sid)
        if len(self.char_conn) == 1:
            await self.manage_char_pos(1)
        else:
            await self.manage_char_pos()

    async def remove(self, sid):
        if sid in self.char_conn: self.char_conn.remove(sid)
        await self.manage_char_pos(1, deselect=True)

    async def walk_out(self, dir):
        if dir is None: return
        dn = 1 if dir == 'right' else -1

        await self.sio.emit('walkOut', dn, to=self.char_pos)

        return {'event_name': 'walking out of the current screen to the next one', 'content': 'on the way to next screen'}

    async def manage_char_pos(self, dir=0, deselect=False):
        prev = self.char_pos
        length = len(self.char_conn)

        if not length:
            self.char_pos = None
            return

        if prev is None or prev not in self.char_conn:
            self.char_pos = self.char_conn[0]
        else:
            self.char_pos = self.char_conn[(self.char_conn.index(prev) + dir) % length]

        new = self.char_pos

        # print(self.char_conn, prev, new)

        if prev == new and length != 1: return
        if dir or deselect: await self.sio.emit('walkIn', dir, to=new)
