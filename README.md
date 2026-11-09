# CSA08-1921260102-Assignment3

**Name:** DHARSHIDHA S  **Register number:** 1911260095
**Course:** Python Programming - Assignment 3 (CO3): lists, tuples, dictionaries, sets, copying, list comprehension

## Environment
- Python 3.12 (programs use the standard library only)
- `requirements.txt`: matplotlib and reportlab (only to draw graphs and build the PDF report)

## Folders and how to run each program
| Task | Folder | Command (run inside the folder) | Result in one line |
|---|---|---|---|
| Q1 Lists and slicing | `Q1` | `python rainfall.py` | weekly totals, wettest/driest week, dry days; running-sum moving average ~3x faster than naive (matches 6(n-6) vs 2n-8 additions) |
| Q2 Tuples, copying | `Q2` | `python complete_the_code.py` and `python bus_stops.py` | shared-row bug shown with `is`/`id()`; deepcopy fixes it; tuple and list creation/indexing speed is about equal |
| Q3 Dictionaries | `Q3` | `python complete_the_code.py` and `python complaints.py` | output `[('seeds', 3), ('price', 2), ('received', 2)]`; dict and Counter are O(n), `list.count` is O(n*d) |
| Q4 Sets | `Q4` | `python complete_the_code.py` and `python electives.py` | clash/exactly-one/neither match the expected output; set lookup is thousands of times faster than list lookup |
| Q5 List comprehension | `Q5` | `python sensors.py` | three versions give identical results; generator uses about 200 bytes instead of megabytes |
| Q6 Nested data | `Q6` | `python railway.py` | station index answers queries several times faster than scanning, at the cost of extra memory |
| Q7 Contact merging | `Q7` | `python contacts.py` | dictionary design is O(n); pairwise comparison is O(n^2) |

Run everything and rebuild the PDFs:

    python run_all.py
    python build_report.py --github https://github.com/<your-username>/CSA08-1921260102-Assignment3

Each program prints its evidence (outputs, tables of timings, edge-case tests), checks itself with `assert`,
and saves `results.json`, which the report reads. Output screenshots are in each folder's `screenshots/`.
