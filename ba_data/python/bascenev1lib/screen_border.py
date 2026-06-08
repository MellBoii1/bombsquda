import bascenev1 as bs

class ScreenBorder:
    def __init__(self):
        return # for now, just remove it
        cget = bs.app.config.get
        res = cget('squda_border_res')
        self.frame_count = 3
        self.prefix = 'fancy_border'
        self._current_frame = 0
        self.node = bs.newnode('image',
            attrs={
                'scale': (res[0], res[1]),
                'texture': bs.gettexture(f'{self.prefix}1'),
                'front': True,
                'host_only': True,
            }
        )
        delay = 0.1
        self.tickTimer = bs.BaseTimer(delay, self.frame_tick, repeat=True)
        
    def frame_tick(self):
        if not self.node:
            return
        self._current_frame += 1
        if self._current_frame > self.frame_count:
            self._current_frame = 1
        self.node.texture = bs.gettexture(f'{self.prefix}{self._current_frame}')
    
    def refresh_size(self):
        cget = bs.app.config.get
        res = cget('squda_border_res')
        self.node.scale = (res[0], res[1])
        