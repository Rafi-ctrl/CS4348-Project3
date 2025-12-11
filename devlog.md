2025-12-09 21:05 – Initial planning
Read the Project 3 spec. I need to implement an interactive command-line program in Python that manages an index file containing a B-Tree. The index file is divided into 512-byte blocks with a header (magic, root id, next block id) and node blocks (keys, values, child pointers). Commands must include: create, insert, search, load, print, extract. The B-Tree must never have more than three nodes in memory at once.

Plan for this session
- Initialize a local git repository for Project 3.
- Create devlog.md with this initial planning entry.
- Create an empty project3.py file and set up a basic CLI that accepts commands but doesn’t implement them yet.
- Push the initial commit to my GitHub repo (Rafi-ctrl/cs4348-project3).
