#!/usr/bin/env python3
import sys
import os
import struct
import csv
from collections import OrderedDict

BLOCK_SIZE = 512
MAGIC = b"4348PRJ3"  # 8 bytes


# -------------------------
# B-Tree node (on-disk layout)
# -------------------------

class BTreeNode:
    T = 10                       # minimal degree
    MAX_KEYS = 2 * T - 1         # 19
    MAX_CHILDREN = 2 * T         # 20

    def __init__(self, block_id, parent_id, keys=None, values=None, children=None):
        self.block_id = block_id
        self.parent_id = parent_id
        self.keys = keys or []
        self.values = values or []
        self.children = children or []
        self.dirty = True        # needs to be written back

    @property
    def count(self):
        return len(self.keys)

    def is_leaf(self):
        # Leaf if there are no non-zero children
        return not any(self.children)

    def encode(self):
        """Serialize node into a 512-byte block."""
        if len(self.keys) != len(self.values):
            raise ValueError("keys/values length mismatch")
        if len(self.keys) > self.MAX_KEYS:
            raise ValueError("too many keys")
        if len(self.children) > self.MAX_CHILDREN:
            raise ValueError("too many children")

        # pad arrays
        keys = self.keys + [0] * (self.MAX_KEYS - len(self.keys))
        values = self.values + [0] * (self.MAX_KEYS - len(self.values))
        children = self.children + [0] * (self.MAX_CHILDREN - len(self.children))

        buf = bytearray(BLOCK_SIZE)
        buf[0:8] = struct.pack(">Q", self.block_id)
        buf[8:16] = struct.pack(">Q", self.parent_id)
        buf[16:24] = struct.pack(">Q", self.count)

        offset = 24
        # keys
        for k in keys:
            buf[offset:offset + 8] = struct.pack(">Q", k)
            offset += 8
        # values
        for v in values:
            buf[offset:offset + 8] = struct.pack(">Q", v)
            offset += 8
        # children
        for c in children:
            buf[offset:offset + 8] = struct.pack(">Q", c)
            offset += 8

        return bytes(buf)

    @classmethod
    def decode(cls, block_id, data):
        """Deserialize node from a 512-byte block."""
        if len(data) != BLOCK_SIZE:
            raise ValueError("bad block size")
        b_id = struct.unpack(">Q", data[0:8])[0]
        parent_id = struct.unpack(">Q", data[8:16])[0]
        count = struct.unpack(">Q", data[16:24])[0]

        keys = []
        values = []
        children = []

        offset = 24
        for _ in range(cls.MAX_KEYS):
            keys.append(struct.unpack(">Q", data[offset:offset + 8])[0])
            offset += 8
        for _ in range(cls.MAX_KEYS):
            values.append(struct.unpack(">Q", data[offset:offset + 8])[0])
            offset += 8
        for _ in range(cls.MAX_CHILDREN):
            children.append(struct.unpack(">Q", data[offset:offset + 8])[0])
            offset += 8

        node = cls(b_id, parent_id, keys[:count], values[:count], children[:count + 1])
        node.dirty = False
        return node


# -------------------------
# Node cache (max 3 nodes in memory)
# -------------------------

class NodeCache:
    def __init__(self, f, max_nodes=3):
        self.f = f
        self.max_nodes = max_nodes
        self.cache = OrderedDict()   # block_id -> node

    def _read_block(self, block_id):
        self.f.seek(block_id * BLOCK_SIZE)
        data = self.f.read(BLOCK_SIZE)
        if len(data) != BLOCK_SIZE:
            raise IOError(f"Failed to read block {block_id}")
        return data

    def _write_block(self, block_id, data):
        if len(data) != BLOCK_SIZE:
            raise ValueError("bad block size for write")
        self.f.seek(block_id * BLOCK_SIZE)
        self.f.write(data)

    def get(self, block_id):
        """Get node from cache or load from disk."""
        node = self.cache.get(block_id)
        if node is not None:
            self.cache.move_to_end(block_id)
            return node

        # possibly evict LRU
        if len(self.cache) >= self.max_nodes:
            old_block_id, old_node = self.cache.popitem(last=False)
            if old_node.dirty:
                self._write_block(old_block_id, old_node.encode())

        data = self._read_block(block_id)
        node = BTreeNode.decode(block_id, data)
        self.cache[block_id] = node
        return node

    def mark_dirty(self, node):
        node.dirty = True
        self.cache[node.block_id] = node
        self.cache.move_to_end(node.block_id)

    def flush_all(self):
        for bid, node in self.cache.items():
            if node.dirty:
                self._write_block(bid, node.encode())
        self.cache.clear()


