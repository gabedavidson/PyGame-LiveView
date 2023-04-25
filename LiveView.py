from __future__ import annotations

from dataclasses import dataclass

# from PygameStuff.controls_ui import Button, ClickableCamo

import pygame as pg
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
    def __init__(self, default_zones_across: int = 5, default_zones_down: int = 5, border_width: int = 3,
                 border_color: Color = COLORS.BLACK, default_resolution: int = 5, default_color: Color = COLORS.BLACK):
        self.default_zones_across, self.default_zones_down = default_zones_across, default_zones_down
        self.active_zones_across = self.default_zones_across
        self.active_zones_down = self.default_zones_down
        self.zoom_inset = [0, 0]
        self.border_width = border_width
        self.zone_width, self.zone_height = _env_screen_size[0] // self.active_zones_across, _env_screen_size[1] // self.active_zones_down
        self.zone_count = self.default_zones_across * self.default_zones_down

        self.border_color = border_color
        self.borders = []

        self.default_resolution = default_resolution
        self.default_count = (self.zone_height * self.zone_width) // (self.default_resolution * self.default_resolution)
        self.default_color = default_color

    def compile_env_borders(self):
        self.borders = []
        for zd in range(1, self.active_zones_across + 1):
            self.borders.append(((zd * self.zone_width, 0), (zd * self.zone_width, _env_screen_size[1])))
        for za in range(1, self.active_zones_down):
            self.borders.append(((0, za * self.zone_height), (_env_screen_size[0], za * self.zone_height)))

    def change_env_dimensions(self, active_zones_across_inset=0, active_zones_down_inset=0, active_zones_across=-1, active_zones_down=-1):
        # assert 0 < active_zones_across <= self.default_zones_across and 0 < active_zones_down if active_zones_down != -1 else self.default_zones_down <= self.default_zones_down
        _aza = active_zones_across if active_zones_across != -1 else self.default_zones_across
        _azd = active_zones_down if active_zones_down != -1 else self.default_zones_down

        self.active_zones_across = _aza if self.default_zones_across - active_zones_across_inset >= _aza else self.default_zones_across - active_zones_across_inset
        self.active_zones_down = _azd if self.default_zones_down - active_zones_down_inset >= _azd else self.default_zones_down - active_zones_down_inset
        self.zone_width = _env_screen_size[0] // self.active_zones_across
        self.zone_height = _env_screen_size[1] // self.active_zones_down

        self.compile_env_borders()
        self.zoom_inset = [active_zones_across_inset, active_zones_down_inset]


class Helper:
    @staticmethod
    def clamp(n: int | float, small: int | float, large: int | float):
        return max(small, min(n, large))

    @staticmethod
    def zid_to_coords(env: Environment, zid: int, _screen_coords: bool = False):
        if _screen_coords:
            _coords = Helper.zid_to_coords(env, zid, False)
            return _coords[0] * env.zone_width, _coords[1] * env.zone_height
        return zid % env.default_zones_across, zid // env.default_zones_across

    @staticmethod
    def zcoords_to_zid(env: Environment, coords: list[int]):
        return coords[0] % env.default_zones_across + coords[1] * env.default_zones_across

    @staticmethod
    def coords_to_zid(env: Environment, coords: list[int]):
        return coords[0] // env.zone_width, coords[1] // env.zone_height


@dataclass
class Variable:
    data: list[int]
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
    count: int  # need total number of vars, -1 for fill zone, n for n
    base_color: Color = COLORS.BW  # need color for all variable rects
    draw_border: bool = True


@dataclass
class Zone:
    id: int
    top_left: tuple[int, int]
    pool: list[ZoneVarsPool]
    active: bool = True  # should this zone relay content? only applies if this zone is included in the environment


@dataclass
class StateZonePool:
    zones: list[Zone]
    env: Environment
    active_zones: list[int] = None
    active: bool = True

    def get(self, _id):
        for zone in self.zones:
            if zone.id == _id:
                return zone
        return None

    def resize_tiles(self):
        ratio_x, ratio_y = self.env.default_zones_across / self.env.active_zones_across, self.env.default_zones_down / self.env.active_zones_down
        for zone in self.zones:
            for zvp in zone.pool:
                for var in zvp.vars:
                    var.data[2] = var.data[2] * ratio_x
                    var.data[3] = var.data[3] * ratio_y

    def reposition_tiles(self):
        zids_in_order = []
        for i, zone in enumerate(self.zones):
            ...


