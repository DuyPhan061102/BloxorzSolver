from collections import deque
import time
import tracemalloc

from bloxorz_go_version import Block
from bloxorz_go_version import Path

class SolverState:
    def __init__(self, block, bridges):
        self.block = block
        # Lưu trạng thái cầu dạng tuple để có thể hash được ổn định
        self.bridges = tuple(sorted(bridges.items()))

    def get_bridges_dict(self):
        return dict(self.bridges)

    def __hash__(self):
        return hash((
            self.block.ax,
            self.block.ay,
            self.block.bx,
            self.block.by,
            self.block.is_split,    # QUAN TRỌNG: Thêm trạng thái tách khối
            self.block.active_idx,  # QUAN TRỌNG: Thêm mảnh đang hoạt động
            self.bridges
        ))

    def __eq__(self, other):
        return (
            self.block.ax == other.block.ax and
            self.block.ay == other.block.ay and
            self.block.bx == other.block.bx and
            self.block.by == other.block.by and
            self.block.is_split == other.block.is_split and       # Thêm kiểm tra
            self.block.active_idx == other.block.active_idx and   # Thêm kiểm tra
            self.bridges == other.bridges
        )

# def apply_switches_for_state(old_block, new_block, current_bridges, terrain):
#     """
#     Chỉ kích hoạt công tắc tại các ô mà new_block chiếm giữ NHƯNG old_block chưa chiếm giữ.
#     """
#     bridges = dict(current_bridges)
#     width = terrain.width
#     data = terrain.arr

#     # Tọa độ cũ và mới
#     old_coords = {(old_block.ax, old_block.ay)}
#     if not old_block.is_up(): old_coords.add((old_block.bx, old_block.by))

#     new_coords = [(new_block.ax, new_block.ay)]
#     if not new_block.is_up(): new_coords.append((new_block.bx, new_block.by))

#     for x, y in new_coords:
#         # Chỉ kích hoạt nếu đây là ô MỚI bước lên
#         if (x, y) in old_coords:
#             continue

#         if x < 0 or x >= width or y < 0 or y >= len(data) // width:
#             continue
            
#         ch = data[x + y * width]
#         soft = ch in ['q', 'w', 'e', 'Q', 'W', 'E']
#         heavy = ch in ['a', 's', 'd', 'A', 'S', 'D']

#         if heavy and not new_block.is_up():
#             continue

#         if soft or heavy:
#             if ch in ['q', 'a', 'Q', 'A']:
#                 bridges['1'] = not bridges['1']
#             elif ch in ['w', 's', 'W', 'S']:
#                 bridges['2'] = not bridges['2']
#             elif ch in ['e', 'd', 'E', 'D']:
#                 bridges['3'] = not bridges['3']

#     return bridges

# # Trong vòng lặp BFS / DFS, cập nhật lại lời gọi hàm:
# # new_bridges = apply_switches_for_state(block, nxt, current_bridges, terrain)

def apply_switches_for_state(old_block, new_block, current_bridges, terrain):
    bridges = dict(current_bridges)
    width = terrain.width
    data = terrain.arr

    # Lấy danh sách các ô mà khối mới sẽ chiếm giữ
    new_coords = []
    if new_block.is_split:
        # Nếu đang phân thân, chỉ tính tọa độ của mảnh đang hoạt động (vừa di chuyển xong)
        if new_block.active_idx == 0:
            new_coords.append((new_block.ax, new_block.ay))
        else:
            new_coords.append((new_block.bx, new_block.by))
    else:
        new_coords.append((new_block.ax, new_block.ay))
        if not new_block.is_up(): 
            new_coords.append((new_block.bx, new_block.by))

    # Tính toán tập hợp các ô khối cũ đã đứng để tránh kích hoạt lại công tắc cũ
    old_coords = set()
    if old_block.is_split:
        old_coords.add((old_block.ax, old_block.ay))
        old_coords.add((old_block.bx, old_block.by))
    else:
        old_coords.add((old_block.ax, old_block.ay))
        if not old_block.is_up():
            old_coords.add((old_block.bx, old_block.by))

    for x, y in new_coords:
        if (x, y) in old_coords: # Nếu ô này khối cũ đã đứng sẵn thì không bấm lại công tắc
            continue
        if x < 0 or x >= width or y < 0 or y >= len(data) // width:
            continue
            
        ch = data[x + y * width]
        soft = ch in ['q', 'w', 'e', 'Q', 'W', 'E']
        heavy = ch in ['a', 's', 'd', 'A', 'S', 'D']

        # Công tắc nặng chỉ kích hoạt khi khối lớn đứng thẳng (không áp dụng cho mảnh phân thân)
        if heavy and (new_block.is_split or not new_block.is_up()): 
            continue

        if soft or heavy:
            if ch in ['q', 'a', 'Q', 'A']: bridges['1'] = not bridges['1']
            elif ch in ['w', 's', 'W', 'S']: bridges['2'] = not bridges['2']
            elif ch in ['e', 'd', 'E', 'D']: bridges['3'] = not bridges['3']

    return bridges

