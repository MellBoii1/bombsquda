# Define a cutscene player we can use for coop levels.
import bascenev1 as bs

class CutscenePlayer:
    def __init__(self, cutscene_id: int, frame_delays: list[float],
                 fade_duration: float = 1.0):
        """
        Plays a cutscene frame-by-frame with individual delays.

        cutscene_id: number used in texture names "cutsceneXframeY"
        frame_delays: list of delays per frame, e.g. [2.0, 1.5, 3.0]
        fade_duration: fade-out time after the last frame
        """
        self.cutscene_id = cutscene_id
        self._stopped = False
        self.frame_delays = frame_delays
        self.fade_duration = fade_duration
        self.bgimage = bs.newnode('image', attrs={
            'texture': bs.gettexture('bg'),
            'absolute_scale': True,
            'position': (0, 0),
            'fill_screen': True,
            'opacity': 1.0,
            'color': (1, 1, 1)
        })
        self.node = None
        self._show_frame(1)
    def _show_frame(self, frame_number: int):
        if self._stopped == True:
            return
        if frame_number > len(self.frame_delays):
            self._fade_out()
            return

        # Texture name example: "cutscene1frame2"
        texture_name = f"cutscene{self.cutscene_id}frame{frame_number}"
        tex = bs.gettexture(texture_name)

        # Delete last frame before showing new one
        if self.node:
            self.node.delete()
        
        # Show the new frame
        self.node = bs.newnode('image', attrs={
            'texture': tex,
            'absolute_scale': True,
            'position': (0, 0),
            'scale': (1000, 720),
            'opacity': 1.0
        })

        # Schedule the next frame using FRAME-SPECIFIC delay
        delay = self.frame_delays[frame_number - 1]
        bs.timer(delay, lambda: self._show_frame(frame_number + 1))

    def _fade_out(self):
        if self.bgimage:
            bs.animate(self.bgimage, 'opacity',
                       {0: 1.0, self.fade_duration: 0.0})
            bs.timer(self.fade_duration + 0.05, self.bgimage.delete)

        if self.node:
            bs.animate(self.node, 'opacity',
                       {0: 1.0, self.fade_duration: 0.0})
            bs.timer(self.fade_duration + 0.06, self.node.delete)
    def stop(self):
        self._stopped = True
        if hasattr(self, 'node') and self.node:
            self.node.delete()
        if hasattr(self, 'bgimage') and self.bgimage:
            self.bgimage.delete()
            
class CutscenePlayerSpecialEditionCuzFucked:
    def __init__(self, cutscene_id: int, frame_delays: list[float],
                 fade_duration: float = 1.0):
        """
        Plays a cutscene frame-by-frame with individual delays.

        cutscene_id: number used in texture names "cutsceneXframeY"
        frame_delays: list of delays per frame, e.g. [2.0, 1.5, 3.0]
        fade_duration: fade-out time after the last frame
        """
        self.cutscene_id = cutscene_id
        self._stopped = False
        self.frame_delays = frame_delays
        self.fade_duration = fade_duration
        self.node = None
        self._show_frame(1)

    def _show_frame(self, frame_number: int):
        if self._stopped == True:
            return
        if frame_number > len(self.frame_delays):
            self._fade_out()
            return

        # Texture name example: "cutscene1frame2"
        texture_name = f"cutscene{self.cutscene_id}frame{frame_number}"
        tex = bs.gettexture(texture_name)

        # Delete last frame before showing new one
        if self.node:
            self.node.delete()
        
        # Show the new frame
        self.node = bs.newnode('image', attrs={
            'texture': tex,
            'absolute_scale': True,
            'position': (0, 0),
            'fill_screen': True,
            'opacity': 1.0
        })

        # Schedule the next frame using FRAME-SPECIFIC delay
        delay = self.frame_delays[frame_number - 1]
        bs.timer(delay, lambda: self._show_frame(frame_number + 1))

    def _fade_out(self):
        if self.node:
            bs.animate(self.node, 'opacity',
                       {0: 1.0, self.fade_duration: 0.0})
            bs.timer(self.fade_duration + 0.06, self.node.delete)
    def stop(self):
        self._stopped = True
        if hasattr(self, 'node') and self.node:
            self.node.delete()
        if hasattr(self, 'bgimage') and self.bgimage:
            self.bgimage.delete()