clickables = []


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
    def __init__(self, _states: list[str], env: Environment | list[Environment]):
        self.states = {_state: StateZonePool([Zone(id=i, top_left=(Helper.zid_to_coords(env[_i] if isinstance(env, list) else env, i, True)), pool=[]) for i in range(env[_i].zone_count)], env=env[_i] if isinstance(env, list) else env) for _i, _state in enumerate(_states)}
        self.env = None

    def __iter__(self):
        return _StatesIterable(list(self.states))

    def __getitem__(self, item):
        if isinstance(item, int):
            return list(self.states.values())[item]
        elif isinstance(item, str):
            return self.states[item]

    def __str__(self):
        istate = 0
        nzones, nvarpools, nvars = 0, 0, 0
        _s_header = f"\n====================================================================\n" \
                    f"There are {len(self.states)} states: {' | '.join([_state + f' ({i})' for i, _state in enumerate(self.states)])}\n" \
                    f"====================================================================\n" \
                    f"\n"
        ___s, __s = '', ''
        for _state, zpool in self.states.items():
            ___s += '\n{\n\n'
            for _zone in zpool.zones:
                nzones += 1
                ___s += f'\t[ZONE {_zone.id}]   =>   TL: {_zone.top_left}   =>   Length: {len(_zone.pool)}\n'
                for vpool in _zone.pool:
                    nvarpools += 1
                    ___s += f'\t\t[VARS POOL {vpool.id}]   =>   Name: {vpool.name}Vars   =>   Resolution: {vpool.resolution}   =>   => Base Color: {vpool.base_color.color()}   =>   Length: {len(vpool.vars)}\n'
                    for i, _var in enumerate(vpool.vars):
                        nvars += 1
                        ___s += f'\t\t\t[VAR {i}]   =>   Type: {type(_var).__name__}   =>   Color: {_var.color} | {vpool.base_color.color(_var.color)}   =>   Data: {_var.data}   =>   Full: {_var}\n'
            ___s += '\n}\n\n'
            ___s += '====================================================================\n\n'
            __s += f"[STATE {istate}: {_state}]   =>   Length: {len(zpool.zones)}\n[TOTAL STATE COUNTS]   =>   Zones: {nzones}   =>   VarPools: {nvarpools}   =>   Vars: {nvars}\n" + ___s
            ___s = ''
            istate += 1
        return _s_header + __s

    def _add(self, name: str, env: Environment, override=False, catch=True):
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

        self.states[name] = StateZonePool([Zone(id=i, top_left=(Helper.zid_to_coords(self.env, i, _screen_coords=True)), pool=[]) for i in range(self.env.zone_count)], env)

    def generate(self, state: str, _vars: list, _counts: list[int], _colors: list[Color] = None,
                 _resolutions: list[int | list[int]] = None, _zones: list[int] = None, zone_override=False,
                 state_override=False, _clickable=True):
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
        :param _clickable: Make tiles clickable/hover-able
        :return: None
        # state: StateZonePool   =>   StateZonePool: list[Zone]   =>   Zone: list[ZoneVarsPool]   =>   ZoneVarsPool: list[Variable]   =>   Variable: ...
        """
        assert len(_vars) == len(_counts) == (len(_colors) if _colors is not None else len(_vars)) == (
            len(_resolutions) if _resolutions is not None else len(_vars))

        zp = self[state]

        assert 0 <= len(_zones) if _zones is not None else 0 <= zp.env.zone_count

        self._add(state, zp.env, state_override, catch=False)
        zp.env.compile_env_borders()

        for zi in (_zones if _zones is not None else [_ for _ in range(zp.env.zone_count)]):
            if not 0 <= zi < zp.env.zone_count:
                continue
            zone = zp.get(zi)
            if zone_override:
                zone.pool = []
            for i in range(len(_vars)):
                color = _colors[i] if _colors is not None else zp.env.default_color

                resolution = []
                if _resolutions is None:
                    resolution = [
                        zp.env.default_resolution if _counts[
                                                           i] != -1 else zp.env.zone_width // zp.env.default_resolution,
                        zp.env.default_resolution if _counts[
                                                           i] != -1 else zp.env.zone_height // zp.env.default_resolution]
                else:
                    if isinstance(_resolutions[i], int):  # same in both dimensions
                        resolution = [_resolutions[i] if _counts[i] != -1 else zp.env.zone_width // _resolutions[i],
                                      _resolutions[i] if _counts[i] != -1 else zp.env.zone_height // _resolutions[i]]
                    elif isinstance(_resolutions[i], list):  # different w and h dimensions
                        assert len(_resolutions[i]) == 2
                        resolution = [
                            _resolutions[i][0] if _counts[i] != -1 else zp.env.zone_width // _resolutions[i][0],
                            _resolutions[i][1] if _counts[i] != -1 else zp.env.zone_height // _resolutions[i][1]
                        ]

                count = _counts[i] if _counts[i] != -1 else (zp.env.zone_width * zp.env.zone_height) // (
                            resolution[0] * resolution[1])

                zvp = ZoneVarsPool(id=len(zone.pool), resolution=resolution, name=_vars[i].__name__, vars=[],
                                   count=count, base_color=color)
                m_across = zp.env.zone_width // resolution[0]
                for c in range(count):
                    _var_t = _vars[i]
                    _var = _var_t(
                        (
                            zone.top_left[0] + (c % m_across) * resolution[0],  # left
                            zone.top_left[1] + (c // m_across) * resolution[1],  # top
                            zvp.resolution[0],  # width
                            zvp.resolution[1]  # height
                        )
                    )
                    zvp.vars.append(_var)
                    # clickables.append(ClickableCamo(_var, _var.data))
                zone.pool.append(zvp)

    def change_env_dimensions(self, x_offset, y_offset, _w, _h):
        self.env.change_env_dimensions(x_offset, y_offset, _w, _h)  # this updates zones across and down, and borders

        for i, z in enumerate(self[Simulation.curr_state].zones):
            good_across = self.env.zoom_inset[0] <= z.id % self.env.default_zones_across < min(self.env.default_zones_across, self.env.zoom_inset[0] + self.env.default_zones_across)
            good_down = self.env.zoom_inset[1] <= z.id // self.env.default_zones_across < min(self.env.default_zones_down, self.env.zoom_inset[1] + self.env.default_zones_down)

            if not (good_across and good_down):  # this zone should not be included in the updated environment
                self[Simulation.curr_state].zones.append(self[Simulation.curr_state].zones.pop(i))

        for i, z in enumerate(self[Simulation.curr_state].zones):
            good_across = self.env.zoom_inset[0] <= z.id % self.env.default_zones_across < min(self.env.default_zones_across, self.env.zoom_inset[0] + self.env.default_zones_across)
            good_down = self.env.zoom_inset[1] <= z.id // self.env.default_zones_across < min(self.env.default_zones_down, self.env.zoom_inset[1] + self.env.default_zones_down)

            if good_across and good_down:  # this zone should be included in the updated environment
                self[Simulation.curr_state].zones.append(self[Simulation.curr_state].zones.pop(i))


class Simulation:
    user_input_active = False
    curr_state = 2

    @staticmethod
    def change_state(states: _States, _id: int):
        states[Simulation.curr_state].active = False
        states[_id].active = True

        states[_id].env.compile_env_borders()

        Simulation.curr_state = _id

    @staticmethod
    def draw_state(states: _States, dynamic_sizing: bool = True, dynamic_position: bool = True):
        def _draw_tile_borders(var):
            pg.draw.line(screen, COLORS.BLACK.color(), (var.data[0], var.data[1]), (var.data[0] + var.data[2], var.data[1]))  # top
            pg.draw.line(screen, COLORS.BLACK.color(), (var.data[0], var.data[1]), (var.data[0], var.data[1] + var.data[3]))  # left
            pg.draw.line(screen, COLORS.BLACK.color(), (var.data[0], var.data[1] + var.data[3]), (var.data[0] + var.data[2], var.data[1] + var.data[3]))  # bot
            pg.draw.line(screen, COLORS.BLACK.color(), (var.data[0] + var.data[2], var.data[1]), (var.data[0] + var.data[2], var.data[1] + var.data[3]))  # right

        def _draw_tile(_color, var: Variable):
            pg.draw.rect(screen, _color.color(var.color), var.data)

        if not states[Simulation.curr_state].active:
            return

        for _a in range(states[Simulation.curr_state].env.zoom_inset[0], states[Simulation.curr_state].env.zoom_inset[0] + states[Simulation.curr_state].env.active_zones_across):  # fixme, so that this happens once when state is changed or environment is changed.
            for _d in range(states[Simulation.curr_state].env.zoom_inset[1], states[Simulation.curr_state].env.zoom_inset[1] + states[Simulation.curr_state].env.active_zones_down):
                _zone = states[Simulation.curr_state].zones[Helper.zcoords_to_zid(states[Simulation.curr_state].env, [_a, _d])]
                for zvp in _zone.pool:
                    for _var in zvp.vars:
                        _draw_tile(zvp.base_color, _var)

                        if zvp.draw_border:
                            _draw_tile_borders(_var)

    @staticmethod
    def draw_tile_borders(states: _States, state: str | int):
        for z in states[state].zones:
            for zvp in z.pool:
                zvp.draw_border = not zvp.draw_border

    @staticmethod
    def draw_env_borders(states: _States):
        for line_data in states[Simulation.curr_state].env.borders:
            pg.draw.line(screen, states[Simulation.curr_state].env.border_color.color(), start_pos=line_data[0], end_pos=line_data[1],
                         width=states[Simulation.curr_state].env.border_width)

    @staticmethod
    def draw_grid(every: int = 50, color: Color = COLORS.BLUE, width=1):
        for down in range(_env_screen_size[1] // every + 1):
            pg.draw.line(screen, color.color(), (0, down * every), (_env_screen_size[0], down * every), width)
        for across in range(_env_screen_size[0] // every + 1):
            pg.draw.line(screen, color.color(), (across * every, 0), (across * every, _env_screen_size[1]), width)

    @staticmethod
    def foo():
        print('button pressed... Hello!')


my_env_1 = Environment(border_width=5, border_color=COLORS.RED)
my_env_2 = Environment(default_zones_across=3, default_zones_down=3, border_color=COLORS.DGRAY)

states_shortcuts = {
    '1': 'aerial', '2': 'ground', '3': 'test-tube'
}
States = _States(list(states_shortcuts.values()), [my_env_1, my_env_1, my_env_2])


States.generate(state='aerial', _vars=[MyGroundTileClass, MyIndividualTileClass], _counts=[-1, 5],
                _colors=[COLORS.GREEN, COLORS.PURPLE], _resolutions=[[4, 5], [25, 15]])
States.generate(state='ground', _vars=[MyIndividualTileClass], _counts=[5],
                _colors=[COLORS.BROWN], _resolutions=[18], _zones=[4, 5, 6, 7])
States.generate(state='ground', _vars=[MyGroundTileClass, MyIndividualTileClass], _counts=[3, 1],
                _colors=[COLORS.LBLUE, COLORS.PINK], _resolutions=[20, 15])
States.generate(state='test-tube', _vars=[MyGroundTileClass], _counts=[-1],
                _colors=[COLORS.PURPLE], _resolutions=[5], _zones=[0, 1, 2, 3, 7, 8, 11, 15, 1])
States.generate(state='test-tube', _vars=[MyGroundTileClass], _counts=[18],
                _colors=[COLORS.LBLUE], _resolutions=[[8, 12]])
States.generate(state='test-tube', _vars=[MyGroundTileClass], _counts=[25],
                _colors=[COLORS.RED], _resolutions=[6])

print(States)

Simulation.change_state(States, 0)
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        if event.type == pg.KEYDOWN:
            if not Simulation.user_input_active:
                # change states with number keys
                if event.unicode in states_shortcuts.keys():
                    Simulation.change_state(States, int(event.unicode) - 1)
                if event.key == pg.K_q:
                    States[Simulation.curr_state].env.change_env_dimensions(1, 1, 2, 3)
                elif event.key == pg.K_w:
                    States[Simulation.curr_state].env.change_env_dimensions()
            else:
                # user input is active
                pass

    screen.fill(COLORS.WHITE.color())

    Simulation.draw_state(States)

    Simulation.draw_env_borders(States)

    # tick markings for y coordinates
    for _y in range(0, _env_screen_size[1], 50):
        img = font_small.render(str(_y), True, COLORS.BLACK.color())
        screen.blit(img, (_env_screen_size[0] + 20, _y))
        pg.draw.line(screen, COLORS.BLACK.color(), (_env_screen_size[0], _y), (_env_screen_size[0] + 15, _y))

    pg.display.update()
