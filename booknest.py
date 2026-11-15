"""BookNest - Personal Library Manager | Python 3.9+ | Tkinter + SQLite."""
import csv
import sqlite3
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

DB_PATH = Path(__file__).with_name('booknest.db')
STATUSES = ('To Read', 'Reading', 'Completed')
COLORS = {'bg':'#0b1220','panel':'#172238','panel2':'#202f49','text':'#f3f6ff','muted':'#a6b6ce','accent':'#8b83ff','green':'#48d6aa','yellow':'#ffc778'}


def completion_percentage(completed, total):
    """Return percentage of books completed, safe for empty libraries."""
    return round(completed / total * 100, 1) if total > 0 else 0.0


def validate_book(title, author, pages, current_page, status):
    title, author = title.strip(), author.strip()
    if not title or not author:
        raise ValueError('Book title and author are required.')
    try:
        pages, current_page = int(pages), int(current_page)
    except (ValueError, TypeError):
        raise ValueError('Total pages and current page must be whole numbers.') from None
    if pages <= 0 or current_page < 0 or current_page > pages:
        raise ValueError('Pages must be positive, with current page between 0 and total pages.')
    if status not in STATUSES:
        raise ValueError('Please choose a valid reading status.')
    if status == 'Completed' and current_page != pages:
        raise ValueError('Completed books must have current page equal to total pages.')
    if status == 'To Read' and current_page != 0:
        raise ValueError('To Read books must start at page 0.')
    return title, author, pages, current_page


