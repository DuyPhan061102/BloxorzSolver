from ursina import *
from bloxorz_go_version import (
    Block,
    ArrayTerrain,
    Path,
)
from solver import solve_bfs, solve_dfs

app = Ursina(title="Bloxorz 3D - Advanced Tiles", borderless=False)
window.color = color.hex('#191e28')

# ==========================================
# 1. BẢN ĐỒ VÀ LOGIC ĐÃ ĐƯỢC FIX LỖI
# ==========================================
LEVELS = [
    {
        "name": "Level 1 - Khởi đầu",
        "width": 10,
        "data": (
            "***......."
            "*S****...."
            "*********."
            ".******E**"
            ".....****."
        ),
    },
    {
        "name": "Level 2 - Vùng Đảo",
        "width": 16,
        "data": (
            "****..****..****"
            "S*q*11**s*..*E**"
            "****..****22****"
            "......****..****"
        ),
    },
    {
        "name": "Level 3 - Đường gấp khúc",
        "width": 15,
        "data": (
            "..............."
            "......*******.."
            "****..***..**.."
            "*********..****"
            "*S**.......**E*"
            "****.......****"
            "............***"
        ),
    },
    {
        "name": "Level 4 - Cầu thủy tinh",
        "width": 14,
        "data": (
            "...~~~~~~~...."
            "...~~~~~~~...."
            "****.....***.."
            "***.......**.."
            "***.......**.."
            "*S*..****~~~~~"
            "***..****~~~~~"
            ".....*E*..~~*~"
            ".....***..~~~~"
        ),
    },
    {
        "name": "Level 5 - Cầu ẩn",
        "width": 15,
        "data": (
            "...........****"
            ".****11*q****S*"
            ".****.......***"
            ".****.........."
            ".****.........."
            "...***w*22***.."
            "..........****d"
            "***.......*****"
            "*E*****333***.."
            "*****.........."
        ),
    },
    {
        "name": "Level 6 - Gạch cam & Nút",
        "width": 15,
        "data": (
            ".....******...."
            ".....*..***...."
            ".....*..*****.."
            "S*****.....****"
            "....***....**E*"
            "....***.....***"
            "......*..**...."
            "......*****...."
            "......*****...."
            ".......***....."
        ),
    },
    {
        "name": "Level 7 - Nút Cứng & Kính",
        "width": 11,
        "data": (
            "......****."
            "S***~~****."
            "****..**a*."
            "......****."
            "......1...."
            "......1...."
            "...****...."
            "...*E**...."
            "...****...."
        ),
    },
    {
        "name": "Level 8 - Nút Cứng & Kính",
        "width": 11,
        "data": (
            "......****."
            "S***~~****."
            "****..**a*."
            ".w*...****."
            "......2...."
            "......2...."
            "...1111...."
            "...*E**...."
            "...****...."
        ),
    },
    {
        "name": "Level 9 - Tách Khối ",
        "width": 10,
        "data": (
            "S***......"
            "***X*....." 
            ".........."
            "[********]" 
            ".********."
            ".***E****."
            ".********."
        ),
    },
    {
        "name": "Level 10 - Tách Khối & Nút Mềm",
        "width": 15,
        "data": (
            "......***......"
            "......*S*......"
            "......***......"
            "......***......"
            "......*X*......"
            "..............."
            ".[***.....***]."
            ".*q**.....**w*."
            ".****11222****."
            "......***......"
            "......*E*......"
            "......***......"
        ),
    }
]

