from collections import deque
import time
import tracemalloc
import heapq

# ==========================================
# 1. BLOCK 
# ==========================================
class Block:
    def __init__(self, ax, ay, bx, by):
        self.ax, self.ay, self.bx, self.by = ax, ay, bx, by
    @classmethod
    def new_block_down(cls, ax, ay, bx, by): return cls(ax, ay, bx, by)
    @classmethod
    def new_block_up(cls, x, y): return cls(x, y, x, y)
    def is_up(self): return self.ax == self.bx and self.ay == self.by
    def move(self, dx, dy):
        if self.is_up():
            if dx == 1 or dy == 1: return Block.new_block_down(self.ax + dx, self.ay + dy, self.bx + 2*dx, self.by + 2*dy)
            return Block.new_block_down(self.ax + 2*dx, self.ay + 2*dy, self.bx + dx, self.by + dy)
        is_ns = (self.ax == self.bx)
        if (is_ns and dy == 0) or (not is_ns and dx == 0): return Block.new_block_down(self.ax + dx, self.ay + dy, self.bx + dx, self.by + dy)
        if (is_ns and dy == -1) or (not is_ns and dx == -1): return Block.new_block_up(self.ax + dx, self.ay + dy)
        if (is_ns and dy == 1) or (not is_ns and dx == 1): return Block.new_block_up(self.bx + dx, self.by + dy)
        raise ValueError("Block.move error")
    def equals(self, other): return self.ax == other.ax and self.ay == other.ay and self.bx == other.bx and self.by == other.by

# ==========================================
# 2. PATH (GIỜ LƯU CÁC HÀNH ĐỘNG THAY VÌ KHỐI)
# ==========================================
class Path:
    def __init__(self, actions=None): self.actions = actions if actions is not None else []
    def add(self, action): self.actions.append(action)
    def clone(self): return Path(list(self.actions))
    def __len__(self): return len(self.actions)

# ==========================================
# 3. TERRAIN & AI STATE MỚI (HỖ TRỢ 2 KHỐI)
# ==========================================
class ArrayTerrain:
    def __init__(self, start, end, arr, width):
        self._start, self._end, self.arr, self.width = start, end, arr, width
    def start(self): return self._start
    def end(self): return self._end

class AIState:
    def __init__(self, block, bridges, is_split=False, block2=None, active_idx=0):
        self.block = block
        self.bridges = bridges
        self.is_split = is_split
        self.block2 = block2
        self.active_idx = active_idx # 0 hoặc 1 (Biết khối nào đang được điều khiển)

    def get_hash(self):
        br_tuple = tuple(sorted(self.bridges.items()))
        if not self.is_split:
            return (self.block.ax, self.block.ay, self.block.bx, self.block.by, False, 0, br_tuple)
        return (self.block.ax, self.block.ay, self.block2.ax, self.block2.ay, True, self.active_idx, br_tuple)

def get_tile(arr, width, x, y, bridges):
    if x < 0 or y < 0 or x >= width or y * width >= len(arr): return '.'
    char = arr[x + y * width]
    if char in ['1', '2', '3']: return '*' if bridges.get(char, False) else '.'
    if char in ['[', ']', 'X', 'q', 'w', 'e', 'a', 's', 'd']: return '*'
    return char

def is_legal_sim(b, arr, width, bridges, is_half):
    sq_a = get_tile(arr, width, b.ax, b.ay, bridges)
    sq_b = get_tile(arr, width, b.bx, b.by, bridges)
    if sq_a == '.' or sq_b == '.': return False
    if b.is_up() and not is_half:
        char_a = arr[b.ax + b.ay * width]
        char_b = arr[b.bx + b.by * width]
        if char_a == '~' or char_b == '~': return False
    return True

