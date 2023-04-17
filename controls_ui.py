import pygame as pg
import random


pg.init()

screen_size = (800, 800)

screen = pg.display.set_mode(screen_size)

running = True
font_small = pg.font.SysFont('arialblack', 15, italic=False, bold=False)

user_input_active = False


def blend(c1, c2):
    c3 = [
        (c1[0] + c2[0]) // 2,
        (c1[1] + c2[1]) // 2,
        (c1[2] + c2[2]) // 2
    ]
    return c3


class Range:
    def __init__(self, start: list[int], end: list[int] = None):
        assert all([0 <= c <= 255 for c in start])
        if end is not None:
            assert all([0 <= c <= 255 for c in end])

        self.start, self.end = start, end if end is not None else start
        self.coverage = [self.end[i] - self.start[i] for i in range(3)]

    def at(self, p: float = 0.0):
        assert 0.0 <= p <= 1.0
        return [int(self.start[i] + self.coverage[i] * p) for i in range(3)]

    def random(self):
        return [int(random.random() * self.coverage[i] + self.start[i]) for i in range(3)]


class Clickable:
    def __init__(self, _rect, _color, on_click, on_hover=None, _camo=False):
        self.on_click = on_click
        self.on_hover = on_hover

        self._surf = pg.Surface((_rect[2], _rect[3]))
        self._rect = pg.Rect(_rect[0], _rect[1], _rect[2], _rect[3])

        self.pressed = False
        self.hovered = False

        self._color = _color
        self._camo = _camo

        if self._camo:
            self._surf.set_alpha(0)

    def process(self):
        mouse_pos = pg.mouse.get_pos()

        self._surf.fill(self._color)
        if self._rect.collidepoint(mouse_pos):
            self._surf.fill(blend(self._color, [120, 120, 120]))
            if self._camo:
                self._surf.set_alpha(75)
            if self.on_hover is not None:
                self.on_hover(self._rect)
            if pg.mouse.get_pressed(num_buttons=3)[0]:
                self._surf.fill(blend(self._color, [60, 60, 60]))
                if not self.pressed:
                    self.on_click()
                    self.pressed = True
            else:
                self.pressed = False
        else:
            if self._camo:
                self._surf.set_alpha(0)
        self.update()

    def update(self):
        screen.blit(self._surf, self._rect)


class ClickableCamo(Clickable):
    def __init__(self, _rect: tuple, on_click, on_hover):
        Clickable.__init__(self, _rect, [135, 135, 135], on_click, on_hover, True)

    def update(self):
        Clickable.update(self)


class Button(Clickable):
    def __init__(self, _rect, text, _color, on_click, on_hover=None, _camo=False):
        Clickable.__init__(self, _rect, _color, on_click, on_hover, _camo)
        self.__surf = font_small.render(text, True, (20, 20, 20))

    def update(self):
        self._surf.blit(self.__surf, [
            self._rect.width / 2 - self.__surf.get_rect().width / 2,
            self._rect.height / 2 - self.__surf.get_rect().height / 2
        ])
        pg.draw.rect(screen, [0, 0, 0], (self._rect.x - 5, self._rect.y - 5, self._rect.w + 10, self._rect.h + 10))
        Clickable.update(self)


class InputField(Clickable):
    def __init__(self, _rect, _color, on_click, on_hover=None, _camo=False):
        self.u_input = ""


def on_click_func():
    print(f'clicked!')


def on_hover_func(_rect):
    pg.draw.rect(screen, [0, 255, 0], (100, 400, 100, 100))


button = Button((300, 100, 100, 25), "hello", [160, 120, 90], on_click_func)
camo = ClickableCamo((100, 200, 100, 100), on_click=on_click_func, on_hover=on_hover_func)
input_field = InputField((300, 200, 200, 25), [0, 0, 0], on_click_func)

while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

    screen.fill([100, 100, 200])

    camo.process()
    button.process()

    pg.display.update()

pg.quit()
