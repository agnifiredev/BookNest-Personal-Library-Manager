# BookNest – Personal Library Manager

A college APP mini project built with **Python, Tkinter, and SQLite**. Runs offline.

## Requirements
- Python 3.9 or newer
- Tkinter (included with most Windows/macOS Python installations; Linux may require `sudo apt install python3-tk`)
- No pip dependencies

## Run
```bash
python booknest.py
```
On macOS/Linux, use `python3 booknest.py` if necessary.

## Test
```bash
python -m unittest -v
```

## Features
- Add, edit, and delete books
- Search by title, author, or genre; filter by reading status
- Track current page, total pages, and reading status
- Dashboard with total books, reading, completed, and completion rate
- SQLite persistence in `booknest.db` (created automatically)
- Export all books to CSV
- Load demo books when library is empty

## Important
GitHub hosts the source files; Tkinter requires a local desktop display and cannot run as a GitHub Pages website.

## Demo data
Click **Load Demo Books** on a fresh database to see five sample books.

## Student project
APP / Advanced Programming Practice – Python + Tkinter Mini Project.