def check_split(b, arr, width):
    if not b.is_up(): return False, None, None
    char = arr[b.ax + b.ay * width]
    if char == 'X':
        idx1, idx2 = arr.find('['), arr.find(']')
        if idx1 != -1 and idx2 != -1:
            return True, Block.new_block_up(idx1 % width, idx1 // width), Block.new_block_up(idx2 % width, idx2 // width)
    return False, None, None

def trigger_switches(b, arr, width, bridges, is_half):
    new_bridges = bridges.copy()
    coords = [(b.ax, b.ay)] if b.is_up() else [(b.ax, b.ay), (b.bx, b.by)]
    for x, y in coords:
        char = arr[x + y * width]
        is_soft = char in ['q', 'w', 'e']
        is_heavy = char in ['a', 's', 'd']
        if is_heavy and (not b.is_up() or is_half): continue 
        if is_soft or is_heavy:
            target = '1' if char in ['q', 'a'] else '2' if char in ['w', 's'] else '3'
            new_bridges[target] = not new_bridges[target]
    return new_bridges

def get_neighbors(state, arr, width):
    neighbors = []
    # NƯỚC ĐI 1: NẾU ĐANG TÁCH, CÓ THỂ BẤM PHÍM 'SPACE' ĐỂ ĐỔI KHỐI
    if state.is_split:
        new_state = AIState(state.block, state.bridges, True, state.block2, 1 - state.active_idx)
        neighbors.append((new_state, (0, 0, True))) # (dx, dy, space_pressed)
        
    active_block = state.block if state.active_idx == 0 else state.block2
    other_block = state.block2 if state.active_idx == 0 else state.block
    
    # NƯỚC ĐI 2: LĂN LÊN/XUỐNG/TRÁI/PHẢI
    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
        try:
            if not state.is_split:
                neighbour = active_block.move(dx, dy)
                if is_legal_sim(neighbour, arr, width, state.bridges, False):
                    is_split, b1, b2 = check_split(neighbour, arr, width)
                    new_bridges = trigger_switches(neighbour, arr, width, state.bridges, False)
                    if is_split: ns = AIState(b1, new_bridges, True, b2, 0)
                    else: ns = AIState(neighbour, new_bridges, False, None, 0)
                    neighbors.append((ns, (dx, dy, False)))
            else:
                new_active = Block.new_block_up(active_block.ax + dx, active_block.ay + dy)
                if is_legal_sim(new_active, arr, width, state.bridges, True):
                    new_bridges = trigger_switches(new_active, arr, width, state.bridges, True)
                    dx_merge, dy_merge = abs(new_active.ax - other_block.ax), abs(new_active.ay - other_block.ay)
                    
                    # Nếu 2 nửa gặp nhau -> Ghép khối!
                    if (dx_merge == 1 and dy_merge == 0) or (dx_merge == 0 and dy_merge == 1):
                        merged_block = Block(
                            min(new_active.ax, other_block.ax), min(new_active.ay, other_block.ay),
                            max(new_active.ax, other_block.ax), max(new_active.ay, other_block.ay)
                        )
                        ns = AIState(merged_block, new_bridges, False, None, 0)
                    else:
                        b1 = new_active if state.active_idx == 0 else state.block
                        b2 = state.block2 if state.active_idx == 0 else new_active
                        ns = AIState(b1, new_bridges, True, b2, state.active_idx)
                    neighbors.append((ns, (dx, dy, False)))
        except: pass
    return neighbors

# ==========================================
# 4. CHẠY THUẬT TOÁN
# ==========================================
def solve(terrain, algo="BFS"):
    tracemalloc.start()
    start_time = time.perf_counter()
    
    path, nodes = None, 0
    if algo == "BFS": path, nodes = solve_bfs(terrain)
    elif algo == "DFS": path, nodes = solve_dfs(terrain)
    elif algo == "UCS": path, nodes = solve_ucs(terrain)
    elif algo == "A*": path, nodes = solve_astar(terrain)
        
    end_time = time.perf_counter()
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "path": path,
        "time_ms": (end_time - start_time) * 1000,
        "mem_kb": peak_mem / 1024,
        "nodes": nodes,
        "length": len(path) if path else 0
    }

def solve_bfs(terrain):
    queue = deque()
    start_state = AIState(terrain.start(), {'1': False, '2': False, '3': False}, False, None, 0)
    queue.append((start_state, Path()))
    visited = {start_state.get_hash()}
    nodes = 0
    while queue:
        state, path = queue.popleft()
        nodes += 1
        if not state.is_split and state.block.equals(terrain.end()) and state.block.is_up(): return path, nodes
        for next_state, action in get_neighbors(state, terrain.arr, terrain.width):
            h = next_state.get_hash()
            if h not in visited:
                visited.add(h)
                new_path = path.clone()
                new_path.add(action)
                queue.append((next_state, new_path))
    return None, nodes

def solve_dfs(terrain):
    stack = []
    start_state = AIState(terrain.start(), {'1': False, '2': False, '3': False}, False, None, 0)
    stack.append((start_state, Path()))
    visited = set()
    nodes = 0
    while stack:
        state, path = stack.pop()
        h = state.get_hash()
        if h in visited: continue
        visited.add(h)
        nodes += 1
        if not state.is_split and state.block.equals(terrain.end()) and state.block.is_up(): return path, nodes
        for next_state, action in get_neighbors(state, terrain.arr, terrain.width):
            if next_state.get_hash() not in visited:
                new_path = path.clone()
                new_path.add(action)
                stack.append((next_state, new_path))
    return None, nodes

def solve_ucs(terrain):
    pq = []
    start_state = AIState(terrain.start(), {'1': False, '2': False, '3': False}, False, None, 0)
    heapq.heappush(pq, (0, id(start_state), start_state, Path()))
    visited = set()
    nodes = 0
    while pq:
        cost, _, state, path = heapq.heappop(pq)
        h = state.get_hash()
        if h in visited: continue
        visited.add(h)
        nodes += 1
        if not state.is_split and state.block.equals(terrain.end()) and state.block.is_up(): return path, nodes
        for next_state, action in get_neighbors(state, terrain.arr, terrain.width):
            if next_state.get_hash() not in visited:
                new_path = path.clone()
                new_path.add(action)
                heapq.heappush(pq, (cost + 1, id(next_state), next_state, new_path))
    return None, nodes

def heuristic(state, end_b):
    if state.is_split:
        h1 = abs(state.block.ax - end_b.ax) + abs(state.block.ay - end_b.ay)
        h2 = abs(state.block2.ax - end_b.ax) + abs(state.block2.ay - end_b.ay)
        return min(h1, h2)
    return abs(state.block.ax - end_b.ax) + abs(state.block.ay - end_b.ay)

def solve_astar(terrain):
    pq = []
    start_state = AIState(terrain.start(), {'1': False, '2': False, '3': False}, False, None, 0)
    heapq.heappush(pq, (heuristic(start_state, terrain.end()), 0, id(start_state), start_state, Path()))
    visited = set()
    nodes = 0
    while pq:
        f, g, _, state, path = heapq.heappop(pq)
        h = state.get_hash()
        if h in visited: continue
        visited.add(h)
        nodes += 1
        if not state.is_split and state.block.equals(terrain.end()) and state.block.is_up(): return path, nodes
        for next_state, action in get_neighbors(state, terrain.arr, terrain.width):
            if next_state.get_hash() not in visited:
                new_path = path.clone()
                new_path.add(action)
                new_g = g + 1
                new_h = heuristic(next_state, terrain.end())
                heapq.heappush(pq, (new_g + new_h, new_g, id(next_state), next_state, new_path))
    return None, nodes