class LibraryDB:
    def __init__(self, path=DB_PATH):
        self.connection = sqlite3.connect(str(path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute('''CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, author TEXT NOT NULL,
            genre TEXT NOT NULL DEFAULT 'General',
            total_pages INTEGER NOT NULL CHECK(total_pages > 0),
            current_page INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'To Read',
            created_at TEXT NOT NULL)''')
        self.connection.commit()

    def add(self, title, author, genre, pages, current_page, status):
        title, author, pages, current_page = validate_book(title, author, pages, current_page, status)
        with self.connection:
            self.connection.execute('''INSERT INTO books(title,author,genre,total_pages,current_page,status,created_at)
                VALUES (?,?,?,?,?,?,?)''', (title, author, genre.strip() or 'General', pages, current_page, status, datetime.now().isoformat(timespec='seconds')))

    def update(self, book_id, title, author, genre, pages, current_page, status):
        title, author, pages, current_page = validate_book(title, author, pages, current_page, status)
        with self.connection:
            self.connection.execute('''UPDATE books SET title=?,author=?,genre=?,total_pages=?,current_page=?,status=? WHERE id=?''',
                                    (title, author, genre.strip() or 'General', pages, current_page, status, book_id))

    def delete(self, book_id):
        with self.connection:
            self.connection.execute('DELETE FROM books WHERE id=?', (book_id,))

    def all(self, search='', status='All'):
        sql = 'SELECT * FROM books WHERE (title LIKE ? OR author LIKE ? OR genre LIKE ?)'
        params = ['%' + search + '%'] * 3
        if status != 'All':
            sql += ' AND status=?'
            params.append(status)
        sql += ' ORDER BY id DESC'
        return self.connection.execute(sql, params).fetchall()

    def summary(self):
        result = self.connection.execute('''SELECT COUNT(*) AS total,
            COALESCE(SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END),0) AS completed,
            COALESCE(SUM(CASE WHEN status='Reading' THEN 1 ELSE 0 END),0) AS reading,
            COALESCE(SUM(current_page),0) AS pages_read FROM books''').fetchone()
        return dict(result)

    def close(self):
        self.connection.close()


class BookNestApp(tk.Tk):
    def __init__(self, db_path=DB_PATH):
        super().__init__()
        self.db = LibraryDB(db_path)
        self.selected_id = None
        self.title('BookNest  |  Personal Library Manager')
        self.geometry('1180x760')
        self.minsize(960, 650)
        self.configure(bg=COLORS['bg'])
        self._style()
        self._build()
        self.refresh()
        self.protocol('WM_DELETE_WINDOW', self._quit)

    def _style(self):
        s = ttk.Style(self)
        s.theme_use('clam')
        s.configure('Treeview', background=COLORS['panel'], foreground=COLORS['text'], fieldbackground=COLORS['panel'], rowheight=34, borderwidth=0, font=('Arial', 10))
        s.configure('Treeview.Heading', background=COLORS['panel2'], foreground=COLORS['text'], font=('Arial', 10, 'bold'), padding=10)
        s.map('Treeview', background=[('selected', '#4c498c')])
        s.configure('TCombobox', padding=5)
        s.configure('Horizontal.TProgressbar', troughcolor=COLORS['panel2'], background=COLORS['green'])

    def _label(self, parent, text, size=11, color='text', bold=False, **kwargs):
        return tk.Label(parent, text=text, bg=parent.cget('bg'), fg=COLORS.get(color, color), font=('Arial', size, 'bold' if bold else 'normal'), **kwargs)

    def _button(self, parent, text, command, color='accent'):
        return tk.Button(parent, text=text, command=command, bg=COLORS[color], fg='#0b1220', activebackground='#b2abff', font=('Arial', 10, 'bold'), relief='flat', padx=14, pady=9, cursor='hand2')

    def _entry(self, parent, variable, width=20):
        return tk.Entry(parent, textvariable=variable, bg=COLORS['panel2'], fg=COLORS['text'], insertbackground=COLORS['text'], relief='flat', font=('Arial', 11), width=width, highlightthickness=1, highlightbackground='#33435c')

    def _build(self):
        header = tk.Frame(self, bg=COLORS['bg'], padx=30, pady=22)
        header.pack(fill='x')
        self._label(header, 'BookNest', 27, bold=True).pack(anchor='w')
        self._label(header, 'Your personal reading space  •  Organize, read, achieve', 11, 'muted').pack(anchor='w', pady=(4,0))
        self.cards = tk.Frame(self, bg=COLORS['bg'], padx=30)
        self.cards.pack(fill='x')
        self.stats = {}
        for key, label, color in [('total','TOTAL BOOKS','accent'),('reading','CURRENTLY READING','yellow'),('completed','COMPLETED','green'),('progress','COMPLETION RATE','accent')]:
            card = tk.Frame(self.cards, bg=COLORS['panel'], padx=18, pady=16)
            card.pack(side='left', fill='x', expand=True, padx=(0,12))
            self._label(card, label, 9, 'muted', bold=True).pack(anchor='w')
            value = tk.Label(card, text='0', bg=COLORS['panel'], fg=COLORS[color], font=('Arial', 27, 'bold'))
            value.pack(anchor='w', pady=(8,0))
            self.stats[key] = value
        main = tk.Frame(self, bg=COLORS['bg'], padx=30, pady=20)
        main.pack(fill='both', expand=True)
        left = tk.Frame(main, bg=COLORS['panel'], padx=18, pady=16, width=320)
        left.pack(side='left', fill='y', padx=(0,18))
        left.pack_propagate(False)
        self._label(left, 'BOOK DETAILS', 13, bold=True).pack(anchor='w', pady=(0,12))
        self.vars = {k: tk.StringVar(value=v) for k,v in [('title',''),('author',''),('genre','Fiction'),('pages','200'),('current','0'),('status','To Read')]}
        for key, caption in [('title','Book title'),('author','Author'),('genre','Genre'),('pages','Total pages'),('current','Current page'),('status','Reading status')]:
            self._label(left, caption, 10, 'muted').pack(anchor='w', pady=(9,4))
            if key == 'status':
                ttk.Combobox(left, textvariable=self.vars[key], values=STATUSES, state='readonly', width=25).pack(fill='x')
            else:
                self._entry(left, self.vars[key]).pack(fill='x', ipady=7)
        self._button(left, '+ Add Book', self.add_book).pack(fill='x', pady=(20,7))
        self._button(left, 'Update Selected', self.update_book, 'green').pack(fill='x', pady=5)
        self._button(left, 'Clear Form', self.clear_form, 'yellow').pack(fill='x', pady=5)
        right = tk.Frame(main, bg=COLORS['panel'], padx=18, pady=16)
        right.pack(side='left', fill='both', expand=True)
        self._label(right, 'MY LIBRARY', 13, bold=True).pack(anchor='w')
        controls = tk.Frame(right, bg=COLORS['panel'])
        controls.pack(fill='x', pady=(14,12))
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', lambda *_: self.refresh_table())
        self._entry(controls, self.search_var, 22).pack(side='left', ipady=7, padx=(0,10))
        self.filter_var = tk.StringVar(value='All')
        filt = ttk.Combobox(controls, textvariable=self.filter_var, values=('All',)+STATUSES, state='readonly', width=13)
        filt.pack(side='left')
        filt.bind('<<ComboboxSelected>>', lambda *_: self.refresh_table())
        columns = ('title','author','genre','status','pages')
        self.tree = ttk.Treeview(right, columns=columns, show='headings', selectmode='browse')
        for key, heading, width in [('title','TITLE',180),('author','AUTHOR',120),('genre','GENRE',90),('status','STATUS',100),('pages','PROGRESS',100)]:
            self.tree.heading(key, text=heading)
            self.tree.column(key, width=width, minwidth=65, stretch=True)
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.select_book)
        bottom = tk.Frame(right, bg=COLORS['panel'])
        bottom.pack(fill='x', pady=(14,0))
        self._button(bottom, 'Delete Selected', self.delete_book, 'yellow').pack(side='left')
        self._button(bottom, 'Export CSV', self.export_csv, 'green').pack(side='left', padx=10)
        self._button(bottom, 'Load Demo Books', self.load_demo).pack(side='left')
        self._label(self, 'BOOKNEST  •  PYTHON + TKINTER + SQLITE  |  OFFLINE DESKTOP APP', 9, 'muted').pack(pady=(0,12))

    def _values(self):
        return tuple(self.vars[k].get() for k in ('title','author','genre','pages','current','status'))

    def add_book(self):
        try:
            self.db.add(*self._values())
        except ValueError as exc:
            messagebox.showerror('Invalid book details', str(exc))
            return
        self.clear_form()
        self.refresh()

    def update_book(self):
        if self.selected_id is None:
            messagebox.showinfo('Select a book', 'Choose a book from the table first.')
            return
        try:
            self.db.update(self.selected_id, *self._values())
        except ValueError as exc:
            messagebox.showerror('Invalid book details', str(exc))
            return
        self.clear_form()
        self.refresh()

    def delete_book(self):
        if self.selected_id is None:
            messagebox.showinfo('Select a book', 'Choose a book from the table first.')
            return
        if messagebox.askyesno('Delete book', 'Remove the selected book from your library?'):
            self.db.delete(self.selected_id)
            self.clear_form()
            self.refresh()

    def select_book(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return
        self.selected_id = int(selection[0])
        row = self.db.connection.execute('SELECT * FROM books WHERE id=?', (self.selected_id,)).fetchone()
        if row:
            for key, field in [('title','title'),('author','author'),('genre','genre'),('pages','total_pages'),('current','current_page'),('status','status')]:
                self.vars[key].set(str(row[field]))

    def clear_form(self):
        self.selected_id = None
        for key, value in [('title',''),('author',''),('genre','Fiction'),('pages','200'),('current','0'),('status','To Read')]:
            self.vars[key].set(value)
        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for book in self.db.all(self.search_var.get().strip(), self.filter_var.get()):
            pages = f"{book['current_page']}/{book['total_pages']}"
            self.tree.insert('', 'end', iid=str(book['id']), values=(book['title'],book['author'],book['genre'],book['status'],pages))

    def refresh(self):
        s = self.db.summary()
        for key in ('total','reading','completed'):
            self.stats[key].config(text=str(s[key]))
        self.stats['progress'].config(text=f"{completion_percentage(s['completed'], s['total'])}%")
        self.refresh_table()

    def export_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files','*.csv')], initialfile='booknest_library.csv')
        if not filename:
            return
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Title','Author','Genre','Total Pages','Current Page','Status'])
            for b in self.db.all():
                writer.writerow([b['title'],b['author'],b['genre'],b['total_pages'],b['current_page'],b['status']])
        messagebox.showinfo('Export complete', f'Saved your library to:\n{filename}')

    def load_demo(self):
        if self.db.summary()['total']:
            messagebox.showinfo('Library already contains books', 'Demo books can only be loaded into an empty library.')
            return
        samples = [
            ('The Alchemist','Paulo Coelho','Fiction',208,208,'Completed'),
            ('Atomic Habits','James Clear','Self-help',320,120,'Reading'),
            ('Wings of Fire','A. P. J. Abdul Kalam','Biography',180,0,'To Read'),
            ('The Hobbit','J. R. R. Tolkien','Fantasy',310,310,'Completed'),
            ('Ikigai','Héctor García','Non-fiction',208,75,'Reading'),
        ]
        for sample in samples:
            self.db.add(*sample)
        self.refresh()

    def _quit(self):
        self.db.close()
        self.destroy()


if __name__ == '__main__':
    BookNestApp().mainloop()
