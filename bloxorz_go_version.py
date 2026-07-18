
from collections import deque
import time
import tracemalloc

# ==========================================
# 1. BLOCK (Tương đương block.go)
# ==========================================
class Block:
    def __init__(self, ax, ay, bx, by, is_split=False, active_idx=0):
        self.ax = ax
        self.ay = ay
        self.bx = bx
        self.by = by
        self.is_split = is_split
        self.active_idx = active_idx # 0 nếu điều khiển khối A, 1 nếu điều khiển khối B

    @classmethod
    def new_block_down(cls, ax, ay, bx, by):
        """Tạo khối lập phương nằm ngang/dọc"""
        return cls(ax, ay, bx, by, is_split=False)

    @classmethod
    def new_block_up(cls, x, y):
        """Tạo khối lập phương đứng"""
        return cls(x, y, x, y, is_split=False)

    def is_up(self):
        """Kiểm tra xem khối liền có đang đứng không"""
        if self.is_split:
            return False
        return self.ax == self.bx and self.ay == self.by

    def move(self, dx, dy):
        """Tạo một khối mới di chuyển tương đối so với khối hiện tại"""
        # --- LOGIC NÂNG CẤP CHO TRẠNG THÁI TÁCH KHỐI ---
        if self.is_split:
            if self.active_idx == 0:
                # Chỉ di chuyển khối A(ax, ay), khối B(bx, by) giữ nguyên
                n_ax, n_ay = self.ax + dx, self.ay + dy
                n_bx, n_by = self.bx, self.by
            else:
                # Chỉ di chuyển khối B(bx, by), khối A(ax, ay) giữ nguyên
                n_ax, n_ay = self.ax, self.ay
                n_bx, n_by = self.bx + dx, self.by + dy
            
            # Kiểm tra xem sau khi đi, hai khối nhỏ có tụ lại kề nhau để nhập lại làm một không?
            # Điều kiện nhập lại: Khối A và B chạm cạnh nhau theo chiều ngang hoặc dọc
            if (n_ax == n_bx and abs(n_ay - n_by) == 1):
                # Nhập lại thành khối nằm dọc (A nằm trên B hoặc ngược lại)
                ay_min, ay_max = min(n_ay, n_by), max(n_ay, n_by)
                return Block(n_ax, ay_min, n_ax, ay_max, is_split=False)
            elif (n_ay == n_by and abs(n_ax - n_bx) == 1):
                # Nhập lại thành khối nằm ngang (A nằm trái B hoặc ngược lại)
                ax_min, ax_max = min(n_ax, n_bx), max(n_ax, n_bx)
                return Block(ax_min, n_ay, ax_max, n_ay, is_split=False)
            
            # Nếu chưa nhập lại, tiếp tục ở trạng thái tách khối
            return Block(n_ax, n_ay, n_bx, n_by, is_split=True, active_idx=self.active_idx)

        # --- LOGIC DI CHUYỂN BÌNH THƯỜNG CHO CÁC MAP CŨ ---
        if self.is_up():
            if dx == 1 or dy == 1:
                return Block.new_block_down(self.ax + dx, self.ay + dy, self.bx + 2*dx, self.by + 2*dy)
            return Block.new_block_down(self.ax + 2*dx, self.ay + 2*dy, self.bx + dx, self.by + dy)

        is_north_south = (self.ax == self.bx)
        if (is_north_south and dy == 0) or (not is_north_south and dx == 0):
            return Block.new_block_down(self.ax + dx, self.ay + dy, self.bx + dx, self.by + dy)
        if (is_north_south and dy == -1) or (not is_north_south and dx == -1):
            return Block.new_block_up(self.ax + dx, self.ay + dy)
        if (is_north_south and dy == 1) or (not is_north_south and dx == 1):
            return Block.new_block_up(self.bx + dx, self.by + dy)

        raise ValueError(f"Block.move: unreachable {self} {dx} {dy}")

    def equals(self, other):
        """So sánh 2 khối có trùng vị trí không"""
        return (self.ax == other.ax and self.ay == other.ay and 
                self.bx == other.bx and self.by == other.by and self.is_split == other.is_split)

    def __eq__(self, other):
        if not isinstance(other, Block):
            return False
        return (self.ax == other.ax and self.ay == other.ay and
                self.bx == other.bx and self.by == other.by and
                self.is_split == other.is_split and self.active_idx == other.active_idx)

    def __hash__(self):
        return hash((self.ax, self.ay, self.bx, self.by, self.is_split, self.active_idx))

    def __str__(self):
        if self.is_split:
            active_str = "A" if self.active_idx == 0 else "B"
            return f"Split: A({self.ax}, {self.ay}) B({self.bx}, {self.by}) [Active: {active_str}]"
        if self.is_up():
            return f"({self.ax}, {self.ay})"
        return f"({self.ax}, {self.ay})-({self.bx}, {self.by})"


