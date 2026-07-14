from collections import deque

# ==========================================
# 1. BLOCK (Tương đương block.go)
# ==========================================
class Block:
    def __init__(self, ax, ay, bx, by):
        self.ax = ax
        self.ay = ay
        self.bx = bx
        self.by = by

    @classmethod
    def new_block_down(cls, ax, ay, bx, by):
        """Tạo khối lập phương nằm ngang/dọc"""
        return cls(ax, ay, bx, by)

    @classmethod
    def new_block_up(cls, x, y):
        """Tạo khối lập phương đứng"""
        return cls(x, y, x, y)

    def is_up(self):
        """Kiểm tra xem khối có đang đứng không"""
        return self.ax == self.bx and self.ay == self.by

    def move(self, dx, dy):
        """Tạo một khối mới di chuyển tương đối so với khối hiện tại"""
        if self.is_up():
            if dx == 1 or dy == 1:
                # Đổ về Đông (East) hoặc Nam (South)
                return Block.new_block_down(self.ax + dx, self.ay + dy, 
                                            self.bx + 2*dx, self.by + 2*dy)
            # Đổ về Tây (West) hoặc Bắc (North)
            return Block.new_block_down(self.ax + 2*dx, self.ay + 2*dy, 
                                        self.bx + dx, self.by + dy)

        # Khối đang nằm
        is_north_south = (self.ax == self.bx)

        if (is_north_south and dy == 0) or (not is_north_south and dx == 0):
            # Lăn ngang thân (Roll)
            return Block.new_block_down(self.ax + dx, self.ay + dy, 
                                        self.bx + dx, self.by + dy)

        if (is_north_south and dy == -1) or (not is_north_south and dx == -1):
            # Dựng đứng lên hướng Bắc hoặc Tây
            return Block.new_block_up(self.ax + dx, self.ay + dy)

        if (is_north_south and dy == 1) or (not is_north_south and dx == 1):
            # Dựng đứng lên hướng Nam hoặc Đông
            return Block.new_block_up(self.bx + dx, self.by + dy)

        raise ValueError(f"Block.move: unreachable {self} {dx} {dy}")

    def equals(self, other):
        """So sánh 2 khối có trùng vị trí không"""
        return (self.ax == other.ax and self.ay == other.ay and 
                self.bx == other.bx and self.by == other.by)

    def __str__(self):
        """In thông tin tọa độ khối (String representation)"""
        if self.is_up():
            return f"({self.ax}, {self.ay})"
        return f"({self.ax}, {self.ay})-({self.bx}, {self.by})"


# ==========================================
# 2. PATH (Tương đương path.go)
# ==========================================
class Path:
    def __init__(self, blocks=None):
        self.blocks = blocks if blocks is not None else []

    def contains(self, b):
        """Kiểm tra đường đi hiện tại đã đi qua khối này chưa"""
        for block in self.blocks:
            if block.equals(b):
                return True
        return False

    def add(self, b):
        """Thêm một bước (Block) vào đường đi"""
        self.blocks.append(b)

    def tail(self):
        """Lấy khối cuối cùng trong đường đi (vị trí hiện tại)"""
        if not self.blocks:
            return None
        return self.blocks[-1]

    def clone(self):
        """Nhân bản (Deep copy) đường đi hiện tại"""
        return Path(list(self.blocks))

    def __len__(self):
        return len(self.blocks)

    def __str__(self):
        return "[" + "; ".join(str(b) for b in self.blocks) + "]"


# ==========================================
# 3. TERRAIN (Tương đương terrain.go)
# ==========================================
class ArrayTerrain:
    def __init__(self, start, end, arr, width):
        self._start = start
        self._end = end
        self.arr = arr # Chuỗi string 1 chiều (Giống mảng []byte trong Go)
        self.width = width

    def is_legal(self, b):
        """Kiểm tra khối có hợp lệ (không rớt khỏi mảng và không chạm '.')"""
        if (b.ax < 0 or b.ay < 0 or b.bx < 0 or b.by < 0 or
            b.ax >= self.width or b.bx >= self.width or
            b.ay * self.width >= len(self.arr) or b.by * self.width >= len(self.arr)):
            return False

        square_a = self.arr[b.ax + self.width * b.ay]
        square_b = self.arr[b.bx + self.width * b.by]

        return square_a != '.' and square_b != '.'

    def start(self):
        return self._start

    def end(self):
        return self._end

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
def solve(terrain):
    """
    Thuật toán giải BFS.
    Thay vì dùng Channel (chan) của Go, hàm này sẽ return ngay Path tối ưu đầu tiên tìm được.
    """
    queue = deque()
    path = Path()
    start_block = terrain.start()
    
    path.add(start_block)
    queue.append(path)
    
    return solve_iter(terrain, queue)

def solve_iter(terrain, queue):
    while queue:
        # Lấy Path đầu tiên ra khỏi Queue
        path = queue.popleft()
        
        # Lấy khối cuối cùng của Path đó (vị trí hiện tại)
        block = path.tail()

        # 4 hướng: Lên, Xuống, Trái, Phải
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

        for dx, dy in directions:
            neighbour = block.move(dx, dy)

            # Code gốc của Go chỉ check visited trên CÙNG 1 path hiện tại
            visited = path.contains(neighbour)
            
            if not visited and terrain.is_legal(neighbour):
                new_path = path.clone()
                new_path.add(neighbour)
                queue.append(new_path)
                
                # Tìm thấy lời giải
                if neighbour.equals(terrain.end()):
                    return new_path

    # Không tìm thấy đường đi
    return None


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

def test_solvable_terrain(terrain, name):
    solution = solve(terrain)
    if solution:
        print(f"{name} first solution in {len(solution)-1} moves: {solution}")
    else:
        print(f"{name} has no solution")

if __name__ == "__main__":
    print("--- Chạy thử các Terrain gốc từ tác giả Go ---")
    
    # Test Terrain 1
    test_solvable_terrain(build_terrain_1(), "terrain1")
    
    # Test Terrain 2
    test_solvable_terrain(build_terrain_2(), "terrain2")
    
    # Test Unsolvable Terrain
    test_solvable_terrain(build_unsolvable_terrain(), "unsolvable terrain")
    
    # Test Infinite Terrain
    start = Block.new_block_up(0, 0)
    end = Block.new_block_up(5, 1)
    test_solvable_terrain(InfiniteTerrain(start, end), "infinite")