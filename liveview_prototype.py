from __future__ import annotations

from dataclasses import dataclass
import pygame as pg
from enum import Enum
import random

pg.init()

_env_screen_size = (800, 800)
stat_screen_size = (400, 800)
screen_size = (_env_screen_size[0] + stat_screen_size[0], _env_screen_size[1])

screen = pg.display.set_mode(screen_size)
pg.display.set_caption("Visualization")

font_large = pg.font.SysFont('arialblack', 30, italic=False, bold=False)
font_med = pg.font.SysFont('arialblack', 22, italic=False, bold=False)
font_small = pg.font.SysFont('arialblack', 15, italic=False, bold=False)

running = True


class Color:
    def __init__(self, start: list[int], end: list[int] = None):
        assert all([0 <= c <= 255 for c in start])
        if end is not None:
            assert all([0 <= c <= 255 for c in end])

        self.start, self.end = start, end if end is not None else start
        self.coverage = [self.end[i] - self.start[i] for i in range(3)]

    def color(self, p: float = 0.0):
        assert 0.0 <= p <= 1.0
        return [int(self.start[i] + self.coverage[i] * p) for i in range(3)]

    def random(self):
        return [int(random.random() * self.coverage[i] + self.start[i]) for i in range(3)]


class COLORS:
    BLACK = Color([0, 0, 0])
    GRAY = Color([150, 150, 150])
    DGRAY = Color([75, 75, 75])
    WHITE = Color([255, 255, 255])
    RED = Color([255, 0, 0])
    GREEN = Color([0, 255, 0])
    BLUE = Color([0, 0, 255])
    BROWN = Color([150, 75, 0])
    LBLUE = Color([50, 190, 240])
    PURPLE = Color([160, 35, 230])
    PINK = Color([240, 100, 170])

    BW = Color([0, 0, 0], [255, 255, 255])
    FEATURED = Color([random.randrange(0, 256) for _ in range(3)], [random.randrange(0, 256) for _ in range(3)])

    OTHER = {}

    @staticmethod
    def random(_range=False):
        return Color([random.randrange(0, 256) for _ in range(3)],
                     None if not _range else [random.randrange(0, 256) for _ in range(3)])

    @staticmethod
    def new(name, start, end=None):
        COLORS.OTHER[name] = Color(start, end)


class Environment:
    z_across, z_down = 4, 8
    border_width = 5
    z_width, z_height = _env_screen_size[0] // z_across, _env_screen_size[1] // z_down
    z_count = z_across * z_down

    border_color = COLORS.BLACK
    borders = []
    for zd in range(1, z_across + 1):
        borders.append(((zd * z_width, 0), (zd * z_width, _env_screen_size[1])))
    for za in range(1, z_down):
        borders.append(((0, za * z_height), (_env_screen_size[0], za * z_height)))

    default_resolution = 5
    default_count = (z_height * z_width) // (default_resolution * default_resolution)
    default_color = COLORS.BLACK


class Helper:
    @staticmethod
    def clamp(n, small, large):
        return max(small, min(n, large))

    @staticmethod
    def zid_to_coords(env, zid, _screen: bool = False):
        if _screen:
            _coords = Helper.zid_to_coords(env, zid, False)
            return _coords[0] * env.z_width, _coords[1] * env.z_height
        return zid % env.z_across, zid // env.z_across

    @staticmethod
    def coords_to_zid(env, coords):
        return coords[0] // env.z_width, coords[1] // env.z_height


@dataclass
class Variable:
    data: tuple = (0, 0, 0, 0)
    color: float = 0.0


@dataclass
class MyGroundTileClass(Variable):
    value: float = 0.0


@dataclass
class MyIndividualTileClass(Variable):
    value: float = 0.0


@dataclass
class ZoneVarsPool:
    id: int
    resolution: int | list[int]
    name: str
    vars: list[Variable]  # need variable class reference and necessary parameters
    count: int = Environment.default_count  # need total number of vars, -1 for fill zone, n for n
    base_color: Color = COLORS.BW  # need color for all variable rects
    draw_border: bool = True


@dataclass
class Zone:
    id: int
    top_left: tuple[int, int]
    pool: list[ZoneVarsPool]


