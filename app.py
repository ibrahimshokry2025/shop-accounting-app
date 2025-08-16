
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os, datetime
import db
from invoice_pdf import generate_invoice_pdf

APP_TITLE = "برنامج حسابات المحل - إصدار خفيف"
SHOP_NAME = "اسم المحل"
SHOP_INFO = "هاتف: 0000000\nالعنوان: ---"
LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "logo.png")

class LoginWindow(tk.Toplevel):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.title("تسجيل الدخول")
        self.on_success = on_success
        self.geometry("320x180")
        self.resizable(False, False)
        ttk.Label(self, text="اسم المستخدم").pack(pady=5)
        self.e_user = ttk.Entry(self, justify='center')
        self.e_user.pack(fill='x', padx=20)
        ttk.Label(self, text="كلمة السر").pack(pady=5)
        self.e_pass = ttk.Entry(self, show="*", justify='center')
        self.e_pass.pack(fill='x', padx=20)
        ttk.Button(self, text="دخول", command=self.do_login).pack(pady=10)
        self.bind("<Return>", lambda e: self.do_login())

    def do_login(self):
        user = self.e_user.get().strip()
        pwd = self.e_pass.get().strip()
        conn = db.get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (user,pwd))
        row = c.fetchone()
        conn.close()
        if row:
            self.on_success(dict(row))
            self.destroy()
        else:
            messagebox.showerror("خطأ", "بيانات الدخول غير صحيحة")

class SimpleForm(ttk.Frame):
    def __init__(self, master, fields, on_submit, submit_label="حفظ"):
        super().__init__(master)
        self.vars = {}
        for i, (key, label) in enumerate(fields):
            ttk.Label(self, text=label).grid(row=i, column=0, sticky="e", padx=4, pady=4)
            e = ttk.Entry(self)
            e.grid(row=i, column=1, sticky="we", padx=4, pady=4)
            self.vars[key] = e
        self.columnconfigure(1, weight=1)
        ttk.Button(self, text=submit_label, command=self.submit).grid(row=len(fields), column=0, columnspan=2, pady=8)
        self.on_submit = on_submit

    def submit(self):
        data = {k: v.get() for k, v in self.vars.items()}
        self.on_submit(data)

class ItemsView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.tree = ttk.Treeview(self, columns=("code","name","price","cost","qty","min_qty"), show="headings")
        for col, txt in zip(self.tree["columns"], ["الكود","الاسم","سعر البيع","سعر التكلفة","الكمية","حد أدنى"]):
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=100, anchor="center")
        self.tree.pack(fill="both", expand=True)
        btns = ttk.Frame(self); btns.pack(fill='x')
        ttk.Button(btns, text="إضافة", command=self.add_item).pack(side='right', padx=4, pady=4)
        ttk.Button(btns, text="تعديل", command=self.edit_item).pack(side='right', padx=4, pady=4)
        ttk.Button(btns, text="حذف", command=self.delete_item).pack(side='right', padx=4, pady=4)
        self.refresh()

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        conn = db.get_conn(); c = conn.cursor()
        for row in c.execute("SELECT * FROM items ORDER BY id DESC"):
            self.tree.insert("", "end", iid=row["id"], values=(row["code"], row["name"], row["price"], row["cost"], row["qty"], row["min_qty"]))
        conn.close()

    def add_item(self):
        win = tk.Toplevel(self); win.title("إضافة صنف")
        form = SimpleForm(win, [
            ("code","الكود"), ("name","الاسم"), ("price","سعر البيع"), ("cost","سعر التكلفة"), ("qty","الكمية"), ("min_qty","حد أدنى")
        ], self._save_new, "حفظ")
        form.pack(fill='both', expand=True, padx=8, pady=8)

    def _save_new(self, data):
        try:
            conn = db.get_conn(); c = conn.cursor()
            c.execute("INSERT INTO items(code,name,price,cost,qty,min_qty) VALUES (?,?,?,?,?,?)",
                      (data["code"], data["name"], float(data["price"] or 0), float(data["cost"] or 0),
                       float(data["qty"] or 0), float(data["min_qty"] or 0)))
            conn.commit(); conn.close()
            self.refresh()
        except Exception as e:
            messagebox.showerror("خطأ", str(e))

    def edit_item(self):
        sel = self.tree.selection()
        if not sel: return
        item_id = int(sel[0])
        conn = db.get_conn(); c = conn.cursor()
        row = c.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
        conn.close()
        win = tk.Toplevel(self); win.title("تعديل صنف")
        form = SimpleForm(win, [
            ("code","الكود"), ("name","الاسم"), ("price","سعر البيع"), ("cost","سعر التكلفة"), ("qty","الكمية"), ("min_qty","حد أدنى")
        ], lambda d: self._save_edit(item_id, d), "تحديث")
        for k, e in form.vars.items():
            e.insert(0, str(row[k]))
        form.pack(fill='both', expand=True, padx=8, pady=8)

    def _save_edit(self, item_id, data):
        try:
            conn = db.get_conn(); c = conn.cursor()
            c.execute("""UPDATE items SET code=?, name=?, price=?, cost=?, qty=?, min_qty=? WHERE id=?""",
                      (data["code"], data["name"], float(data["price"] or 0), float(data["cost"] or 0),
                       float(data["qty"] or 0), float(data["min_qty"] or 0), item_id))
            conn.commit(); conn.close()
            self.refresh()
        except Exception as e:
            messagebox.showerror("خطأ", str(e))

    def delete_item(self):
        sel = self.tree.selection()
        if not sel: return
        item_id = int(sel[0])
        if not messagebox.askyesno("تأكيد", "هل تريد حذف الصنف؟"): return
        conn = db.get_conn(); c = conn.cursor()
        c.execute("DELETE FROM items WHERE id=?", (item_id,))
        conn.commit(); conn.close()
        self.refresh()