# -------------------------
# B-Tree file wrapper
# -------------------------

class BTreeFile:
    def __init__(self, path, mode='r+b', create=False):
        self.path = path

        if create:
            if os.path.exists(path):
                raise FileExistsError("Index file already exists")
            self.f = open(path, 'w+b')
            header = bytearray(BLOCK_SIZE)
            header[0:8] = MAGIC
            header[8:16] = struct.pack(">Q", 0)  # root id
            header[16:24] = struct.pack(">Q", 1)  # next block id (first node)
            self.f.write(header)
            self.f.flush()
        else:
            if not os.path.exists(path):
                raise FileNotFoundError("Index file missing")
            self.f = open(path, mode)
            header = self.f.read(BLOCK_SIZE)
            if len(header) != BLOCK_SIZE or header[0:8] != MAGIC:
                raise ValueError("Invalid index file")

        self._load_header()
        self.cache = NodeCache(self.f, max_nodes=3)

    def _load_header(self):
        self.f.seek(0)
        header = self.f.read(BLOCK_SIZE)
        self.root_id = struct.unpack(">Q", header[8:16])[0]
        self.next_block_id = struct.unpack(">Q", header[16:24])[0]

    def _write_header(self):
        header = bytearray(BLOCK_SIZE)
        header[0:8] = MAGIC
        header[8:16] = struct.pack(">Q", self.root_id)
        header[16:24] = struct.pack(">Q", self.next_block_id)
        self.f.seek(0)
        self.f.write(header)
        self.f.flush()

    def close(self):
        self.cache.flush_all()
        self._write_header()
        self.f.close()

    def allocate_node(self, parent_id):
        block_id = self.next_block_id
        self.next_block_id += 1
        # start as a leaf: one dummy child 0
        node = BTreeNode(block_id, parent_id, [], [], [0])
        self.cache.mark_dirty(node)
        return node

    def get_node(self, block_id):
        return self.cache.get(block_id)

    # ---- search ----

    def search(self, key):
        if self.root_id == 0:
            return None
        return self._search_node(self.root_id, key)

    def _search_node(self, block_id, key):
        node = self.get_node(block_id)
        i = 0
        while i < node.count and key > node.keys[i]:
            i += 1
        if i < node.count and key == node.keys[i]:
            return node.values[i]
        if node.is_leaf():
            return None
        child_id = node.children[i]
        if child_id == 0:
            return None
        return self._search_node(child_id, key)

    # ---- insert ----

    def insert(self, key, value):
        # ensure unsigned 64-bit range
        if not (0 <= key <= 2**64 - 1 and 0 <= value <= 2**64 - 1):
            raise ValueError("Key/value out of range")

        if self.root_id == 0:
            root = self.allocate_node(parent_id=0)
            root.keys = [key]
            root.values = [value]
            root.children = [0, 0]
            self.cache.mark_dirty(root)
            self.root_id = root.block_id
            return

        root = self.get_node(self.root_id)
        if root.count == BTreeNode.MAX_KEYS:
            # split full root
            new_root = self.allocate_node(parent_id=0)
            new_root.children = [root.block_id]
            root.parent_id = new_root.block_id
            self.cache.mark_dirty(root)
            self.root_id = new_root.block_id
            self._split_child(new_root, 0, root)
            self._insert_nonfull(new_root, key, value)
        else:
            self._insert_nonfull(root, key, value)

    def _split_child(self, parent, index, full_child):
        t = BTreeNode.T
        new_node = self.allocate_node(parent_id=parent.block_id)

        median_key = full_child.keys[t - 1]
        median_val = full_child.values[t - 1]

        # keys/values for new node
        new_node.keys = full_child.keys[t:]
        new_node.values = full_child.values[t:]

        if full_child.is_leaf():
            new_node.children = [0] * (len(new_node.keys) + 1)
        else:
            new_node.children = full_child.children[t:]
            full_child.children = full_child.children[:t]
            # update parent id for moved children
            for child_id in new_node.children:
                if child_id != 0:
                    child = self.get_node(child_id)
                    child.parent_id = new_node.block_id
                    self.cache.mark_dirty(child)

        # shrink full_child
        full_child.keys = full_child.keys[:t - 1]
        full_child.values = full_child.values[:t - 1]

        # insert median into parent
        parent.keys.insert(index, median_key)
        parent.values.insert(index, median_val)
        parent.children.insert(index + 1, new_node.block_id)

        self.cache.mark_dirty(parent)
        self.cache.mark_dirty(full_child)
        self.cache.mark_dirty(new_node)

    def _insert_nonfull(self, node, key, value):
        # find first index where key <= node.keys[i]
        i = 0
        while i < node.count and key > node.keys[i]:
            i += 1

        # key already exists: update value
        if i < node.count and key == node.keys[i]:
            node.values[i] = value
            self.cache.mark_dirty(node)
            return

        if node.is_leaf():
            # insert at position i
            node.keys.insert(i, key)
            node.values.insert(i, value)
            self.cache.mark_dirty(node)
        else:
            child_id = node.children[i]
            child = self.get_node(child_id)
            if child.count == BTreeNode.MAX_KEYS:
                self._split_child(node, i, child)
                # after split, decide which child to descend into
                if key > node.keys[i]:
                    i += 1
                elif key == node.keys[i]:
                    node.values[i] = value
                    self.cache.mark_dirty(node)
                    return
                child_id = node.children[i]
                child = self.get_node(child_id)
            self._insert_nonfull(child, key, value)

    # ---- traversal ----

    def inorder_traverse(self, out_func):
        if self.root_id == 0:
            return
        self._inorder_node(self.root_id, out_func)

    def _inorder_node(self, block_id, out_func):
        node = self.get_node(block_id)
        for i in range(node.count):
            if not node.is_leaf():
                child_id = node.children[i]
                if child_id != 0:
                    self._inorder_node(child_id, out_func)
            out_func(node.keys[i], node.values[i])
        if not node.is_leaf():
            last_child = node.children[node.count]
            if last_child != 0:
                self._inorder_node(last_child, out_func)


# -------------------------
# Command implementations
# -------------------------

def cmd_create(idx_path):
    if os.path.exists(idx_path):
        raise RuntimeError("Index already exists")
    bt = BTreeFile(idx_path, create=True)
    bt.close()


def cmd_insert(idx_path, key_str, value_str):
    key = int(key_str)
    value = int(value_str)
    bt = BTreeFile(idx_path)
    try:
        bt.insert(key, value)
    finally:
        bt.close()


def cmd_search(idx_path, key_str):
    key = int(key_str)
    bt = BTreeFile(idx_path)
    try:
        val = bt.search(key)
    finally:
        bt.close()
    if val is None:
        raise RuntimeError("Key not found")
    print(f"{key} {val}")


def cmd_load(idx_path, csv_path):
    bt = BTreeFile(idx_path)
    try:
        with open(csv_path, "r", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                if len(row) != 2:
                    raise RuntimeError("Bad CSV row")
                key = int(row[0].strip())
                value = int(row[1].strip())
                bt.insert(key, value)
    finally:
        bt.close()


def cmd_print(idx_path):
    bt = BTreeFile(idx_pa_
