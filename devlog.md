## 2025-12-09 21:05 – Initial planning
- Read the Project 3 specification thoroughly. The project requires implementing a persistent on-disk B-Tree stored in 512-byte blocks, consisting of a file header, node blocks, and strict memory constraints (max 3 nodes in memory).
- Identified the required user commands: `create`, `insert`, `search`, `load`, `print`, and `extract`.
- Understood key challenges: B-Tree splitting logic, big-endian encoding, fixed block layout, node serialization, and cache enforcement.
- Decided to implement the entire solution in Python for easier byte manipulation and file I/O.
- Sketched the structure:
  - `BTreeNode` for encoding/decoding
  - `NodeCache` for enforcing 3-node memory limit
  - `BTreeFile` for header management, splitting, traversal, and IO
  - CLI handling for all commands
- Created local Git repo and added initial `devlog.md`.

**Plan for this session**
- Connect repository to GitHub.
- Create initial project skeleton (`project3.py`) and CLI stubs.
- Begin implementing header and node structures.
- Commit devlog and base project files.

---

## 2025-12-09 22:40 – Work session
- Successfully connected repo to GitHub (`CS4348-Project3`) after resolving incorrect remote URL issues.
- Created starter `project3.py` with placeholder command handlers.
- Implemented:
  - Header creation (`MAGIC`, root id, next block id).
  - Full node encoding/decoding with exact byte alignment.
  - LRU-based `NodeCache` enforcing the 3-node memory rule.
  - Basic B-Tree header loading and block allocation logic.
- Verified that block reads/writes behave as expected.

**Work performed**
- Completed `BTreeNode.encode()` / `decode()` using big-endian formatting.
- Implemented LRU eviction + auto-flush in `NodeCache`.
- Created `allocate_node()` and basic file initialization logic.
- Built initial `search()` traversal method.

**Issues & fixes**
- Git unexpectedly opened Vim for commit messages; resolved using `ESC :wq ENTER`.
- Fixed GitHub remote case-sensitivity issues (`cs4348` vs `CS4348`).

**Next session**
- Finish insert logic (splitting, recursive non-full insert).
- Implement all CLI commands.
- Test with sample index files.

---

## 2025-12-10 16:30 – Implementation session
- Completed full B-Tree insertion: root splitting, internal node splitting, child redistribution.
- Finalized `search()`, `_insert_nonfull()`, `_split_child()`, and traversal logic.
- Implemented all required commands: `create`, `insert`, `search`, `load`, `print`, `extract`.
- Added in-order traversal for sorted printing and CSV export.
- Performed multiple tests using random inserts and sequential inserts.

**Work performed**
- Finished `_split_child()` and updated moved child-parent relationships.
- Completed `NodeCache` integration with every write.
- Implemented `cmd_print` and `cmd_extract`.
- Tested the entire system using a previously created index file; results matched expectations.

**Issues & fixes**
- Adjusted decode trimming so node.children = count+1 to match B-Tree rule.
- Ensured flushing on close updates all dirty blocks.
- Fixed partially implemented print command.

**Results**
- Entire B-Tree system (persistent on-disk structure) now operational.
- Functional commands: create, insert, search, load, print, extract.
- Confident the implementation aligns with project specifications.

**Next session**
- Write README.
- Perform stress testing.
- Prepare final submission zip.

---

## 2025-12-10 21:40 – Reflection session (final for today)
- Conducted end-to-end testing: created index file, inserted data, searched keys, printed data, and extracted CSV.
- Verified LRU node cache properly respects the 3-node memory limit.
- Commit history and devlog accurately document all phases of development.
- Code is stable and fully matches the project requirements.

**Results**
- Fully working Project 3 implementation.
- Clean repository and traceable development process.

**Next steps**
- Write README.md explaining usage and file structure.
- Perform additional scaling tests.
- Zip repo for submission.