# ==========================================
# 2. PATH (Đã đồng bộ chuẩn hóa)
# ==========================================
class Path:
    def __init__(self, blocks=None):
        # blocks thực chất là danh sách chứa các SolverState
        self.blocks = blocks if blocks is not None else []

    def contains(self, state):
        """Kiểm tra xem trạng thái này đã có trong path chưa"""
        for s in self.blocks:
            if s == state:
                return True
        return False

    def add(self, state):
        self.blocks.append(state)

    def tail(self):
        if not self.blocks:
            return None
        return self.blocks[-1]

    def clone(self):
        return Path(list(self.blocks))

    def __len__(self):
        return len(self.blocks)

    def __str__(self):
        # Kiểm tra an toàn: nếu s là SolverState thì lấy s.block, nếu là Block thì in s
        return "[" + "; ".join(str(getattr(s, 'block', s)) for s in self.blocks) + "]"

class SearchResult:
    def __init__(self, path, search_time, expanded_nodes, memory_usage):
        self.path = path  # Đây sẽ là object Path chứa danh sách SolverState hoàn chỉnh
        self.search_time = search_time
        self.expanded_nodes = expanded_nodes
        self.memory_usage = memory_usage

    @property
    def solution_length(self):
        if self.path is None:
            return 0
        return len(self.path) - 1
    
class SolverState:
    def __init__(self, block, bridges):
        self.block = block
        self.bridges = bridges.copy()

    def get_bridges_dict(self):
        return self.bridges

    def __hash__(self):
        return hash((
            self.block,
            tuple(sorted(self.bridges.items()))
        ))

    def __eq__(self, other):
        if not isinstance(other, SolverState):
            return False
        return (
            self.block == other.block and
            self.bridges == other.bridges
        )

from copy import deepcopy

class SearchNode:
    def __init__(self, path, terrain):
        self.path = path
        self.terrain = terrain

# ==========================================
# 3. TERRAIN (Tương đương terrain.go)
# ==========================================
class ArrayTerrain:
    def __init__(self, start, end, arr, width):
        self._start = start
        self._end = end
        self.arr = arr 
        self.width = width
        self.bridges = {'1': False, '2': False, '3': False} # Thêm biến lưu trạng thái cầu toàn cục lúc check

    def is_legal(self, b):
        # 1. Kiểm tra giới hạn bản đồ
        if (b.ax < 0 or b.ay < 0 or b.bx < 0 or b.by < 0 or
            b.ax >= self.width or b.bx >= self.width or
            b.ay * self.width >= len(self.arr) or b.by * self.width >= len(self.arr)):
            return False

        square_a = self.arr[b.ax + self.width * b.ay]
        square_b = self.arr[b.bx + self.width * b.by]

        # Ô trống '0' thì chắc chắn rơi xuống vực
        if square_a == '0' or square_b == '0':
            return False

        # Định nghĩa hàm kiểm tra một ô cụ thể có hợp lệ không
        def check_tile(tile, is_up_block):
            # Nếu là ô cầu, phải kiểm tra trạng thái cầu đang mở (True) hay đóng
            if tile in ['1', '2', '3']:
                return self.bridges.get(tile, False)
            
            # Ô yếu '.' chỉ trả về False nếu là khối LIỀN đang DỰNG ĐỨNG
            if tile == '.':
                if not getattr(b, 'is_split', False) and is_up_block:
                    return False  # Khối lớn đứng dọc trên ô yếu -> Vỡ
                return True       # Khối tách hoặc khối lớn nằm ngang -> Hợp lệ
                
            return True

        # Nếu là khối tách, cả 2 mảnh nhỏ đều đang ở trạng thái 1x1 nằm ngang (không tính là dựng đứng)
        if getattr(b, 'is_split', False):
            return check_tile(square_a, is_up_block=False) and check_tile(square_b, is_up_block=False)
        
        # Nếu là khối liền thông thường
        return check_tile(square_a, b.is_up()) and check_tile(square_b, b.is_up())

