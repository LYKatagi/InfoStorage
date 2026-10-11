import tkinter as tk
from contextlib import suppress
from pathlib import Path
from tkinter import messagebox, ttk

from info_storage.desktop.api_client import RemoteVaultStore
from info_storage.desktop.storage import Collection, LocalVaultStore


class InfoStorageDesktop:
    def __init__(self, root: tk.Tk, local_dir: Path | None = None):
        self.root = root
        self.root.title("InfoStorage Desktop")
        self.root.geometry("1040x740")
        self.root.minsize(820, 600)
        self.root.configure(background="#f2f6f3")
        self.local_dir = local_dir or Path.home() / ".infostorage" / "desktop"
        self.store: LocalVaultStore | RemoteVaultStore | None = None
        self.mode = tk.StringVar(value="local")
        self.api_url = tk.StringVar(value="http://127.0.0.1:8000")
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.confirmation = tk.StringVar()
        self.create_account = tk.BooleanVar(value=not self._local_account_exists())
        self.active_collection: Collection = "credentials"
        self.content = ttk.Frame(root, padding=24)
        self.content.pack(fill="both", expand=True)
        self._configure_style()
        self._show_login()

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background="#f2f6f3")
        style.configure("Panel.TFrame", background="#ffffff")
        style.configure(
            "TLabel", background="#f2f6f3", foreground="#172a25", font=("Segoe UI", 10)
        )
        style.configure("Title.TLabel", font=("Segoe UI", 25, "bold"))
        style.configure("Section.TLabel", font=("Segoe UI", 13, "bold"))
        style.configure("Muted.TLabel", foreground="#61726b")
        style.configure("Card.TFrame", background="#ffffff", relief="flat")
        style.configure("Card.TLabel", background="#ffffff", foreground="#172a25")
        style.configure("CardMuted.TLabel", background="#ffffff", foreground="#61726b")
        style.configure(
            "Badge.TLabel", background="#e4f1e9", foreground="#105542", padding=(10, 5)
        )
        style.configure("TButton", padding=(11, 7), font=("Segoe UI", 9))
        style.configure(
            "Accent.TButton",
            background="#176b55",
            foreground="#ffffff",
            padding=(14, 9),
            font=("Segoe UI", 9, "bold"),
        )
        style.map("Accent.TButton", background=[("active", "#105542")])
        style.configure(
            "Treeview",
            rowheight=36,
            font=("Segoe UI", 10),
            background="#ffffff",
            fieldbackground="#ffffff",
        )
        style.map(
            "Treeview",
            background=[("selected", "#dceee3")],
            foreground=[("selected", "#172a25")],
        )
        style.configure(
            "Treeview.Heading", font=("Segoe UI", 9, "bold"), padding=(9, 8)
        )
        style.configure("TNotebook", background="#f2f6f3", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 9), font=("Segoe UI", 9, "bold"))

    def _local_account_exists(self) -> bool:
        return (self.local_dir / "credentials.json").exists()

    def _clear_content(self) -> None:
        for child in self.content.winfo_children():
            child.destroy()

    def _show_login(self) -> None:
        self._clear_content()
        self.mode.set("local")
        brand = ttk.Frame(self.content)
        brand.pack(fill="x", pady=(0, 22))
        ttk.Label(
            brand, text="IS", style="Badge.TLabel", font=("Segoe UI", 12, "bold")
        ).pack(side="left")
        ttk.Label(brand, text="InfoStorage", style="Section.TLabel").pack(
            side="left", padx=10
        )
        ttk.Label(brand, text="DESKTOP VAULT", style="Muted.TLabel").pack(side="right")

        centered = ttk.Frame(self.content)
        centered.pack(fill="both", expand=True)
        card = ttk.Frame(centered, style="Card.TFrame", padding=30)
        card.pack(anchor="center", pady=22)
        ttk.Label(
            card, text="Acesse seu cofre", style="Title.TLabel", background="#ffffff"
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            card,
            text="Escolha o local dos dados e desbloqueie ou crie uma conta.",
            style="CardMuted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 22))
        ttk.Label(
            card,
            text="ARMAZENAMENTO",
            style="CardMuted.TLabel",
            font=("Segoe UI", 8, "bold"),
        ).grid(row=2, column=0, sticky="w", pady=(0, 8))
        mode_row = ttk.Frame(card, style="Card.TFrame")
        mode_row.grid(row=3, column=0, sticky="ew")
        ttk.Radiobutton(
            mode_row,
            text="Local",
            value="local",
            variable=self.mode,
            command=self._update_login_fields,
        ).pack(side="left", padx=(0, 22))
        ttk.Radiobutton(
            mode_row,
            text="Sincronizar pela API",
            value="sync",
            variable=self.mode,
            command=self._update_login_fields,
        ).pack(side="left")

        ttk.Separator(card).grid(row=4, column=0, sticky="ew", pady=(18, 8))
        self.fields = ttk.Frame(card, style="Card.TFrame")
        self.fields.grid(row=5, column=0, sticky="ew", pady=(4, 0))
        card.columnconfigure(0, weight=1)
        self._update_login_fields()

        self.status = ttk.Label(card, text="", style="Muted.TLabel", wraplength=490)
        self.status.grid(row=6, column=0, sticky="w", pady=(14, 0))

    def _update_login_fields(self) -> None:
        for child in self.fields.winfo_children():
            child.destroy()
        row = 0
        if self.mode.get() == "sync":
            ttk.Label(self.fields, text="URL da API", background="#ffffff").grid(
                row=row, column=0, sticky="w", pady=(0, 5)
            )
            ttk.Entry(self.fields, textvariable=self.api_url).grid(
                row=row + 1, column=0, sticky="ew", pady=(0, 12)
            )
            row += 2
            ttk.Label(self.fields, text="Usuário", background="#ffffff").grid(
                row=row, column=0, sticky="w", pady=(0, 5)
            )
            ttk.Entry(self.fields, textvariable=self.username).grid(
                row=row + 1, column=0, sticky="ew", pady=(0, 12)
            )
            row += 2

        ttk.Label(self.fields, text="Senha mestra", background="#ffffff").grid(
            row=row, column=0, sticky="w", pady=(0, 5)
        )
        ttk.Entry(self.fields, textvariable=self.password, show="•").grid(
            row=row + 1, column=0, sticky="ew", pady=(0, 12)
        )
        row += 2
        if self.create_account.get():
            ttk.Label(self.fields, text="Confirmar senha", background="#ffffff").grid(
                row=row, column=0, sticky="w", pady=(0, 5)
            )
            ttk.Entry(self.fields, textvariable=self.confirmation, show="•").grid(
                row=row + 1, column=0, sticky="ew", pady=(0, 12)
            )
            row += 2

        action = "Criar conta" if self.create_account.get() else "Desbloquear cofre"
        ttk.Button(
            self.fields,
            text=action,
            style="Accent.TButton",
            command=self._authenticate,
        ).grid(row=row, column=0, sticky="ew")
        switch_text = (
            "Já tenho conta? Entrar"
            if self.create_account.get()
            else "Criar conta nova"
        )
        ttk.Button(
            self.fields, text=switch_text, command=self._toggle_account_mode
        ).grid(row=row + 1, column=0, sticky="e", pady=(8, 0))
        self.fields.columnconfigure(0, weight=1)

    def _toggle_account_mode(self) -> None:
        self.create_account.set(not self.create_account.get())
        self.password.set("")
        self.confirmation.set("")
        self._update_login_fields()

    def _authenticate(self) -> None:
        password = self.password.get()
        if not password:
            self._set_status("Informe a senha mestra.", error=True)
            return
        if self.create_account.get() and password != self.confirmation.get():
            self._set_status("As senhas não coincidem.", error=True)
            return

        try:
            if self.mode.get() == "local":
                store = LocalVaultStore(self.local_dir)
                data = (
                    store.create_account(password)
                    if self.create_account.get()
                    else store.login(password)
                )
            else:
                if not self.username.get().strip():
                    self._set_status("Informe o usuário da API.", error=True)
                    return
                store = RemoteVaultStore(self.api_url.get())
                data = (
                    store.register(self.username.get().strip(), password)
                    if self.create_account.get()
                    else store.login(self.username.get().strip(), password)
                )
        except Exception as error:
            self._set_status(str(error), error=True)
            return

        self.store = store
        self.password.set("")
        self.confirmation.set("")
        self._show_vault(data)

    def _show_vault(self, data: dict[str, list[dict]] | None = None) -> None:
        self._clear_content()
        top = ttk.Frame(self.content)
        top.pack(fill="x", pady=(0, 20))
        heading = ttk.Frame(top)
        heading.pack(side="left", fill="x", expand=True)
        ttk.Label(
            heading,
            text="MEU COFRE",
            foreground="#176b55",
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")
        ttk.Label(heading, text="Credenciais e notas", style="Title.TLabel").pack(
            anchor="w", pady=(2, 0)
        )
        mode_label = (
            "API sincronizada"
            if isinstance(self.store, RemoteVaultStore)
            else "Somente local"
        )
        ttk.Label(top, text=mode_label, style="Badge.TLabel").pack(
            side="right", padx=(8, 0)
        )
        ttk.Button(top, text="Bloquear cofre", command=self._logout).pack(side="right")
        if isinstance(self.store, RemoteVaultStore):
            ttk.Button(top, text="Sincronizar", command=self._refresh).pack(
                side="right", padx=(0, 8)
            )

        self.status = ttk.Label(self.content, text="", style="Muted.TLabel")
        self.status.pack(fill="x", pady=(0, 10))

        self.tabs = ttk.Notebook(self.content)
        self.tabs.pack(fill="both", expand=True)
        self.credential_tab = ttk.Frame(self.tabs, padding=12)
        self.note_tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(self.credential_tab, text="Credenciais")
        self.tabs.add(self.note_tab, text="Notas")
        self.credential_tree = self._make_tree(
            self.credential_tab,
            ("title", "username"),
            ("Serviço", "Usuário"),
        )
        self.note_tree = self._make_tree(
            self.note_tab, ("title", "content"), ("Título", "Prévia")
        )
        self._fill_trees(data)

        credential_actions = ttk.Frame(self.credential_tab)
        credential_actions.pack(fill="x", pady=(10, 0))
        ttk.Button(
            credential_actions,
            text="Nova credencial",
            command=lambda: self._edit_item("credentials"),
        ).pack(side="left")
        ttk.Button(
            credential_actions,
            text="Editar",
            command=lambda: self._edit_selected("credentials"),
        ).pack(side="left", padx=6)
        ttk.Button(
            credential_actions,
            text="Remover",
            command=lambda: self._delete_selected("credentials"),
        ).pack(side="left")
        ttk.Button(
            credential_actions, text="Mostrar senha", command=self._show_password
        ).pack(side="right")

        note_actions = ttk.Frame(self.note_tab)
        note_actions.pack(fill="x", pady=(10, 0))
        ttk.Button(
            note_actions, text="Nova nota", command=lambda: self._edit_item("notes")
        ).pack(side="left")
        ttk.Button(
            note_actions, text="Editar", command=lambda: self._edit_selected("notes")
        ).pack(side="left", padx=6)
        ttk.Button(
            note_actions, text="Remover", command=lambda: self._delete_selected("notes")
        ).pack(side="left")

    def _make_tree(
        self, parent: ttk.Frame, columns: tuple[str, str], headings: tuple[str, str]
    ) -> ttk.Treeview:
        table = ttk.Frame(parent)
        table.pack(fill="both", expand=True)
        tree = ttk.Treeview(
            table, columns=columns, show="headings", selectmode="browse"
        )
        for column, heading in zip(columns, headings, strict=True):
            tree.heading(column, text=heading)
            tree.column(column, width=260 if column == "title" else 420, anchor="w")
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(table, orient="vertical", command=tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=scrollbar.set)
        table.rowconfigure(0, weight=1)
        table.columnconfigure(0, weight=1)
        return tree

    def _fill_trees(self, data: dict[str, list[dict]] | None = None) -> None:
        if data is None:
            data = {
                "credentials": self.store.list_items("credentials"),
                "notes": self.store.list_items("notes"),
            }
        self.credential_tree.delete(*self.credential_tree.get_children())
        self.note_tree.delete(*self.note_tree.get_children())
        for item in data["credentials"]:
            self.credential_tree.insert(
                "",
                "end",
                iid=item["id"],
                values=(item["title"], item.get("username", "")),
            )
        for item in data["notes"]:
            preview = item.get("content", "").replace("\n", " ")[:100]
            self.note_tree.insert(
                "", "end", iid=item["id"], values=(item["title"], preview)
            )

    def _refresh(self) -> None:
        try:
            data = self.store.load()
            self._fill_trees(data)
            self._set_status("Cofre atualizado.")
        except Exception as error:
            self._set_status(str(error), error=True)

    def _selected_id(self, collection: Collection) -> str | None:
        tree = self.credential_tree if collection == "credentials" else self.note_tree
        selected = tree.selection()
        return selected[0] if selected else None

    def _selected_item(self, collection: Collection) -> dict | None:
        item_id = self._selected_id(collection)
        if item_id is None:
            return None
        return next(
            (
                item
                for item in self.store.list_items(collection)
                if item["id"] == item_id
            ),
            None,
        )

    def _edit_selected(self, collection: Collection) -> None:
        item = self._selected_item(collection)
        if item is None:
            messagebox.showinfo("InfoStorage", "Selecione um item primeiro.")
            return
        self._edit_item(collection, item)

    def _edit_item(self, collection: Collection, item: dict | None = None) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar" if item else "Novo item")
        dialog.transient(self.root)
        dialog.grab_set()
        form = ttk.Frame(dialog, padding=20)
        form.pack(fill="both", expand=True)
        title = tk.StringVar(value=item.get("title", "") if item else "")
        ttk.Label(form, text="Título").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=title, width=48).grid(
            row=1, column=0, sticky="ew", pady=(4, 12)
        )

        values: dict[str, tk.StringVar] = {"title": title}
        if collection == "credentials":
            for row, field, label, secret in (
                (2, "username", "Usuário ou e-mail", False),
                (4, "password", "Senha", True),
                (6, "notes", "Observações", False),
            ):
                values[field] = tk.StringVar(value=item.get(field, "") if item else "")
                ttk.Label(form, text=label).grid(row=row, column=0, sticky="w")
                ttk.Entry(
                    form,
                    textvariable=values[field],
                    width=48,
                    show="•" if secret else "",
                ).grid(row=row + 1, column=0, sticky="ew", pady=(4, 12))
        else:
            values["content"] = tk.StringVar(
                value=item.get("content", "") if item else ""
            )
            ttk.Label(form, text="Conteúdo").grid(row=2, column=0, sticky="w")
            content = tk.Text(form, width=48, height=9, wrap="word")
            content.grid(row=3, column=0, sticky="nsew", pady=(4, 12))
            content.insert("1.0", values["content"].get())

        def save() -> None:
            payload = {key: variable.get().strip() for key, variable in values.items()}
            if collection == "notes":
                payload["content"] = content.get("1.0", "end-1c").strip()
            if not payload["title"]:
                messagebox.showerror("InfoStorage", "Informe um título.", parent=dialog)
                return
            if collection == "credentials" and not payload.get("password"):
                messagebox.showerror("InfoStorage", "Informe a senha.", parent=dialog)
                return
            try:
                self.store.save_item(
                    collection, payload, item.get("id") if item else None
                )
                dialog.destroy()
                self._refresh()
            except Exception as error:
                messagebox.showerror("InfoStorage", str(error), parent=dialog)

        buttons = ttk.Frame(form)
        buttons.grid(row=8, column=0, sticky="e")
        ttk.Button(buttons, text="Cancelar", command=dialog.destroy).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(buttons, text="Salvar", command=save).pack(side="left")
        form.columnconfigure(0, weight=1)

    def _delete_selected(self, collection: Collection) -> None:
        item_id = self._selected_id(collection)
        if item_id is None:
            messagebox.showinfo("InfoStorage", "Selecione um item primeiro.")
            return
        if not messagebox.askyesno("Confirmar remoção", "Remover este item do cofre?"):
            return
        try:
            self.store.delete_item(collection, item_id)
            self._refresh()
        except Exception as error:
            messagebox.showerror("InfoStorage", str(error))

    def _show_password(self) -> None:
        item = self._selected_item("credentials")
        if item is None:
            messagebox.showinfo("InfoStorage", "Selecione uma credencial primeiro.")
            return
        messagebox.showinfo(item["title"], item.get("password", ""))

    def _logout(self) -> None:
        if self.store is not None:
            with suppress(Exception):
                self.store.logout()
        self.store = None
        self.password.set("")
        self.confirmation.set("")
        self._show_login()

    def _set_status(self, message: str, error: bool = False) -> None:
        self.status.configure(
            text=message, foreground="#b43c3c" if error else "#176b55"
        )


def main() -> None:
    root = tk.Tk()
    application = InfoStorageDesktop(root)
    root.application = application
    root.mainloop()
