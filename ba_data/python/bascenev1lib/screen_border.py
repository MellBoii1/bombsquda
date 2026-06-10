import bascenev1 as bs
STYLES = {
    'fancy': ('fancy_border', 3),
    'fancy_logo': ('fancy_border_logo', 3),
    'fancy_dark': ('fancy_border_dark', 3),
    'basic': ('basic_border', 1),
}
    

class ScreenBorder:
    def __init__(self):
        cget = bs.app.config.get
        res = cget('squda_border_res')
        style = cget('squda_border_style')
        self.prefix, self.frame_count = STYLES[style]
        self._current_frame = 1
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
    
    def set_style(self, style):
        self.prefix, self.frame_count = STYLES[style]
        self.frame_tick()
    
    def delete(self):
        if self.node:
            self.node.delete()
        self.tickTimer = None
        