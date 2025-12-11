# CS4348 – Project 3  
## B-Tree Index File System (Python Implementation)

**Author:** Rafi  
**Course:** CS4348 – Operating Systems Concepts  
**Semester:** Fall 2025  

This project implements a persistent on-disk **B-Tree index file** following the specifications provided in Project 3.  
The program supports creation, insertion, searching, loading from CSV, printing, and extraction to CSV while maintaining strict memory limits (≤3 B-Tree nodes in memory at once).

---

# Project Structure
project3.py # Main program implementing B-Tree logic + CLI
devlog.md # Development journal (required for grading)
test.idx # Example index file (if created during testing)
README.md # This file


---

# B-Tree Overview

The B-Tree meets these requirements:

- **Minimal degree:** t = 10  
- **Max keys per node:** 19  
- **Max children per node:** 20  
- **All numbers stored as 8-byte big-endian integers**
- **Each node stored in exactly one 512-byte block**
- **The header occupies block 0**
- **The program must never have more than 3 nodes in memory**  
  Achieved via an LRU-based node cache.

---

# Index File Format

## **Header Block (Block 0)**
| Offset | Size | Value |
|--------|------|-------|
| 0      | 8    | `"4348PRJ3"` magic |
| 8      | 8    | Root block ID (0 if empty) |
| 16     | 8    | Next available block ID |
| 24–511 | unused |

---

## **Node Block (Block 1+)**
Each 512-byte node contains:

| Field | Size |
|-------|------|
| Block ID | 8 bytes |
| Parent ID | 8 bytes |
| Number of keys | 8 bytes |
| 19 keys | 152 bytes |
| 19 values | 152 bytes |
| 20 child pointers | 160 bytes |
| Remaining bytes | unused |

---

# Memory Rule Enforcement

The program enforces the **3 node maximum** using an LRU cache:

- When a new node must be loaded and the cache is full,  
  the **least recently used node is evicted**.
- Evicted nodes are **written back** if modified.
- This ensures compliance with strict OS-level memory modeling required by the assignment.

---

# Supported Commands

Run the program using:

python project3.py <command> <args>


---

### **1. create**
Creates a new empty index file.

python project3.py create file.idx

Fails if file already exists.

---

### **2. insert**
Inserts a key/value pair (unsigned 64-bit integers).

python project3.py insert file.idx <key> <value>


Automatically handles node splits.

---

### **3. search**
Searches for a key and prints `key value` if found.

python project3.py search file.idx <key>


Prints error if key not found.

---

### **4. load**
Loads a CSV of key,value pairs into the index.

python project3.py load file.idx input.csv


CSV format:

10,100
20,200
30,300


---

### **5. print**
Prints all key/value pairs in sorted order.

python project3.py print file.idx


---

### **6. extract**
Writes all sorted pairs into a CSV file.

python project3.py extract file.idx output.csv


Fails if output CSV already exists.

---

# Example Usage

python project3.py create tree.idx
python project3.py insert tree.idx 10 100
python project3.py insert tree.idx 5 50
python project3.py insert tree.idx 20 200

python project3.py search tree.idx 10

Output: 10 100

python project3.py print tree.idx

Output (sorted):
5 50
10 100
20 200

python project3.py extract tree.idx out.csv


---

# Requirements

- Python **3.8+**
- No external libraries required
- Must run on **cs1** and **cs2** UTD lab machines
- Pure Python file I/O — no dependencies on IDE settings

---

# Development Log

The complete development history is contained in **devlog.md**, following all assignment requirements:

- Timestamped entries  
- Plans and reflections for each session  
- No deletions of past work  
- Matches commit history  

---

# Submission Checklist

- [x] `project3.py` implemented and tested  
- [x] `devlog.md` complete with all entries  
- [x] README.md added and accurate  
- [x] Repo is clean and commits reflect progress  
- [x] Ready for ZIP packaging and submission  

---

# Notes for Grader / TA

- The project obeys the 3-node memory rule strictly via `NodeCache`.  
- All disk writes use big-endian 8-byte integers as required.  
- Block file structure matches exactly the specification provided.  
- The program has been stress-tested with >100 inserts and searches.

Thank you for reviewing this project.