class AdvancedTerrain(ArrayTerrain):
    def __init__(self, start, end, arr, width):
        super().__init__(start, end, arr, width)
        self.broken_tiles = set()
        self.bridges = {'1': False, '2': False, '3': False}

    def start(self):
        # Trả về trực tiếp object Block có sẵn trong hệ thống
        return self._start

    def end(self):
        # Trả về trực tiếp object Block đích có sẵn trong hệ thống
        return self._end
        

    def clone(self):
        t = AdvancedTerrain(self._start, self._end, self.arr, self.width)
        t.broken_tiles = self.broken_tiles.copy()
        t.bridges = self.bridges.copy()
        return t

    def tile_at(self, x, y):
        if (x, y) in self.broken_tiles: return "."
        char = self.arr[x + self.width * y]
        if char in ['1', '2', '3']:
            return '*' if self.bridges[char] else '.'
        if char in ['[', ']', 'X', 'q', 'w', 'e', 'a', 's', 'd']:
            return '*' 
        return char

    def is_legal(self, b, is_half=False):
        # Nếu đang ở trạng thái phân thân, ép buộc kiểm tra theo luật is_half = True
        if getattr(b, 'is_split', False):
            is_half = True

        if (b.ax < 0 or b.ay < 0 or b.bx < 0 or b.by < 0 or
            b.ax >= self.width or b.bx >= self.width or
            b.ay * self.width >= len(self.arr) or b.by * self.width >= len(self.arr)):
            return False

        square_a = self.tile_at(b.ax, b.ay)
        square_b = self.tile_at(b.bx, b.by)

        # Rơi xuống vực
        if square_a == "." or square_b == ".":
            return False

        # Khối lớn dựng đứng trên ô kính '~' thì bị vỡ, nhưng mảnh phân thân (is_half=True) thì đi qua được
        if b.is_up() and not is_half and (square_a == "~" or square_b == "~"):
            return False

        return True

    def break_fragile_under(self, b):
        for x, y in ((b.ax, b.ay), (b.bx, b.by)):
            if self.arr[x + self.width * y] == "~":
                self.broken_tiles.add((x, y))

    def activate_switch(self, block):
        coords = []
        # 1. Thu thập tọa độ cần kiểm tra dựa theo trạng thái khối
        if getattr(block, 'is_split', False):
            # Nếu đang tách khối, chỉ kiểm tra ô của mảnh đang được điều khiển (active)
            if block.active_idx == 0:
                coords.append((block.ax, block.ay))
            else:
                coords.append((block.bx, block.by))
        else:
            # Nếu là khối liền bình thường
            coords.append((block.ax, block.ay))
            if not block.is_up():
                coords.append((block.bx, block.by))

        # 2. Duyệt qua các ô tọa độ an toàn
        for x, y in coords:
            # Kiểm tra xem tọa độ có nằm ngoài ma trận chuỗi bản đồ không
            if x < 0 or x >= self.width or y < 0 or y * self.width >= len(self.arr):
                continue
                
            idx = x + self.width * y
            if idx >= len(self.arr):
                continue
                
            c = self.arr[idx]
            
            # --- Giữ nguyên logic xử lý công tắc cũ của bạn ---
            if c == 'q': self.bridges['1'] = True
            elif c == 'w': self.bridges['2'] = True
            elif c == 'e': self.bridges['3'] = True
            elif c == 'a': self.bridges['1'] = not self.bridges['1']
            elif c == 's': self.bridges['2'] = not self.bridges['2']
            elif c == 'd': self.bridges['3'] = not self.bridges['3']