class InfiniteTerrain:
    def __init__(self, start, end):
        self._start = start
        self._end = end

    def is_legal(self, b):
        return True

    def start(self):
        return self._start

    def end(self):
        return self._end


# ==========================================
# 4. BRESENT-FIRST SEARCH SOLVER (Tương đương bloxorz.go)
# ==========================================
# def solve(terrain):
#     """
#     Thuật toán giải BFS.
#     Thay vì dùng Channel (chan) của Go, hàm này sẽ return ngay Path tối ưu đầu tiên tìm được.
#     """
#     queue = deque()
#     path = Path()
#     start_block = terrain.start()
    
#     path.add(start_block)
#     queue.append(path)
    
#     return solve_iter(terrain, queue)

# def solve_iter(terrain, queue):
#     while queue:
#         # Lấy Path đầu tiên ra khỏi Queue
#         path = queue.popleft()
        
#         # Lấy khối cuối cùng của Path đó (vị trí hiện tại)
#         block = path.tail()

#         # 4 hướng: Lên, Xuống, Trái, Phải
#         directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

#         for dx, dy in directions:
#             neighbour = block.move(dx, dy)

#             # Code gốc của Go chỉ check visited trên CÙNG 1 path hiện tại
#             visited = path.contains(neighbour)
            
#             if not visited and terrain.is_legal(neighbour):
#                 new_path = path.clone()
#                 new_path.add(neighbour)
#                 queue.append(new_path)
                
#                 # Tìm thấy lời giải
#                 if neighbour.equals(terrain.end()):
#                     return new_path

#     # Không tìm thấy đường đi
#     return None

def apply_switch(state, terrain):

    block = state.block

    coords = [(block.ax, block.ay)]

    if not block.is_up():
        coords.append((block.bx, block.by))

    for x, y in coords:

        ch = terrain.arr[x + y * terrain.width]

        # Soft switch
        if ch == 'q':
            state.bridges['1'] = not state.bridges['1']

        elif ch == 'w':
            state.bridges['2'] = not state.bridges['2']

        elif ch == 'e':
            state.bridges['3'] = not state.bridges['3']

        # Heavy switch
        elif ch == 'a' and block.is_up():
            state.bridges['1'] = not state.bridges['1']

        elif ch == 's' and block.is_up():
            state.bridges['2'] = not state.bridges['2']

        elif ch == 'd' and block.is_up():
            state.bridges['3'] = not state.bridges['3']

def solve_bfs(terrain):
    """
    BFS chuẩn hóa: Sử dụng SolverState để theo dõi cả vị trí và trạng thái cầu.
    """
    tracemalloc.start()
    start_time = time.perf_counter()

    start_state = SolverState(
        terrain.start(),
        {'1': False, '2': False, '3': False}
    )
    goal = terrain.end()

    # Hàng đợi queue lưu trữ các đối tượng Path chứa SolverState
    queue = deque()
    first_path = Path()
    first_path.add(start_state)
    queue.append(first_path)

    visited = {start_state}
    expanded = 0

    directions = [
        (0, -1), # Lên
        (0, 1),  # Xuống
        (-1, 0), # Trái
        (1, 0)   # Phải
    ]

    while queue:
        path = queue.popleft()
        state = path.tail()  # state lúc này là SolverState hoàn chỉnh
        block = state.block

        expanded += 1

        if block.equals(goal):
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return SearchResult(
                path,
                time.perf_counter() - start_time,
                expanded,
                peak
            )

        for dx, dy in directions:
            nxt_block = block.move(dx, dy)

            # Tạo trạng thái tiếp theo dựa trên trạng thái cầu hiện tại
            new_state = SolverState(
                nxt_block,
                state.bridges
            )

            # Áp dụng thay đổi cầu nếu dẫm vào nút công tắc
            apply_switch(new_state, terrain)

            if terrain.is_legal(nxt_block) and new_state not in visited:
                visited.add(new_state)

                new_path = path.clone()
                new_path.add(new_state)
                queue.append(new_path)

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return SearchResult(None, time.perf_counter() - start_time, expanded, peak)


