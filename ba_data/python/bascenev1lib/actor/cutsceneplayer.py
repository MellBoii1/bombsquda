"""Cutscene player."""
from typing import override, Any
from bascenev1lib.actor.background import Background
import bascenev1 as bs

class CutscenePlayer(bs.Actor):
    def __init__(
        self, 
        cutscene_id: int, 
        frame_times: list[float],
        end_time: float,
        fade_duration: float = 1.0,
    ):
        super().__init__()
        self._cutscene_id = cutscene_id
        self._stopped = False
        self._timers = []
        self._frame_times = frame_times
        self.fade_duration = fade_duration
        self.bgimage = bs.newnode(
            'image',
            delegate=self,
            attrs={
                'fill_screen': True,
                'texture': bs.gettexture('bg'),
                'color': (0, 0.6, 0),
                'opacity': 1.0
            }
        )
        self.node = bs.newnode(
            'image',
            delegate=self,
            attrs={
                'absolute_scale': True,
                'position': (0, 0),
                'scale': (1000, 500),
                'opacity': 1.0
            }
        )
        self.border_node = bs.newnode(
            'image',
            delegate=self,
            attrs={
                'absolute_scale': True,
                'position': (0, 0),
                'scale': (1000, 500),
                'opacity': 1.0,
                'texture': bs.gettexture('cutscene_border'),
            }
        )
        frame = 1
        self._show_frame(frame)
        frame += 1
        for delay in frame_times:
            timer = bs.Timer(
                delay,
                bs.Call(self._show_frame, frame)
            )
            frame += 1
            self._timers.append(timer)
        timer = bs.Timer(end_time, self._fade_out)
        self._timers.append(timer)
        

    def _show_frame(self, frame_number: int):
        texture_name = f"cutscene{self._cutscene_id}frame{frame_number}"
        tex = bs.gettexture(texture_name)
        self.node.texture = tex

    def _fade_out(self):
        if self.bgimage:
            bs.animate(
                self.bgimage, 
                'opacity',
                {
                    0: 1.0, 
                    self.fade_duration: 0.0
                }
            )
        if self.node:
            bs.animate(
                self.node, 
                'opacity',
                {
                    0: 1.0, 
                    self.fade_duration: 0.0
                }
            )
        if self.border_node:
            bs.animate(
                self.border_node, 
                'opacity',
                {
                    0: 1.0, 
                    self.fade_duration: 0.0
                }
            )

    def stop(self):
        self._stopped = True
        if self.node:
            self.node.delete()
        if self.bgimage:
            self.bgimage.delete()
        if self.border_node:
            self.border_node.delete()
        self._timers.clear()
    
    def handlemessage(self, msg: Any):
        if isinstance(msg, bs.DieMessage):
            self.stop()
        else:
            return super().handlemessage(msg)
        return None
    
    @override
    def exists(self):
        return bool(self.node)