def solve_bfs(terrain):
    tracemalloc.start()
    start_time = time.perf_counter()

    initial_bridges = {'1': False, '2': False, '3': False}
    start_state = SolverState(terrain.start(), initial_bridges)
    goal = terrain.end()

    p = Path()
    p.add(start_state)

    queue = deque([p])
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
        state = path.tail() 
        block = state.block

        expanded += 1

        # Điều kiện thắng: Khối lớn đứng khớp vào ô Đích và không bị tách
        if not block.is_split and block.equals(goal) and block.is_up():
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return state_to_result(path, expanded, start_time, peak)

        next_blocks = []

        # 1. Sinh các bước di chuyển 4 hướng
        for dx, dy in directions:
            try:
                nxt = block.move(dx, dy)
                next_blocks.append(nxt)
            except ValueError:
                continue

        # 2. Sinh hành động ĐỔI MẢNH (Chỉ áp dụng khi khối đang bị tách)
        if block.is_split:
            swapped_block = Block(block.ax, block.ay, block.bx, block.by, 
                                  is_split=True, active_idx=1 - block.active_idx)
            next_blocks.append(swapped_block)          

        # 3. Đánh giá tất cả các khối kế tiếp
        width = terrain.width
        height = len(terrain.arr) // width

        for nxt in next_blocks:
            # Kiểm tra biên bản đồ
            if nxt.ax < 0 or nxt.ax >= width or nxt.ay < 0 or nxt.ay >= height:
                continue
            if nxt.bx < 0 or nxt.bx >= width or nxt.by < 0 or nxt.by >= height:
                continue

            # Xử lý dẫm ô tách khối X khi đang là khối liền đứng thẳng
            if not block.is_split and not nxt.is_split and nxt.is_up():
                idx = nxt.ax + nxt.ay * width
                ch = terrain.arr[idx]
                if ch == 'X': 
                    if width == 10: 
                        nxt = Block(0, 3, 9, 3, is_split=True, active_idx=0)
                    elif width == 15: 
                        nxt = Block(1, 6, 13, 6, is_split=True, active_idx=0)
                    else:
                        nxt = Block(nxt.ax, nxt.ay, nxt.ax + 2, nxt.ay, is_split=True, active_idx=0)

            # Tính toán trạng thái cầu
            current_bridges = state.get_bridges_dict()
            
            # Nếu chỉ đổi mảnh điều khiển (tọa độ giữ nguyên), giữ nguyên trạng thái cầu
            if block.ax == nxt.ax and block.ay == nxt.ay and block.bx == nxt.bx and block.by == nxt.by:
                new_bridges = current_bridges.copy()
            else:
                new_bridges = apply_switches_for_state(block, nxt, current_bridges, terrain)

            # Kiểm tra tính hợp lệ của ô đứng (vực thẳm, ô kính...)
            terrain.bridges = new_bridges
            if not terrain.is_legal(nxt):
                continue

            new_state = SolverState(nxt, new_bridges)

            if new_state in visited:
                continue

            visited.add(new_state)
            new_path = path.clone()
            new_path.add(new_state)
            queue.append(new_path)

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    from bloxorz_go_version import SearchResult
    return SearchResult(None, time.perf_counter() - start_time, expanded, peak)