class PartiesView(ttk.Frame):
    def __init__(self, master, ptype):
        super().__init__(master)
        self.ptype = ptype
        self.tree = ttk.Treeview(self, columns=("name","phone","address"), show="headings")
        for col, txt in zip(self.tree["columns"], ["الاسم","الهاتف","العنوان"]):
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=150, anchor="center")
        self.tree.pack(fill="both", expand=True)
        btns = ttk.Frame(self); btns.pack(fill='x')
        ttk.Button(btns, text="إضافة", command=self.add_party).pack(side='right', padx=4, pady=4)
        ttk.Button(btns, text="تعديل", command=self.edit_party).pack(side='right', padx=4, pady=4)
        ttk.Button(btns, text="حذف", command=self.delete_party).pack(side='right', padx=4, pady=4)
        ttk.Button(btns, text="تقرير الرصيد", command=self.balance_report).pack(side='left', padx=4, pady=4)
        self.refresh()

    def refresh(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = db.get_conn(); c = conn.cursor()
        for row in c.execute("SELECT * FROM parties WHERE type=? ORDER BY id DESC", (self.ptype,)):
            self.tree.insert("", "end", iid=row["id"], values=(row["name"], row["phone"], row["address"]))
        conn.close()

    def add_party(self):
        win = tk.Toplevel(self); win.title("إضافة")
        form = SimpleForm(win, [("name","الاسم"),("phone","الهاتف"),("address","العنوان")],
                          self._save_new, "حفظ")
        form.pack(fill='both', expand=True, padx=8, pady=8)

    def _save_new(self, data):
        conn = db.get_conn(); c = conn.cursor()
        c.execute("INSERT INTO parties(type,name,phone,address) VALUES (?,?,?,?)",
                  (self.ptype, data["name"], data["phone"], data["address"]))
        conn.commit(); conn.close(); self.refresh()

    def edit_party(self):
        sel = self.tree.selection()
        if not sel: return
        pid = int(sel[0])
        conn = db.get_conn(); c = conn.cursor()
        row = c.execute("SELECT * FROM parties WHERE id=?", (pid,)).fetchone()
        conn.close()
        win = tk.Toplevel(self); win.title("تعديل")
        form = SimpleForm(win, [("name","الاسم"),("phone","الهاتف"),("address","العنوان")],
                          lambda d: self._save_edit(pid, d), "تحديث")
        for k, e in form.vars.items(): e.insert(0, str(row[k] or ""))
        form.pack(fill='both', expand=True, padx=8, pady=8)

    def _save_edit(self, pid, data):
        conn = db.get_conn(); c = conn.cursor()
        c.execute("UPDATE parties SET name=?, phone=?, address=? WHERE id=?",
                  (data["name"], data["phone"], data["address"], pid))
        conn.commit(); conn.close(); self.refresh()

    def delete_party(self):
        sel = self.tree.selection()
        if not sel: return
        pid = int(sel[0])
        if not messagebox.askyesno("تأكيد", "هل تريد الحذف؟"): return
        conn = db.get_conn(); c = conn.cursor()
        c.execute("DELETE FROM parties WHERE id=?", (pid,))
        conn.commit(); conn.close(); self.refresh()

    def balance_report(self):
        # حساب تراكمي: مبيعات للعميل = دائن له؟ العكس للمورد
        # هنا سنحسب الرصيد = مجموع (مبيعات - مدفوعات) بشكل مبسط من الفواتير
        win = tk.Toplevel(self); win.title("تقرير الأرصدة")
        cols = ("name","sales","purchases","balance")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=15)
        titles = ("الاسم","مبيعات","مشتريات","الرصيد (له+/عليه-)") if self.ptype=="customer" else ("الاسم","مبيعات","مشتريات","الرصيد (لهم+/علينا-)")
        for col, txt in zip(cols, titles):
            tree.heading(col, text=txt)
            tree.column(col, width=140, anchor="center")
        tree.pack(fill='both', expand=True)
        conn = db.get_conn(); c = conn.cursor()
        parties = c.execute("SELECT * FROM parties WHERE type=?", (self.ptype,)).fetchall()
        for p in parties:
            sales = c.execute("""SELECT COALESCE(SUM(total),0) FROM invoices 
                                 WHERE type='sale' AND party_id=?""", (p["id"],)).fetchone()[0]
            purchases = c.execute("""SELECT COALESCE(SUM(total),0) FROM invoices 
                                     WHERE type='purchase' AND party_id=?""", (p["id"],)).fetchone()[0]
            # للعميل: الرصيد = مبيعات (مطلوب منه لنا) - مشتريات (مبالغ سوّيناها كارتجاع)
            # للمورد: الرصيد = مشتريات (مطلوب لنا لهم) - مبيعات (مبالغ عكسية)
            balance = (sales - purchases) if self.ptype=="customer" else (purchases - sales)
            tree.insert("", "end", values=(p["name"], round(sales,2), round(purchases,2), round(balance,2)))
        conn.close()