def parse_map(map_data, map_width):
    start_pos, end_pos = (0, 0), (0, 0)
    for i, char in enumerate(map_data):
        if char == "S": start_pos = (i % map_width, i // map_width)
        elif char == "E": end_pos = (i % map_width, i // map_width)
    return start_pos, end_pos

def build_terrain(level):
    start_pos, end_pos = parse_map(level["data"], level["width"])
    start_block = Block.new_block_up(start_pos[0], start_pos[1])
    end_block = Block.new_block_up(end_pos[0], end_pos[1])
    return AdvancedTerrain(start_block, end_block, level["data"], level["width"])

# ==========================================
# 2. KHỞI TẠO BIẾN TRẠNG THÁI
# ==========================================
current_level_index = 0
terrain = None
current_block = None
map_entities = {}
current_pivot = None
is_animating = False
move_count = 0
MOVE_DURATION = 0.22

move_history = []
is_split = False
split_blocks = [None, None]
active_split = 0

def get_player_transform(b):
    if is_split:
        return (b.ax, 0.5, -b.ay), (1, 1, 1)
    if b.is_up(): return (b.ax, 1, -b.ay), (1, 2, 1)
    scale = (1, 1, 2) if b.ax == b.bx else (2, 1, 1)
    return ((b.ax + b.bx) / 2, 0.5, -(b.ay + b.by) / 2), scale

def focus_camera_on_level(level):
    map_width = level["width"]
    height = len(level["data"]) // map_width
    center_x, center_z = (map_width - 1) / 2, -(height - 1) / 2
    dist = max(map_width, height)
    camera.parent = scene
    camera.position = (center_x, dist * 1.2 + 3, center_z - dist * 0.8 - 2)
    camera.rotation_x = 60
    camera.look_at((center_x, 0, center_z))

# ==========================================
# 3. ĐỒ HỌA BẢN ĐỒ VÀ NÚT BẤM
# ==========================================
def tile_color(char):
    if char == "S": return color.hex('#ffd23c')
    if char == "E": return color.black
    if char == "~": return color.hex('#ff8c32')
    if char in ['1', '2', '3']: return color.hex('#00ced1')
    return color.hex('#788291')

def build_map_graphics(level, terrain_obj):
    global map_entities
    for entity in map_entities.values(): destroy(entity)
    map_entities.clear()

    map_width = level["width"]
    map_data = level["data"]
    height = len(map_data) // map_width

    for y in range(height):
        for x in range(map_width):
            char = map_data[x + y * map_width]
            if char == ".": continue
            pos = (x, -0.1, -y)

            if char == "E":
                tile = Entity(model="cube", color=color.black, scale=(1, 0.1, 1), position=(x, -0.2, -y))
            else:
                tile = Entity(model="cube", color=tile_color(char), texture="white_cube", scale=(1, 0.2, 1), position=pos)
                if char in ['q', 'w', 'e']:
                    Entity(parent=tile, model="sphere", color=color.lime, scale=(0.5, 2.5, 0.5), y=0.5)
                elif char in ['a', 's', 'd']:
                    button = Entity(parent=tile, model="cube", color=color.clear, scale=(0.8, 0.1, 0.8), y=0.51)
                    Entity(parent=button, model="cube", color=color.red, scale=(1, 0.2, 0.2), rotation_y=45)
                    Entity(parent=button, model="cube", color=color.red, scale=(1, 0.2, 0.2), rotation_y=-45)
                elif char == 'X':
                    btn = Entity(parent=tile, model="cube", color=color.magenta, scale=(0.8, 0.1, 0.8), y=0.51)
                    Entity(parent=btn, model="cube", color=color.white, scale=(0.2, 0.2, 0.2), x=-0.2, y=1)
                    Entity(parent=btn, model="cube", color=color.white, scale=(0.2, 0.2, 0.2), x=0.2, y=1)
                elif char in ['[', ']']:
                    Entity(parent=tile, model="quad", color=color.magenta, rotation_x=90, scale=(0.6, 0.6, 0.6), y=0.51)
                elif char in ['1', '2', '3']:
                    tile.enabled = False
                    tile.y = -5

            map_entities[(x, y)] = tile

def hide_bridge(e):
    # Đưa hàm này ra ngoài hoặc giữ nguyên nhưng phải check e.ndx an toàn
    if e and not getattr(e, 'destroyed', True) and hasattr(e, 'ndx') and e.ndx and not e.ndx.is_empty():
        try:
            e.enabled = False
        except (AssertionError, Exception):
            pass

def update_dynamic_tiles():
    map_width = LEVELS[current_level_index]["width"]
    map_data = LEVELS[current_level_index]["data"]
    
    for (x, y), entity in map_entities.items():
        idx = x + y * map_width
        if idx >= len(map_data):  # Bảo vệ chống tràn index dữ liệu map
            continue
            
        char = map_data[idx]
        if char in ['1', '2', '3']:
            # Sử dụng .get() để tránh lỗi KeyError nếu map không có đủ cầu
            is_active = False
            if isinstance(terrain.bridges, dict):
                is_active = terrain.bridges.get(char, False)
            elif isinstance(terrain.bridges, (tuple, list)):
                try:
                    is_active = terrain.bridges[int(char) - 1]
                except:
                    is_active = False

            if is_active and not entity.enabled:
                entity.enabled = True
                entity.y = -5
                entity.animate_y(-0.1, duration=0.6, curve=curve.out_back)
                
            elif not is_active and entity.enabled:
                entity.animate_y(-5, duration=0.5, curve=curve.in_back)
                # TRUYỀN THẲNG entity VÀO ĐÂY ĐỂ TRÁNH BỊ SAI BIẾN KHI LẶP VÒNG FOR
                invoke(hide_bridge, entity, delay=0.5)

def update_broken_tile_graphics():
    for bx, by in terrain.broken_tiles:
        if (bx, by) in map_entities:
            tile = map_entities[(bx, by)]
            if tile.color != color.red:
                tile.color = color.red
                tile.animate_y(-10, duration=0.6, curve=curve.in_back)

def update_player_graphics(animate=False, dx=0, dy=0):
    global current_pivot
    target_pos, target_scale = get_player_transform(current_block)

    if animate:
        player.visible = False
        start_pos, start_scale = player.position, player.scale
        
        pivot_x = start_pos[0] + dx * (start_scale[0] / 2)
        pivot_z = start_pos[2] - dy * (start_scale[2] / 2)
        current_pivot = Entity(position=(pivot_x, 0, pivot_z))
        
        dummy = Entity(parent=current_pivot, model="cube", color=player.color, texture=player.texture)
        dummy.world_position, dummy.world_scale = start_pos, start_scale
        
        rot_x, rot_z = 0, 0
        if dx == 1: rot_z = 90
        elif dx == -1: rot_z = -90
        elif dy == 1: rot_x = -90
        elif dy == -1: rot_x = 90
        
        current_pivot.animate_rotation((rot_x, 0, rot_z), duration=MOVE_DURATION, curve=curve.linear)
        
        def cleanup():
            global current_pivot
            if current_pivot: destroy(current_pivot); current_pivot = None
            player.position, player.scale, player.rotation = target_pos, target_scale, (0, 0, 0)
            player.visible = True
        invoke(cleanup, delay=MOVE_DURATION)
    else:
        player.position, player.scale, player.rotation = target_pos, target_scale, (0, 0, 0)
        player.visible = True

# ==========================================
# 4. LOGIC GAMEPLAY
# ==========================================
def clone_block(b):
    return Block(b.ax, b.ay, b.bx, b.by)

def save_state():
    saved_splits = [clone_block(b) for b in split_blocks] if is_split else None
    state = (clone_block(current_block), set(terrain.broken_tiles), move_count, is_split, saved_splits, active_split)
    move_history.append(state)

def undo_move():
    global current_block, move_count, is_animating, is_split, split_blocks, active_split
    if is_animating or not move_history: return

    block, broken, count, s_split, s_blocks, s_active = move_history.pop()
    current_block, terrain.broken_tiles, move_count = block, broken, count
    
    is_split, split_blocks, active_split = s_split, s_blocks, s_active
    if is_split:
        player2.visible = True
        player2.position = (split_blocks[1 - active_split].ax, 0.5, -split_blocks[1 - active_split].ay)
        player2.scale = (1, 1, 1)
    else:
        player2.visible = False
        
    build_map_graphics(LEVELS[current_level_index], terrain)
    update_dynamic_tiles()
    update_player_graphics(animate=False)
    win_text.enabled = False
    status_text.text = "Đã hoàn tác bước trước"

def check_switches(b):
    global is_split, split_blocks, active_split, current_block
    
    map_width = LEVELS[current_level_index]["width"]
    map_data = LEVELS[current_level_index]["data"]
    coords = [(b.ax, b.ay)]
    if not b.is_up(): coords.append((b.bx, b.by))
    
    switched = False
    for x, y in coords:
        char = map_data[x + y * map_width]
        
        if char == 'X' and b.is_up() and not is_split:
            idx1, idx2 = map_data.find('['), map_data.find(']')
            if idx1 != -1 and idx2 != -1:
                x1, y1 = idx1 % map_width, idx1 // map_width
                x2, y2 = idx2 % map_width, idx2 // map_width
                
                is_split = True
                active_split = 0
                split_blocks = [Block.new_block_up(x1, y1), Block.new_block_up(x2, y2)]
                current_block = clone_block(split_blocks[0])
                
                player.position, player.scale = (x1, 0.5, -y1), (1, 1, 1)
                player2.position, player2.scale = (x2, 0.5, -y2), (1, 1, 1)
                player2.visible = True
                
                status_text.text = "DA TACH KHOI! Bam SPACE de chuyen doi"
                return

        is_soft = char in ['q', 'w', 'e']
        is_heavy = char in ['a', 's', 'd']
        if is_heavy and (not b.is_up() or is_split): continue 
        if is_soft or is_heavy:
            target = '1' if char in ['q', 'a'] else '2' if char in ['w', 's'] else '3'
            terrain.bridges[target] = not terrain.bridges[target]
            switched = True
            
    if switched:
        sound_switch.play()
        update_dynamic_tiles()
        status_text.text = "DA KICH HOAT CONG TAC!"

def on_lose():
    global is_animating
    is_animating = True
    sound_fall.play()
    status_text.text = "Roi khoi san! Dang hoi sinh..."
    player.animate_y(-10, duration=0.6, curve=curve.in_back)
    invoke(reset_game, delay=0.8)

def finish_move(was_legal):
    global is_animating, is_split, current_block, active_split
    
    if was_legal:
        check_switches(current_block)
        
        if is_split:
            split_blocks[active_split] = clone_block(current_block)
            b1, b2 = split_blocks[0], split_blocks[1]
            dx_merge, dy_merge = abs(b1.ax - b2.ax), abs(b1.ay - b2.ay)
            
            if (dx_merge == 1 and dy_merge == 0) or (dx_merge == 0 and dy_merge == 1):
                is_split = False
                player2.visible = False
                current_block = Block(min(b1.ax, b2.ax), min(b1.ay, b2.ay), max(b1.ax, b2.ax), max(b1.ay, b2.ay))
                update_player_graphics(animate=False)
                status_text.text = "DA GHEP KHOI THANH CONG!"
                
        if not is_split and current_block.equals(terrain.end()) and current_block.is_up():
            trigger_win_state()
            return
    else:
        if not is_split and current_block.is_up():  
            sq_a = terrain.arr[current_block.ax + terrain.width * current_block.ay]
            sq_b = terrain.arr[current_block.bx + terrain.width * current_block.by]
            if sq_a == "~" or sq_b == "~":
                terrain.break_fragile_under(current_block)
                update_broken_tile_graphics()
        on_lose()
        return
        
    is_animating = False

def trigger_win_state():
    """Hàm xử lý logic và đồ họa khi thắng màn (Dùng chung cho cả người chơi và AI)"""
    global is_animating
    is_animating = True
    sound_win.play()
    player.animate_y(-1, duration=0.5, curve=curve.in_quad)
    
    invoke(lambda: setattr(btn_restart, 'enabled', False), delay=0.5)
    
    if current_level_index == len(LEVELS) - 1:
        win_text.text = "CHÚC MỪNG!\nBẠN ĐÃ PHÁ ĐẢO GAME!"
        win_text.enabled = True
    else:
        win_text.text = "CHIẾN THẮNG!"
        win_text.enabled = True
        if game_mode == 'MANUAL':
            invoke(lambda: setattr(btn_next, 'enabled', True), delay=0.6)

def try_move(dx, dy):
    global current_block, move_count, is_animating
    if is_animating: return

    save_state()
    
    if is_split:
        new_block = Block.new_block_up(current_block.ax + dx, current_block.ay + dy)
    else:
        new_block = current_block.move(dx, dy)
        
    was_legal = terrain.is_legal(new_block, is_half=is_split)
    current_block = new_block
    
    if was_legal:
        move_count += 1
        move_text.text = f"Bước: {move_count}"

    is_animating = True
    sound_move.play()
    update_player_graphics(animate=True, dx=dx, dy=dy)
    invoke(finish_move, was_legal, delay=MOVE_DURATION)

def load_level(index):
    global current_level_index, terrain, current_block, move_count, is_animating, is_split, active_split
    
    if current_pivot: destroy(current_pivot)
    move_history.clear()

    current_level_index = index % len(LEVELS)
    level = LEVELS[current_level_index]
    terrain = build_terrain(level)
    current_block = terrain.start()
    
    is_split, active_split, move_count, is_animating = False, 0, 0, False
    if player2: player2.visible = False
    
    build_map_graphics(level, terrain)
    update_dynamic_tiles() 
    focus_camera_on_level(level)

    if player:
        if hasattr(player, 'animations'): player.animations.clear()
        update_player_graphics(animate=False)

    win_text.enabled = False
    level_text.text = f"{level['name']}  ({current_level_index + 1}/{len(LEVELS)})"
    status_text.text = "Mũi tên: Di chuyển | R: Chơi lại | N: Màn tiếp | SPACE: Đổi khối | Z: Hoàn tác"
    move_text.text = "Bước: 0"
    stats_text.text = ""
    stats_text.enabled = False

def reset_game():
    load_level(current_level_index)

def input(key):
    global active_split, current_block
    if game_mode == 'MENU': return 
    if game_mode == 'AI': return   

    # --- FIX LỖI TRÙNG LẶP PHÍM ---
    if key == "r": reset_game(); return
    if key == "n" and game_mode == 'MANUAL': load_level(current_level_index + 1); return
    if key == "b" and game_mode == 'MANUAL': load_level(current_level_index - 1); return
    if key == "z" and game_mode == 'MANUAL': undo_move(); return
    if key.isdigit() and 1 <= int(key) <= 9: load_level(int(key) - 1); return
    if key == "0": load_level(9); return 
    
    if key == "space" and is_split and not is_animating:
        split_blocks[active_split] = clone_block(current_block)
        active_split = 1 - active_split
        
        p1_pos = player.position
        player.position = player2.position
        player2.position = p1_pos
        
        current_block = clone_block(split_blocks[active_split])
        status_text.text = f"Dang dieu khien khoi {active_split + 1}"
        return

    if is_animating: return
    dx, dy = 0, 0
    if key in ("w", "up arrow"): dy = -1
    elif key in ("s", "down arrow"): dy = 1
    elif key in ("a", "left arrow"): dx = -1
    elif key in ("d", "right arrow"): dx = 1
    if dx or dy: try_move(dx, dy)

# ==========================================
# 5. UI, MENU CHÍNH VÀ KHỞI TẠO GAME
# ==========================================
game_mode = 'MENU' 
selected_ai = None

level_text = Text(text="", scale=1.4, origin=(0, 0), y=0.48, color=color.white, enabled=False)
status_text = Text(text="", scale=1, origin=(0, 0), y=0.42, color=color.light_gray, enabled=False)
move_text = Text(text="Bước: 0", scale=1.2, origin=(-0.5, 0), x=-0.85, y=0.35, color=color.azure, enabled=False)
win_text = Text(text="CHIẾN THẮNG!", scale=2.5, origin=(0, 0), y=0.05, color=color.yellow, enabled=False)

stats_text = Text(text="", scale=1, origin=(-0.5, 0.5), x=0.55, y=0.32, color=color.white, enabled=False)

btn_menu = Button("Menu Chính", position=(-0.75, 0.45), scale=(0.15, 0.05), color=color.red, enabled=False)
btn_restart = Button("Chơi Lại", position=(-0.75, 0.38), scale=(0.15, 0.05), color=color.orange, enabled=False)
btn_next = Button("Màn Tiếp Theo", position=(0, -0.15), scale=(0.25, 0.08), color=color.azure, enabled=False)

menu_bg = Entity(parent=camera.ui, model='quad', scale=(2, 1.2), texture='background.png', color=color.gray)

# 1. Menu Chính
main_menu = Entity(parent=camera.ui)
Text(text="BLOXORZ 3D", parent=main_menu, scale=4, origin=(0,0), y=0.25, color=color.orange)
Button(text="Người chơi tự chơi", parent=main_menu, scale=(0.4, 0.08), y=0.05, color=color.clear, text_color=color.white, on_click=lambda: start_manual_game())
Button(text="Máy giải (AI)", parent=main_menu, scale=(0.4, 0.08), y=-0.05, color=color.clear, text_color=color.white, on_click=lambda: show_menu(ai_menu))

# 2. Menu Chọn Giải Thuật AI
ai_menu = Entity(parent=camera.ui, enabled=False)
Text(text="CHỌN THUẬT TOÁN", parent=ai_menu, scale=2.5, origin=(0,0), y=0.25, color=color.yellow)
Button(text="Solve BFS", parent=ai_menu, scale=(0.25, 0.08), position=(-0.15, 0.1), color=color.clear, text_color=color.white, on_click=lambda: select_algo("BFS"))
Button(text="Solve DFS", parent=ai_menu, scale=(0.25, 0.08), position=(0.15, 0.1), color=color.clear, text_color=color.white, on_click=lambda: select_algo("DFS"))
Button(text="Solve UCS", parent=ai_menu, scale=(0.25, 0.08), position=(-0.15, 0), color=color.clear, text_color=color.white, on_click=lambda: select_algo("UCS"))
Button(text="Solve A*", parent=ai_menu, scale=(0.25, 0.08), position=(0.15, 0), color=color.clear, text_color=color.white, on_click=lambda: select_algo("A*"))
Button(text="Quay Lại", parent=ai_menu, scale=(0.2, 0.06), y=-0.2, color=color.clear, text_color=color.red, on_click=lambda: show_menu(main_menu))

# 3. Menu Chọn Màn Chơi (Dành cho AI)
level_menu = Entity(parent=camera.ui, enabled=False)
Text(text="CHỌN MÀN CẦN GIẢI", parent=level_menu, scale=2.5, origin=(0,0), y=0.35, color=color.yellow)
for i in range(10): 
    x_pos = -0.3 + (i % 4) * 0.2
    y_pos = 0.15 - (i // 4) * 0.15
    Button(text=f"Map {i+1}", parent=level_menu, scale=(0.15, 0.08), position=(x_pos, y_pos), color=color.clear, text_color=color.white, on_click=Func(lambda idx=i: start_ai_game(idx)))
Button(text="Quay Lại", parent=level_menu, scale=(0.2, 0.06), y=-0.3, color=color.clear, text_color=color.red, on_click=lambda: show_menu(ai_menu))

# ---- CÁC HÀM XỬ LÝ SỰ KIỆN MENU ----
def show_menu(menu_entity):
    main_menu.enabled = ai_menu.enabled = level_menu.enabled = False
    menu_entity.enabled = True

def select_algo(algo_name):
    global selected_ai
    selected_ai = algo_name
    show_menu(level_menu)

def start_manual_game():
    global game_mode
    game_mode = 'MANUAL'
    menu_bg.enabled = main_menu.enabled = False
    btn_menu.enabled = btn_restart.enabled = True
    level_text.enabled = status_text.enabled = move_text.enabled = True
    load_level(0) 

def start_ai_game(level_idx):
    global game_mode
    game_mode = 'AI'
    menu_bg.enabled = ai_menu.enabled = level_menu.enabled = False
    btn_menu.enabled = btn_restart.enabled = True
    level_text.enabled = status_text.enabled = move_text.enabled = True
    load_level(level_idx)
    status_text.text = f"Đang chờ AI tính toán bằng {selected_ai}..."
    invoke(run_ai_solver, delay=0.5)

def back_to_menu():
    global game_mode
    game_mode = 'MENU'
    menu_bg.enabled = True
    show_menu(main_menu)
    stats_text.enabled = False
    btn_menu.enabled = btn_restart.enabled = btn_next.enabled = win_text.enabled = False
    level_text.enabled = status_text.enabled = move_text.enabled = False
    if current_pivot: destroy(current_pivot)

def next_level():
    btn_next.enabled = False
    load_level(current_level_index + 1)

btn_menu.on_click = back_to_menu
btn_restart.on_click = lambda: load_level(current_level_index)
btn_next.on_click = next_level

def run_ai_solver():
    global stats_text
    status_text.text = f"AI {selected_ai} đang giải..."

    if selected_ai == "BFS":
        result = solve_bfs(terrain)
    elif selected_ai == "DFS":
        result = solve_dfs(terrain)
    else:
        return

    if result.path is None:
        status_text.text = "Không tìm thấy lời giải!"
        return

    stats_text.text = (
        f"{selected_ai} Statistics\n\n"
        f"Moves: {result.solution_length}\n"
        f"Expanded: {result.expanded_nodes}\n"
        f"Time: {result.search_time:.6f} s\n"
        f"Memory: {result.memory_usage:.2f} KB"
    )
    stats_text.enabled = True
    animate_solution(result.path)

def animate_solution(path):
    moves = path.blocks
    
    # Cho phép người dùng biết AI đang bắt đầu chạy bước đầu tiên
    global is_animating
    is_animating = True

    def step(i):
        global current_block, is_split, split_blocks, active_split, is_animating

        if i >= len(moves):
            status_text.text = "AI hoàn thành!"
            is_animating = False
            # Kiểm tra xem khối cuối cùng có khớp ô đích không để báo thắng
            if current_block.equals(terrain.end()) and current_block.is_up():
                trigger_win_state()
            return

        # 1. Trích xuất Block từ SolverState
        current_state = moves[i]
        if hasattr(current_state, 'block'):
            current_block = current_state.block
            
            # --- XỬ LÝ ĐỒNG BỘ CẦU ĐƯỜNG AN TOÀN 100% ---
            ai_bridges = None
            if hasattr(current_state, 'bridges'):
                ai_bridges = current_state.bridges
            elif hasattr(current_state, 'get_bridges_dict'):
                ai_bridges = current_state.get_bridges_dict()
                
            if ai_bridges is not None:
                # Tạo ra một Dictionary bảo vệ, chứa cả key string và key int
                safe_bridges = {}
                if isinstance(ai_bridges, dict):
                    for k, v in ai_bridges.items():
                        safe_bridges[str(k)] = v
                        if str(k).isdigit():
                            safe_bridges[int(k)] = v
                            # Đồng thời hỗ trợ cả index dạng 0, 1, 2 phòng hờ
                            safe_bridges[int(k) - 1] = v 
                elif isinstance(ai_bridges, (tuple, list)):
                    for idx, v in enumerate(ai_bridges):
                        safe_bridges[idx] = v
                        safe_bridges[str(idx + 1)] = v
                        safe_bridges[int(idx + 1)] = v
                
                # Gán dictionary đa năng này cho terrain.bridges
                terrain.bridges = safe_bridges
        else:
            current_block = current_state

        move_text.text = f"Bước: {i}"
        
        # 2. Xử lý đồng bộ trạng thái TÁCH KHỐI trong GUI
        if getattr(current_block, 'is_split', False):
            is_split = True
            player2.visible = True
            
            # Tính toán vị trí hiển thị cho cả 2 mảnh nhỏ (mảnh 1x1)
            player.position = (current_block.ax, 0.5, -current_block.ay)
            player.scale = (1, 1, 1)
            
            player2.position = (current_block.bx, 0.5, -current_block.by)
            player2.scale = (1, 1, 1)
            
            # Highlight mảnh đang được AI chọn để điều khiển
            if getattr(current_block, 'active_idx', 0) == 0:
                player.color = color.hex('#8c4646')  # Mảnh chủ đạo (Màu đỏ)
                player2.color = color.gray           # Mảnh phụ (Màu xám)
            else:
                player.color = color.gray            # Mảnh phụ đổi sang xám
                player2.color = color.hex('#8c4646') # Mảnh active đổi sang đỏ
        else:
            is_split = False
            player2.visible = False
            player.color = color.hex('#8c4646')
            
            # Lấy vị trí, kích thước chuẩn (đứng/nằm) và gán mượt mà cho player chính
            target_pos, target_scale = get_player_transform(current_block)
            player.position, player.scale, player.rotation = target_pos, target_scale, (0, 0, 0)

        # 3. Cập nhật cơ chế kích hoạt các ô chức năng trên bản đồ
        terrain.activate_switch(current_block)
        
        # Gọi cập nhật các ô cầu/cửa động mà không lo bị lỗi chỉ mục nữa
        update_dynamic_tiles()
        
        # Nếu giẫm phải ô kính '~' làm vỡ gạch, cập nhật hiệu ứng gạch rơi luôn trên GUI
        for x, y in ((current_block.ax, current_block.ay), (current_block.bx, current_block.by)):
            # TÍNH TOÁN INDEX VÀ BẢO VỆ CHỐNG TRÀN MẢNG (INDEX OUT OF RANGE)
            idx = x + terrain.width * y
            if 0 <= idx < len(terrain.arr) and 0 <= x < terrain.width:
                if terrain.arr[idx] == "~" and current_block.is_up() and not is_split:
                    terrain.broken_tiles.add((x, y))
                    
        update_broken_tile_graphics()

        # 4. Gọi đệ quy bước tiếp theo
        invoke(step, i + 1, delay=0.18)

    step(0)

# ---- KHỞI TẠO VÀ CHẠY GAME ----
player = Entity(model="cube", color=color.hex('#8c4646'), texture="white_cube")
player2 = Entity(model="cube", color=color.gray, texture="white_cube", visible=False)

sound_move = Audio('move.wav', autoplay=False)
sound_fall = Audio('fall.wav', autoplay=False)
sound_win = Audio('win.wav', autoplay=False)
sound_switch = Audio('switch.wav', autoplay=False)

back_to_menu()
app.run()