def solve_dfs(terrain):
    tracemalloc.start()
    start_time = time.perf_counter()

    initial_bridges = {'1': False, '2': False, '3': False}
    start_state = SolverState(terrain.start(), initial_bridges)
    goal = terrain.end()

    p = Path()
    p.add(start_state)

    stack = [p]
    visited = {start_state}
    expanded = 0

    # Thứ tự duyệt 4 hướng thông thường
    directions = [
        (0, -1), # Lên
        (0, 1),  # Xuống
        (-1, 0), # Trái
        (1, 0)   # Phải
    ]

    width = terrain.width
    height = len(terrain.arr) // width

    while stack:
        path = stack.pop()
        state = path.tail()
        block = state.block

        expanded += 1

        # Điều kiện thắng: Khối lớn đứng khớp vào ô Đích và không bị tách
        if not block.is_split and block.equals(goal) and block.is_up():
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return state_to_result(path, expanded, start_time, peak)

        next_blocks = []

        # 1. Sinh hành động ĐỔI MẢNH nếu đang phân thân
        # Trong DFS, ta đẩy hành động đổi mảnh vào trước để nó được xử lý linh hoạt
        if block.is_split:
            swapped_block = Block(block.ax, block.ay, block.bx, block.by, 
                                  is_split=True, active_idx=1 - block.active_idx)
            next_blocks.append(swapped_block)

        # 2. Sinh các bước di chuyển 4 hướng (sử dụng reversed để giữ đúng thứ tự ưu tiên của stack)
        for dx, dy in reversed(directions):
            try:
                nxt = block.move(dx, dy)
                next_blocks.append(nxt)
            except ValueError:
                continue

        # 3. Duyệt và đánh giá các khối kế tiếp kế thừa cấu trúc từ BFS
        for nxt in next_blocks:
            # Kiểm tra biên bản đồ
            if nxt.ax < 0 or nxt.ax >= width or nxt.ay < 0 or nxt.ay >= height:
                continue
            if nxt.bx < 0 or nxt.bx >= width or nxt.by < 0 or nxt.by >= height:
                continue

            # Xử lý dẫm ô tách khối X khi đang là khối liền đứng thẳng
            if not block.is_split and not nxt.is_split and nxt.is_up():
                idx = nxt.ax + nxt.ay * width
                ch = terrain.arr[idx]
                if ch == 'X': 
                    if width == 10: 
                        nxt = Block(0, 3, 9, 3, is_split=True, active_idx=0)
                    elif width == 15: 
                        nxt = Block(1, 6, 13, 6, is_split=True, active_idx=0)
                    else:
                        nxt = Block(nxt.ax, nxt.ay, nxt.ax + 2, nxt.ay, is_split=True, active_idx=0)

            # Tính toán trạng thái cầu tương ứng
            current_bridges = state.get_bridges_dict()
            
            # Nếu chỉ đổi mảnh điều khiển (tọa độ giữ nguyên), giữ nguyên trạng thái cầu
            if block.ax == nxt.ax and block.ay == nxt.ay and block.bx == nxt.bx and block.by == nxt.by:
                new_bridges = current_bridges.copy()
            else:
                new_bridges = apply_switches_for_state(block, nxt, current_bridges, terrain)

            # Kiểm tra tính hợp lệ của ô đứng (vực thẳm, ô kính...)
            terrain.bridges = new_bridges
            if not terrain.is_legal(nxt):
                continue

            new_state = SolverState(nxt, new_bridges)

            if new_state in visited:
                continue

            visited.add(new_state)
            new_path = path.clone()
            new_path.add(new_state)
            stack.append(new_path)

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    from bloxorz_go_version import SearchResult
    return SearchResult(None, time.perf_counter() - start_time, expanded, peak)


def state_to_result(path, expanded, start_time, peak):
    from bloxorz_go_version import SearchResult
    # Không bóc tách block nữa, trả về nguyên vẹn path chứa SolverState
    # GUI từ nay sẽ đọc: step.block để lấy tọa độ và step.bridges để vẽ cầu
    return SearchResult(
        path,
        time.perf_counter() - start_time,
        expanded,
        peak
    )