class InvoiceWindow(tk.Toplevel):
    def __init__(self, master, inv_type, current_user):
        super().__init__(master)
        self.title("فاتورة " + ("بيع" if inv_type=="sale" else "شراء"))
        self.inv_type = inv_type
        self.current_user = current_user
        self.geometry("900x560")

        frm = ttk.Frame(self); frm.pack(fill='x', padx=8, pady=6)
        ttk.Label(frm, text="الطرف:").pack(side='right')
        self.party_cb = ttk.Combobox(frm, state="readonly")
        self.party_cb.pack(side='right', padx=6)
        ttk.Button(frm, text="إضافة طرف", command=self.add_party).pack(side='right')
        self.load_parties()

        ttk.Label(frm, text="تاريخ:").pack(side='right', padx=6)
        self.date_var = tk.StringVar(value=str(datetime.date.today()))
        ttk.Entry(frm, textvariable=self.date_var, width=12).pack(side='right')

        self.tree = ttk.Treeview(self, columns=("item","qty","price","total"), show="headings", height=14)
        for col, txt in zip(self.tree["columns"], ["الصنف","الكمية","السعر","الإجمالي"]):
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=160 if col=="item" else 100, anchor="center")
        self.tree.pack(fill='both', expand=True, padx=8, pady=6)

        btns = ttk.Frame(self); btns.pack(fill='x', padx=8)
        ttk.Button(btns, text="إضافة صنف", command=self.add_item).pack(side='right', padx=4)
        ttk.Button(btns, text="حذف سطر", command=self.del_row).pack(side='right', padx=4)

        totals = ttk.Frame(self); totals.pack(fill='x', padx=8, pady=6)
        self.subtotal_var = tk.DoubleVar(value=0.0)
        self.discount_var = tk.DoubleVar(value=0.0)
        self.tax_var = tk.DoubleVar(value=0.0)
        self.total_var = tk.DoubleVar(value=0.0)
        for lbl, var in [("الإجمالي قبل الخصم", self.subtotal_var),
                         ("الخصم", self.discount_var),
                         ("الضريبة", self.tax_var),
                         ("الصافي", self.total_var)]:
            f = ttk.Frame(totals); f.pack(side='right', padx=8)
            ttk.Label(f, text=lbl).pack()
            ttk.Entry(f, textvariable=var, width=10).pack()

        actions = ttk.Frame(self); actions.pack(fill='x', padx=8, pady=8)
        ttk.Button(actions, text="حفظ الفاتورة", command=self.save_invoice).pack(side='right', padx=6)
        ttk.Button(actions, text="طباعة (PDF)", command=self.print_invoice).pack(side='right', padx=6)

    def load_parties(self):
        conn = db.get_conn(); c = conn.cursor()
        typ = "customer" if self.inv_type=="sale" else "supplier"
        rows = c.execute("SELECT id,name FROM parties WHERE type=? ORDER BY name", (typ,)).fetchall()
        self.parties = rows
        self.party_cb['values'] = [r['name'] for r in rows]
        conn.close()

    def add_party(self):
        win = tk.Toplevel(self); win.title("إضافة طرف")
        name = tk.StringVar(); phone = tk.StringVar(); address = tk.StringVar()
        for lbl, var in [("الاسم", name), ("الهاتف", phone), ("العنوان", address)]:
            f = ttk.Frame(win); f.pack(fill='x', padx=8, pady=4)
            ttk.Label(f, text=lbl).pack(side='right'); ttk.Entry(f, textvariable=var).pack(side='right', fill='x', expand=True)
        def do():
            conn = db.get_conn(); c = conn.cursor()
            c.execute("INSERT INTO parties(type,name,phone,address) VALUES (?,?,?,?)",
                      ("customer" if self.inv_type=="sale" else "supplier", name.get(), phone.get(), address.get()))
            conn.commit(); conn.close(); self.load_parties(); win.destroy()
        ttk.Button(win, text="حفظ", command=do).pack(pady=6)

    def add_item(self):
        win = tk.Toplevel(self); win.title("إضافة صنف")
        cb = ttk.Combobox(win, state="readonly"); cb.pack(fill='x', padx=8, pady=6)
        conn = db.get_conn(); c = conn.cursor()
        items = c.execute("SELECT id,name,price,cost FROM items ORDER BY name").fetchall()
        conn.close()
        cb['values'] = [f"{r['name']}" for r in items]
        qty_var = tk.DoubleVar(value=1.0)
        price_var = tk.DoubleVar(value=0.0)
        def on_select(e=None):
            i = cb.current()
            if i>=0:
                r = items[i]
                price_var.set(r["price"] if self.inv_type=="sale" else r["cost"])
        cb.bind("<<ComboboxSelected>>", on_select)
        ttk.Label(win, text="الكمية").pack(); ttk.Entry(win, textvariable=qty_var).pack(fill='x', padx=8)
        ttk.Label(win, text="السعر").pack(); ttk.Entry(win, textvariable=price_var).pack(fill='x', padx=8)
        def add_line():
            name = cb.get()
            if not name: return
            qty = float(qty_var.get() or 0)
            price = float(price_var.get() or 0)
            total = qty * price
            self.tree.insert("", "end", values=(name, qty, price, total))
            self.recalc()
            win.destroy()
        ttk.Button(win, text="إضافة", command=add_line).pack(pady=6)

    def del_row(self):
        sel = self.tree.selection()
        for s in sel:
            self.tree.delete(s)
        self.recalc()

    def recalc(self):
        subtotal = 0.0
        for iid in self.tree.get_children():
            vals = self.tree.item(iid, "values")
            subtotal += float(vals[3])
        self.subtotal_var.set(round(subtotal,2))
        total = subtotal - float(self.discount_var.get() or 0) + float(self.tax_var.get() or 0)
        self.total_var.set(round(total,2))

    def save_invoice(self):
        if self.party_cb.current() < 0:
            messagebox.showerror("خطأ","اختر طرفاً (عميل/مورد)")
            return
        conn = db.get_conn(); c = conn.cursor()
        inv_no = db.next_invoice_number("S" if self.inv_type=="sale" else "P")
        party_id = self.parties[self.party_cb.current()]["id"]
        date = self.date_var.get()
        subtotal = float(self.subtotal_var.get() or 0)
        discount = float(self.discount_var.get() or 0)
        tax = float(self.tax_var.get() or 0)
        total = float(self.total_var.get() or 0)
        c.execute("""INSERT INTO invoices(number,type,party_id,date,subtotal,discount,tax,total,user_id)
                     VALUES (?,?,?,?,?,?,?,?,?)""",
                  (inv_no, self.inv_type, party_id, date, subtotal, discount, tax, total, self.current_user["id"]))
        inv_id = c.lastrowid
        # map item name to id
        items_map = {r["name"]: r for r in c.execute("SELECT id,name,price,cost FROM items").fetchall()}
        for iid in self.tree.get_children():
            name, qty, price, total_line = self.tree.item(iid, "values")
            item = items_map.get(name)
            if not item:
                continue
            c.execute("""INSERT INTO invoice_items(invoice_id,item_id,qty,price,total)
                         VALUES (?,?,?,?,?)""", (inv_id, item["id"], float(qty), float(price), float(total_line)))
            # update stock
            if self.inv_type=="sale":
                c.execute("UPDATE items SET qty = qty - ? WHERE id=?", (float(qty), item["id"]))
            else:
                c.execute("UPDATE items SET qty = qty + ? WHERE id=?", (float(qty), item["id"]))
        conn.commit(); conn.close()
        messagebox.showinfo("تم", f"حُفظت الفاتورة رقم: {inv_no}")

    def print_invoice(self):
        if self.party_cb.current() < 0:
            messagebox.showerror("خطأ","اختر طرفاً (عميل/مورد)")
            return
        # Build data from current screen without requiring save
        items = []
        for iid in self.tree.get_children():
            name, qty, price, total = self.tree.item(iid, "values")
            items.append({"name": name, "qty": float(qty), "price": float(price), "total": float(total)})
        data = {
            "invoice_no": "PREVIEW",
            "invoice_date": self.date_var.get(),
            "invoice_type": "بيع" if self.inv_type=="sale" else "شراء",
            "customer_supplier_name": self.party_cb.get(),
            "customer_supplier_info": "",
            "items": items,
            "subtotal": float(self.subtotal_var.get() or 0),
            "discount": float(self.discount_var.get() or 0),
            "tax": float(self.tax_var.get() or 0),
            "total": float(self.total_var.get() or 0),
            "shop_name": SHOP_NAME,
            "shop_info": SHOP_INFO,
            "logo_path": LOGO_PATH
        }
        out = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")], title="حفظ الفاتورة PDF")
        if not out: return
        try:
            generate_invoice_pdf(out, data)
            messagebox.showinfo("تم", "تم حفظ الفاتورة PDF")
        except Exception as e:
            messagebox.showerror("خطأ", str(e))