@dataclass
class ZonePool:
    zones: list[Zone]

    def get(self, _id):
        for zone in self.zones:
            if zone.id == _id:
                return zone
        return None


class _StatesIterable:
    def __init__(self, _states):
        self._states = _states
        self._count = len(self._states)
        self.i = 0

    def __next__(self):
        if self.i < self._count:
            _state = self._states[self.i]
            self.i += 1
            return _state
        raise StopIteration


class _States:
    def __init__(self, _states: list[str], env):
        self._states = {_state: ZonePool([Zone(id=i, top_left=(Helper.zid_to_coords(env, i, True)), pool=[]) for i in range(Environment.z_count)]) for _state in _states}
        self.env = env

    def __iter__(self):
        return _StatesIterable(list(self._states))

    def __getitem__(self, item):
        if isinstance(item, int):
            return list(self._states.values())[item]
        elif isinstance(item, str):
            return self._states[item]

    def __str__(self):
        istate = 0
        nzones, nvarpools, nvars = 0, 0, 0
        _s_header = f"\n====================================================================\n" \
                    f"There are {len(self._states)} states:\n" \
                    f"====================================================================\n" \
                    f"\n"
        ___s, __s = '', ''
        for _state, zpool in self._states.items():
            ___s += '\n{\n\n'
            for _zone in zpool.zones:
                nzones += 1
                ___s += f'\t[ZONE {_zone.id}]   =>   TL: {_zone.top_left}   =>   Length: {len(_zone.pool)}\n'
                for vpool in _zone.pool:
                    nvarpools += 1
                    ___s += f'\t\t[VARS POOL {vpool.id}]   =>   Name: {vpool.name}   =>   Resolution: {vpool.resolution}   =>   => Base Color: {vpool.base_color.color()}   =>   Length: {len(vpool.vars)}\n'
                    for i, _var in enumerate(vpool.vars):
                        nvars += 1
                        ___s += f'\t\t\t[VAR {i}]   =>   Type: {type(_var).__name__}   =>   Color: {_var.color} | {vpool.base_color.color(_var.color)}   =>   Data: {_var.data}   =>   Full: {_var}\n'
            ___s += '\n}\n\n'
            ___s += '====================================================================\n\n'
            __s += f"[STATE {istate}: {_state}]   =>   Length: {len(zpool.zones)}\n[TOTAL STATE COUNTS]   =>   Zones: {nzones}   =>   VarPools: {nvarpools}   =>   Vars: {nvars}\n" + ___s
            ___s = ''
            istate += 1
        return _s_header + __s

    def _add(self, name: str, env, override=False, catch=True):
        try:
            # Try to access state to see if it exists
            _ = self[name]
            if not override:
                # it exists -> do not override it
                if catch:
                    # it exists -> throw an exception
                    raise Exception(f"Cannot create new state '{name}'. This state already exists.")
                # it exists -> do not throw an exception, return None
                return
            else:
                # it exists -> override it
                print(f"[NOTICE]   =>   Overriding state {name}.")
        except KeyError:
            # it does not exist -> create it in default manner
            pass

        self._states[name] = ZonePool([Zone(id=i, top_left=(Helper.zid_to_coords(self.env, i, _screen=True)), pool=[]) for i in range(Environment.z_count)])

    def generate(self, state: str, _vars: list, _counts: list[int], _colors: list[Color] = None,
                 _resolutions: list[int | list[int]] = None, _zones: list[int] = None, zone_override=False,
                 state_override=False):
        """
        Generates ZoneVarsPool objects for zones for some state.
        :param state: state name
        :param _vars: The variable objects to use for each ZVP
        :param _counts: The number of tiles to create. -1 for max num of tiles that can fit in zone.
        :param _colors: The color for each tile in a ZVP. None for default env color
        :param _resolutions: The resolution for each tile in a ZVP
        :param _zones: The zones to generate ZoneVarsPool objects in. None for all zones. Positive integers for zones to include, negative integers for zones to disclude.
        :param zone_override: Override existing ZoneVarsPool objects for this state
        :param state_override: Override state if it exists already
        :return: None
        # state: ZonePool   =>   ZonePool: list[Zone]   =>   Zone: list[ZoneVarsPool]   =>   ZoneVarsPool: list[Variable]   =>   Variable: ...
        """
        assert len(_vars) == len(_counts) == (len(_colors) if _colors is not None else len(_vars)) == (
            len(_resolutions) if _resolutions is not None else len(_vars))
        assert 0 <= len(_zones) if _zones is not None else 0 <= self.env.z_count

        self._add(state, self.env, state_override, catch=False)

        zp = self[state]
        for zi in (_zones if _zones is not None else [_ for _ in range(self.env.z_count)]):
            zone = zp.get(zi)
            if zone_override:
                zone.pool = []
            for i in range(len(_vars)):
                color = _colors[i] if _colors is not None else self.env.default_color

                resolution = []
                if _resolutions is None:
                    resolution = [
                        self.env.default_resolution if _counts[
                                                           i] != -1 else self.env.z_width // self.env.default_resolution,
                        self.env.default_resolution if _counts[
                                                           i] != -1 else self.env.z_height // self.env.default_resolution]
                else:
                    if isinstance(_resolutions[i], int):  # same in both dimensions
                        resolution = [_resolutions[i] if _counts[i] != -1 else self.env.z_width // _resolutions[i],
                                      _resolutions[i] if _counts[i] != -1 else self.env.z_height // _resolutions[i]]
                    elif isinstance(_resolutions[i], list):  # different w and h dimensions
                        assert len(_resolutions[i]) == 2
                        resolution = [
                            _resolutions[i][0] if _counts[i] != -1 else self.env.z_width // _resolutions[i][0],
                            _resolutions[i][1] if _counts[i] != -1 else self.env.z_height // _resolutions[i][1]
                        ]

                count = _counts[i] if _counts[i] != -1 else (self.env.z_width * self.env.z_height) // (
                            resolution[0] * resolution[1])

                zvp = ZoneVarsPool(id=len(zone.pool), resolution=resolution, name=_vars[i].__name__, vars=[],
                                   count=count, base_color=color)
                m_across = self.env.z_width // resolution[0]
                for c in range(count):
                    _var = _vars[i]
                    zvp.vars.append(_var(
                        (
                            zone.top_left[0] + (c % m_across) * resolution[0],  # top
                            zone.top_left[1] + (c // m_across) * resolution[1],  # left
                            zvp.resolution[0],  # width
                            zvp.resolution[1]  # height
                        )
                    ))
                zone.pool.append(zvp)


States = _States(['aerial', 'ground'], Environment)


class Simulation:
    def __init__(self):
        self.restrictions = {}
        self.UI = {'buttons': []}

    @staticmethod
    def draw_state(state, restrictions: dict = None):
        for z in States[state].zones:
            for zvp in z.pool:
                for var in zvp.vars:
                    # restrictions
                    if restrictions is not None:
                        if 'zoom' in restrictions:
                            pass

                    pg.draw.rect(screen, zvp.base_color.color(var.color), var.data)
                    if zvp.draw_border:
                        pg.draw.line(screen, COLORS.BLACK.color(), (var.data[0], var.data[1]), (var.data[0] + var.data[2], var.data[1]))  # top
                        pg.draw.line(screen, COLORS.BLACK.color(), (var.data[0], var.data[1]), (var.data[0], var.data[1] + var.data[3]))  # left
                        pg.draw.line(screen, COLORS.BLACK.color(), (var.data[0], var.data[1] + var.data[3]), (var.data[0] + var.data[2], var.data[1] + var.data[3]))  # bot
                        pg.draw.line(screen, COLORS.BLACK.color(), (var.data[0] + var.data[2], var.data[1]), (var.data[0] + var.data[2], var.data[1] + var.data[3]))  # right

    @staticmethod
    def draw_tile_borders(state):
        for z in States[state].zones:
            for zvp in z.pool:
                zvp.draw_border = not zvp.draw_border

    @staticmethod
    def draw_borders():
        for line_data in States.env.borders:
            pg.draw.line(screen, States.env.border_color.color(), start_pos=line_data[0], end_pos=line_data[1],
                         width=States.env.border_width)

    @staticmethod
    def draw_grid(every: int = 50, color: Color = COLORS.BLUE, width=1):
        for down in range(_env_screen_size[1] // every + 1):
            pg.draw.line(screen, color.color(), (0, down * every), (_env_screen_size[0], down * every), width)
        for across in range(_env_screen_size[0] // every + 1):
            pg.draw.line(screen, color.color(), (across * every, 0), (across * every, _env_screen_size[1]), width)

    @staticmethod
    def foo():
        print('button pressed... Hello!')

    @staticmethod
    def generate_UI():
        button = Button(850, 150, 100, 30, "Hello", font_small, Simulation.foo)
        Simulation.UI['buttons'].append(button)


# class Button:
#     def __init__(self, x, y, w, h, text, font, on_click, _color=Color([255, 255, 255], [120, 120, 120])):
#         self.x, self.y = x, y
#         self.w, self.h = w, h
#
#         self.on_click = on_click
#         self._color = _color
#
#         self._surf = pg.Surface((self.w, self.h))
#         self._rect = pg.Rect(self.x, self.y, self.w, self.h)
#         self._bsurf = font.render(text, True, _color.color(1))
#
#         self.is_pressed = False
#
#     def process(self):
#         mpos = pg.mouse.get_pos()
#         self._surf.fill(self._color.color())
#         if self._rect.collidepoint(mpos):
#             self._surf.fill(self._color.color(.5))
#             if pg.mouse.get_pressed()[0]:
#                 self._bsurf.fill(self._color.color(1.0))
#                 if not self.is_pressed:
#                     self.on_click()
#                 self.is_pressed = True
#             else:
#                 self.is_pressed = False
#         self._surf.blit(self._bsurf, [
#             self._rect.width/2 - self._bsurf.get_rect().width / 2,
#             self._rect.height/2 - self._bsurf.get_rect().height / 2
#         ])
#
#         screen.blit(self._surf, self._rect)
#

class Button:
    def __init__(self, x, y, width, height, buttonText, onclickFunction, _color=Color([255, 255, 255], [120, 120, 120])):
        self.x = x
        self.y = y
        self.w = width
        self.h = height
        self.on_click = onclickFunction

        self.buttonSurface = pg.Surface((self.w, self.h))
        self.buttonRect = pg.Rect(self.x, self.y, self.w, self.h)
        self.buttonSurf = font_small.render(buttonText, True, (20, 20, 20))

        self.pressed = False
        self._color = _color

    def process(self):

        mousePos = pg.mouse.get_pos()

        self.buttonSurface.fill(self._color.color())
        if self.buttonRect.collidepoint(mousePos):
            self.buttonSurface.fill(self._color.color(.5))
            if pg.mouse.get_pressed(num_buttons=3)[0]:
                self.buttonSurface.fill(self._color.color(1.0))
                if not self.pressed:
                    self.on_click()
                    self.pressed = True
            else:
                self.pressed = False

        self.buttonSurface.blit(self.buttonSurf, [
            self.buttonRect.width/2 - self.buttonSurf.get_rect().width/2,
            self.buttonRect.height/2 - self.buttonSurf.get_rect().height/2
        ])
        screen.blit(self.buttonSurface, self.buttonRect)


States.generate(state='aerial', _vars=[MyGroundTileClass, MyIndividualTileClass], _counts=[-1, 5],
                _colors=[Color([0, 0, 0], [255, 255, 255]), COLORS.PURPLE], _resolutions=[[4, 5], [25, 15]])
States.generate(state='ground', _vars=[MyGroundTileClass, MyIndividualTileClass], _counts=[3, 1],
                _colors=[COLORS.LBLUE, COLORS.PINK], _resolutions=[[20, 20], 15])

print(States)

_s = 'ground'

button = Button(900, 200, 100, 50, "Hello!", Simulation.foo)


while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_1:
                _s = 'aerial'
            elif event.key == pg.K_2:
                _s = 'ground'
            print(_s)

    screen.fill(COLORS.WHITE.color())

    Simulation.draw_state(_s)
    Simulation.draw_borders()

    # tick markings for y coordinates
    for _y in range(0, _env_screen_size[1], 50):
        img = font_small.render(str(_y), True, COLORS.BLACK.color())
        screen.blit(img, (_env_screen_size[0] + 20, _y))
        pg.draw.line(screen, COLORS.BLACK.color(), (_env_screen_size[0], _y), (_env_screen_size[0] + 15, _y))

    button.process()
    pg.display.update()