def solve_dfs(terrain):
    """
    DFS chuẩn hóa: Đồng bộ hóa cấu trúc SolverState tương tự BFS để giải được các map có cầu.
    """
    tracemalloc.start()
    start_time = time.perf_counter()

    start_state = SolverState(
        terrain.start(),
        {'1': False, '2': False, '3': False}
    )
    goal = terrain.end()

    # Stack chứa các đối tượng Path
    stack = []
    first_path = Path()
    first_path.add(start_state)
    stack.append(first_path)  # Sửa lỗi: Đẩy vào stack thay vì queue

    visited = {start_state}
    expanded = 0

    directions = [
        (0, -1),
        (0, 1),
        (-1, 0),
        (1, 0)
    ]

    while stack:
        path = stack.pop()
        state = path.tail()
        block = state.block

        expanded += 1

        if block.equals(goal):
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return SearchResult(
                path,
                time.perf_counter() - start_time,
                expanded,
                peak
            )

        # Duyệt đảo ngược hướng đi để giữ thứ tự ưu tiên tự nhiên khi pop từ Stack
        for dx, dy in reversed(directions):
            nxt_block = block.move(dx, dy)

            new_state = SolverState(
                nxt_block,
                state.bridges
            )

            apply_switch(new_state, terrain)

            if terrain.is_legal(nxt_block) and new_state not in visited:
                visited.add(new_state)

                new_path = path.clone()
                new_path.add(new_state)
                stack.append(new_path)

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return SearchResult(None, time.perf_counter() - start_time, expanded, peak)

# ==========================================
# 5. HÀM CHẠY THỬ (Tương đương bloxorz_test.go)
# ==========================================
def build_terrain_1():
    arr = "S**E"
    start = Block.new_block_up(0, 0)
    end = Block.new_block_up(3, 0)
    return ArrayTerrain(start, end, arr, 4)

def build_terrain_2():
    arr = "***E******S****"
    start = Block.new_block_up(0, 3)
    end = Block.new_block_up(3, 0)
    return ArrayTerrain(start, end, arr, 5)

def build_unsolvable_terrain():
    arr = "..S..E.."
    start = Block.new_block_up(2, 0)
    end = Block.new_block_up(5, 0)
    return ArrayTerrain(start, end, arr, 8)

def test_solvable_terrain(terrain, name, solver):

    result = solver(terrain)

    if result.path:

        print(f"\n{name}")
        print("----------------------------------")
        print(f"Moves          : {result.solution_length}")
        print(f"Search Time    : {result.search_time:.6f} s")
        print(f"Expanded Nodes : {result.expanded_nodes}")
        print(f"Memory Usage   : {result.memory_usage / 1024:.2f} KB")
        print(result.path)

    else:
        print(f"{name} has no solution")

# if __name__ == "__main__":
#     print("--- Chạy thử các Terrain gốc từ tác giả Go ---")
    
#     # Test Terrain 1
#     test_solvable_terrain(build_terrain_1(), "terrain1")
    
#     # Test Terrain 2
#     test_solvable_terrain(build_terrain_2(), "terrain2")
    
#     # Test Unsolvable Terrain
#     test_solvable_terrain(build_unsolvable_terrain(), "unsolvable terrain")
    
#     # Test Infinite Terrain
#     start = Block.new_block_up(0, 0)
#     end = Block.new_block_up(5, 1)
#     test_solvable_terrain(InfiniteTerrain(start, end), "infinite")

if __name__ == "__main__":
    print("========== BFS ==========")

    test_solvable_terrain(build_terrain_1(), "terrain1", solve_bfs)
    test_solvable_terrain(build_terrain_2(), "terrain2", solve_bfs)
    test_solvable_terrain(build_unsolvable_terrain(), "unsolvable terrain", solve_bfs)

    start = Block.new_block_up(0, 0)
    end = Block.new_block_up(5, 1)
    test_solvable_terrain(InfiniteTerrain(start, end), "infinite", solve_bfs)

    print("\n========== DFS ==========")

    test_solvable_terrain(build_terrain_1(), "terrain1", solve_dfs)
    test_solvable_terrain(build_terrain_2(), "terrain2", solve_dfs)
    test_solvable_terrain(build_unsolvable_terrain(), "unsolvable terrain", solve_dfs)

    start = Block.new_block_up(0, 0)
    end = Block.new_block_up(5, 1)
    test_solvable_terrain(InfiniteTerrain(start, end), "infinite", solve_dfs)