class ReportsView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        nb = ttk.Notebook(self); nb.pack(fill='both', expand=True)
        self.stock = ttk.Treeview(nb, columns=("code","name","qty","min"), show="headings")
        for col, txt in zip(self.stock["columns"], ["الكود","الصنف","الكمية","حد أدنى"]):
            self.stock.heading(col, text=txt); self.stock.column(col, anchor="center", width=120)
        nb.add(self.stock, text="المخزون")
        self.sales = ttk.Treeview(nb, columns=("date","number","party","total"), show="headings")
        for col, txt in zip(self.sales["columns"], ["التاريخ","رقم","الطرف","الإجمالي"]):
            self.sales.heading(col, text=txt); self.sales.column(col, anchor="center", width=140)
        nb.add(self.sales, text="مبيعات/مشتريات")
        self.profit_lbl = ttk.Label(self, text="الربح (اختبار سريع اليوم): 0.00")
        self.profit_lbl.pack(anchor='e', padx=8, pady=6)
        self.refresh()

    def refresh(self):
        for t in (self.stock, self.sales):
            for i in t.get_children(): t.delete(i)
        conn = db.get_conn(); c = conn.cursor()
        for row in c.execute("SELECT code,name,qty,min_qty FROM items ORDER BY name"):
            self.stock.insert("", "end", values=(row["code"], row["name"], row["qty"], row["min_qty"]))
        for row in c.execute("""SELECT invoices.date, invoices.number, parties.name as party, invoices.total 
                                FROM invoices LEFT JOIN parties ON parties.id=invoices.party_id
                                ORDER BY invoices.id DESC LIMIT 200"""):
            self.sales.insert("", "end", values=(row["date"], row["number"], row["party"], row["total"]))
        # Simple profit = sum(sale total - cost) approximation for today
        today = str(datetime.date.today())
        sales_sum = c.execute("SELECT COALESCE(SUM(total),0) FROM invoices WHERE type='sale' AND date=?", (today,)).fetchone()[0]
        # cost approx: sum over sale items: qty * item.cost (current). This is a simplification.
        cost = 0.0
        for row in c.execute("""SELECT ii.qty, it.cost FROM invoice_items ii
                                JOIN invoices inv ON inv.id=ii.invoice_id
                                JOIN items it ON it.id=ii.item_id
                                WHERE inv.type='sale' AND inv.date=?""", (today,)):
            cost += row["qty"] * row["cost"]
        profit = sales_sum - cost
        self.profit_lbl.config(text=f"الربح اليومي التقريبي: {round(profit,2)}")
        conn.close()

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.state('zoomed') if hasattr(self, 'state') else self.geometry("1100x700")
        db.init_db()
        self.current_user = None
        self.create_menu()
        self.status = ttk.Label(self, text="غير مسجّل", anchor='e')
        self.status.pack(fill='x')
        self.content = ttk.Frame(self)
        self.content.pack(fill='both', expand=True)
        self.show_login()

    def create_menu(self):
        menubar = tk.Menu(self)
        m_master = tk.Menu(menubar, tearoff=0)
        m_master.add_command(label="الأصناف", command=self.show_items)
        m_master.add_command(label="العملاء", command=lambda: self.show_parties("customer"))
        m_master.add_command(label="الموردين", command=lambda: self.show_parties("supplier"))
        menubar.add_cascade(label="بيانات", menu=m_master)

        m_inv = tk.Menu(menubar, tearoff=0)
        m_inv.add_command(label="فاتورة بيع", command=lambda: self.new_invoice("sale"))
        m_inv.add_command(label="فاتورة شراء", command=lambda: self.new_invoice("purchase"))
        menubar.add_cascade(label="الفواتير", menu=m_inv)

        m_rep = tk.Menu(menubar, tearoff=0)
        m_rep.add_command(label="التقارير", command=self.show_reports)
        menubar.add_cascade(label="التقارير", menu=m_rep)

        m_user = tk.Menu(menubar, tearoff=0)
        m_user.add_command(label="تسجيل الدخول", command=self.show_login)
        m_user.add_command(label="تغيير كلمة السر", command=self.change_password)
        menubar.add_cascade(label="المستخدم", menu=m_user)

        self.config(menu=menubar)

    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def show_login(self):
        def on_success(user):
            self.current_user = user
            self.status.config(text=f"المستخدم: {user['username']} ({user['role']})")
            self.show_items()
        LoginWindow(self, on_success)

    def show_items(self):
        self.clear_content()
        ItemsView(self.content).pack(fill='both', expand=True)

    def show_parties(self, typ):
        self.clear_content()
        PartiesView(self.content, typ).pack(fill='both', expand=True)

    def new_invoice(self, inv_type):
        if not self.current_user:
            messagebox.showerror("تنبيه","سجّل الدخول أولاً")
            return
        InvoiceWindow(self, inv_type, self.current_user)

    def show_reports(self):
        self.clear_content()
        ReportsView(self.content).pack(fill='both', expand=True)

    def change_password(self):
        if not self.current_user:
            messagebox.showerror("تنبيه","سجّل الدخول أولاً")
            return
        win = tk.Toplevel(self); win.title("تغيير كلمة السر")
        old = tk.StringVar(); new = tk.StringVar()
        for lbl, var in [("القديمة", old), ("الجديدة", new)]:
            f = ttk.Frame(win); f.pack(fill='x', padx=8, pady=4)
            ttk.Label(f, text=f"كلمة السر {lbl}").pack(side='right'); ttk.Entry(f, textvariable=var, show="*").pack(side='right', fill='x', expand=True)
        def do():
            import sqlite3
            conn = db.get_conn(); c = conn.cursor()
            user = c.execute("SELECT * FROM users WHERE id=?", (self.current_user["id"],)).fetchone()
            if user["password"] != old.get():
                messagebox.showerror("خطأ","كلمة السر القديمة غير صحيحة"); conn.close(); return
            c.execute("UPDATE users SET password=? WHERE id=?", (new.get(), self.current_user["id"]))
            conn.commit(); conn.close(); messagebox.showinfo("تم","تم تغيير كلمة السر"); win.destroy()
        ttk.Button(win, text="حفظ", command=do).pack(pady=6)

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
