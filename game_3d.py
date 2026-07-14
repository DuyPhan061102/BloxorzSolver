from ursina import *
from bloxorz_go_version import Block, ArrayTerrain, Path, solve

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
            "***X*....." # Nút X: Tách khối
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

    def tile_at(self, x, y):
        if (x, y) in self.broken_tiles: return "."
        char = self.arr[x + self.width * y]
        if char in ['1', '2', '3']:
            return '*' if self.bridges[char] else '.'
        # Cho phép dẫm lên các ô công tắc và bệ đáp
        if char in ['[', ']', 'X', 'q', 'w', 'e', 'a', 's', 'd']:
            return '*' 
        return char

    # ĐÃ THÊM: Biến is_half để biết nửa khối đi qua gạch cam sẽ KHÔNG bị vỡ!
    def is_legal(self, b, is_half=False):
        if (b.ax < 0 or b.ay < 0 or b.bx < 0 or b.by < 0 or
            b.ax >= self.width or b.bx >= self.width or
            b.ay * self.width >= len(self.arr) or b.by * self.width >= len(self.arr)):
            return False

        square_a = self.tile_at(b.ax, b.ay)
        square_b = self.tile_at(b.bx, b.by)

        if square_a == "." or square_b == ".": return False
        
        # Chỉ vỡ gạch cam nếu là khối nguyên 1x1x2 ĐỨNG
        if b.is_up() and not is_half and (square_a == "~" or square_b == "~"): 
            return False
        return True

    def break_fragile_under(self, b):
        for x, y in ((b.ax, b.ay), (b.bx, b.by)):
            if self.arr[x + self.width * y] == "~":
                self.broken_tiles.add((x, y))

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
        return (b.ax, 0.5, -b.ay), (1, 1, 1) # Nửa khối thì scale 1x1x1
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
    if char in ['1', '2', '3']: return color.hex('#00ced1') # Màu cầu Cyan
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
                    # Nút Tách Khối (Màu Tím có 2 chấm trắng)
                    btn = Entity(parent=tile, model="cube", color=color.magenta, scale=(0.8, 0.1, 0.8), y=0.51)
                    Entity(parent=btn, model="cube", color=color.white, scale=(0.2, 0.2, 0.2), x=-0.2, y=1)
                    Entity(parent=btn, model="cube", color=color.white, scale=(0.2, 0.2, 0.2), x=0.2, y=1)
                elif char in ['[', ']']:
                    # Điểm đáp của khối vỡ (Bệ màu tím)
                    Entity(parent=tile, model="quad", color=color.magenta, rotation_x=90, scale=(0.6, 0.6, 0.6), y=0.51)
                elif char in ['1', '2', '3']:
                    tile.enabled = False
                    tile.y = -5

            map_entities[(x, y)] = tile

def update_dynamic_tiles():
    map_width = LEVELS[current_level_index]["width"]
    map_data = LEVELS[current_level_index]["data"]
    for (x, y), entity in map_entities.items():
        char = map_data[x + y * map_width]
        if char in ['1', '2', '3']:
            is_active = terrain.bridges[char]
            
            # Nếu cầu đang được lệnh MỞ nhưng entity đang TẮT -> Trồi lên
            if is_active and not entity.enabled:
                entity.enabled = True
                entity.y = -5
                entity.animate_y(-0.1, duration=0.6, curve=curve.out_back) # Hiệu ứng nảy lên
                
            # Nếu cầu đang được lệnh ĐÓNG nhưng entity đang BẬT -> Sụp xuống
            elif not is_active and entity.enabled:
                def hide_bridge(e=entity): e.enabled = False
                entity.animate_y(-5, duration=0.5, curve=curve.in_back) # Hiệu ứng rớt xuống
                invoke(hide_bridge, delay=0.5)

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
        
        # LOGIC TÁCH KHỐI (Split Switch)
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
                return # Ngắt lệnh để không check các công tắc khác lúc bay

        # LOGIC CẦU
        is_soft = char in ['q', 'w', 'e']
        is_heavy = char in ['a', 's', 'd']
        if is_heavy and (not b.is_up() or is_split): continue 
        if is_soft or is_heavy:
            target = '1' if char in ['q', 'a'] else '2' if char in ['w', 's'] else '3'
            terrain.bridges[target] = not terrain.bridges[target]
            switched = True
            
    if switched:
        update_dynamic_tiles()
        status_text.text = "DA KICH HOAT CONG TAC!"

def on_lose():
    global is_animating
    is_animating = True
    status_text.text = "Roi khoi san! Dang hoi sinh..."
    player.animate_y(-10, duration=0.6, curve=curve.in_back)
    invoke(reset_game, delay=0.8)

def finish_move(was_legal):
    global is_animating, is_split, current_block, active_split
    
    if was_legal:
        check_switches(current_block)
        
        # KIỂM TRA GHÉP KHỐI KHI NẰM CẠNH NHAU
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
                
        # KIỂM TRA THẮNG
        if not is_split and current_block.equals(terrain.end()) and current_block.is_up():
            is_animating = True
            win_text.enabled = True
            player.animate_y(-1, duration=0.5, curve=curve.in_quad)
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

def try_move(dx, dy):
    global current_block, move_count, is_animating
    if is_animating: return

    save_state()
    
    if is_split:
        # Khối 1x1x1 chỉ trượt ngang/dọc, không lật thành 1x1x2
        new_block = Block.new_block_up(current_block.ax + dx, current_block.ay + dy)
    else:
        new_block = current_block.move(dx, dy)
        
    was_legal = terrain.is_legal(new_block, is_half=is_split)
    current_block = new_block
    
    if was_legal:
        move_count += 1
        move_text.text = f"Bước: {move_count}"

    is_animating = True
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

def reset_game():
    load_level(current_level_index)

def input(key):
    global active_split, current_block
    if key == "r": reset_game(); return
    if key == "n": load_level(current_level_index + 1); return
    if key == "b": load_level(current_level_index - 1); return
    if key == "z": undo_move(); return
    if key.isdigit() and 1 <= int(key) <= 9: load_level(int(key) - 1); return
    if key == "0": load_level(9); return # 0 để nhảy Màn 10
    
    # CHUYỂN ĐỔI KHỐI BẰNG PHÍM SPACE
    if key == "space" and is_split and not is_animating:
        split_blocks[active_split] = clone_block(current_block)
        active_split = 1 - active_split
        
        # Đổi vị trí hiển thị để Camera & Logic luôn bám theo khối đang điều khiển
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
# 5. UI VÀ KHỞI TẠO
# ==========================================
level_text = Text(text="", scale=1.4, origin=(0, 0), y=0.48, color=color.white)
status_text = Text(text="", scale=1, origin=(0, 0), y=0.42, color=color.light_gray)
move_text = Text(text="Bước: 0", scale=1.2, origin=(-0.5, 0), x=-0.85, y=0.35, color=color.azure)
win_text = Text(text="CHIEN THANG!", scale=2.5, origin=(0, 0), y=0.05, color=color.yellow, enabled=False)

# Khối chính (Đỏ) - Luôn là khối được điều khiển
player = Entity(model="cube", color=color.hex('#8c4646'), texture="white_cube")
# Khối phụ (Xám) - Đại diện cho nửa khối đang đứng im chờ
player2 = Entity(model="cube", color=color.gray, texture="white_cube", visible=False)
load_level(0)

app.run()