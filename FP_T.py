import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from batch_ops import batch_create_folders, batch_delete_folders, batch_rename_folders
from classification import classify_by_type, classify_by_size, classify_by_date, classify_by_ai
from search import search_folders, search_files, ai_search


class SmartFolderManagerUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('智能文件夹管理大师')
        self.geometry('1200x800')

        # 设置样式
        self.style = ttk.Style()
        self.style.configure('TLabel', font=('微软雅黑', 14))
        self.style.configure('TButton', font=('微软雅黑', 14))
        self.style.configure('TCheckbutton', font=('微软雅黑', 14))
        self.style.configure('TCombobox', font=('微软雅黑', 14))

        # 主布局
        self.main_frame = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧文件树
        self.create_file_tree()

        # 右侧功能区域
        self.create_function_area()

        # 状态栏
        self.status_bar = ttk.Label(self, text='就绪', anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_file_tree(self):
        """创建左侧文件树视图"""
        left_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(left_frame, weight=1)

        # 路径选择
        path_frame = ttk.Frame(left_frame)
        path_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(path_frame, text='路径:').pack(side=tk.LEFT)
        self.path_edit = ttk.Entry(path_frame)
        self.path_edit.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.browse_btn = ttk.Button(path_frame, text='浏览', command=self.browse_folder)
        self.browse_btn.pack(side=tk.LEFT)

        # 文件树
        self.tree_view = ttk.Treeview(left_frame)
        self.tree_view.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # 新增：双击树节点可切换路径
        self.tree_view.bind("<Double-1>", self.on_tree_double_click)

    def refresh_tree_view(self, path=None):
        """刷新左侧文件树"""
        if path is None:
            path = self.path_edit.get()
        self.tree_view.delete(*self.tree_view.get_children())
        def insert_items(parent, abspath):
            try:
                items = os.listdir(abspath)
            except Exception:
                return
            for item in items:
                fullpath = os.path.join(abspath, item)
                node = self.tree_view.insert(parent, 'end', text=item, open=False)
                if os.path.isdir(fullpath):
                    insert_items(node, fullpath)
        if os.path.isdir(path):
            insert_items('', path)

    def on_tree_double_click(self, event):
        """双击树节点切换路径"""
        item = self.tree_view.selection()
        if item:
            node = item[0]
            path = self.path_edit.get()
            parts = []
            while node:
                parts.insert(0, self.tree_view.item(node, "text"))
                node = self.tree_view.parent(node)
            new_path = os.path.join(path, *parts)
            if os.path.isdir(new_path):
                self.path_edit.delete(0, tk.END)
                self.path_edit.insert(0, new_path)
                self.refresh_tree_view(new_path)

    def create_function_area(self):
        """创建右侧功能区域"""
        right_frame = ttk.Notebook(self.main_frame)
        self.main_frame.add(right_frame, weight=2)

        # 智能分类标签页
        self.create_classification_tab(right_frame)

        # 批量操作标签页
        self.create_batch_operations_tab(right_frame)

        # 智能搜索标签页
        self.create_search_tab(right_frame)

    def create_classification_tab(self, notebook):
        """创建智能分类标签页"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text='📁 智能分类')

        # 主布局
        main_layout = ttk.Frame(tab)
        main_layout.pack(expand=True, fill=tk.BOTH, padx=40, pady=40)

        # 分类设置组
        settings_group = ttk.LabelFrame(main_layout, text='分类设置', padding=(20, 15))
        settings_group.pack(fill=tk.X, padx=10, pady=(10, 5))

        # 分类方式横向排列，居中显示
        classify_row = ttk.Frame(settings_group)
        classify_row.pack(fill=tk.X, pady=10)
        ttk.Label(classify_row, text='分类方式:', font=('微软雅黑', 14)).pack(side=tk.LEFT, padx=(10, 8))
        self.classify_type = ttk.Combobox(
            classify_row,
            values=['按文件类型', '按文件大小', '按创建日期', 'AI智能分类'],
            width=18,
            font=('微软雅黑', 13)
        )
        self.classify_type.pack(side=tk.LEFT, padx=(0, 30))
        self.classify_type.current(0)

        # 显眼提示
        preview_tip = ttk.Label(
            main_layout,
            text='建议先点击“预览分类结果”查看效果再执行分类操作！',
            font=('微软雅黑', 13, 'bold'),
            foreground='#d9534f'  # 红色
        )
        preview_tip.pack(pady=(10, 0))

        # 操作按钮区域，居中加大间距
        button_frame = ttk.Frame(main_layout)
        button_frame.pack(pady=35)
        self.classify_btn = ttk.Button(
            button_frame, text='🚀 开始智能分类', width=20, command=self.on_classify
        )
        self.classify_btn.pack(side=tk.LEFT, padx=35)
        # 让预览按钮更显眼
        self.style.configure('Preview.TButton', font=('微软雅黑', 14, 'bold'), foreground='#fff', background='#f0ad4e')
        self.preview_btn = ttk.Button(
            button_frame, text='👁️预览分类结果', width=20, command=self.on_preview_classify
        )
        self.preview_btn.pack(side=tk.LEFT, padx=35)

        # 进度条和提示，风格更友好
        progress_frame = ttk.Frame(main_layout)
        progress_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=300)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), pady=5)
        self.progress_label = ttk.Label(
            progress_frame, text='准备就绪', font=('微软雅黑', 12), foreground='#888'
        )
        self.progress_label.pack(side=tk.LEFT, padx=5)

        # 优化按钮风格
        try:
            self.style.configure('Accent.TButton', font=('微软雅黑', 14, 'bold'), foreground='#fff', background='#0078d7')
        except Exception:
            pass

    def create_batch_operations_tab(self, notebook):
        """创建批量操作标签页"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text='⚡ 批量操作')

        # 主布局
        main_layout = ttk.Frame(tab)
        main_layout.pack(expand=True, fill=tk.BOTH, padx=30, pady=30)

        # 批量创建组
        create_group = ttk.LabelFrame(main_layout, text='输入框')
        create_group.pack(fill=tk.X, padx=10, pady=10)

        # 文件夹名称输入区域
        name_row = ttk.Frame(create_group)
        name_row.pack(fill=tk.X, pady=8)
        ttk.Label(name_row, text='文件夹名称:').pack(side=tk.LEFT, padx=(10, 5))
        self.folder_names = tk.Text(name_row, height=3, width=30, font=('微软雅黑', 12))
        self.folder_names.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)

        # 前缀后缀输入区域
        prepost_row = ttk.Frame(create_group)
        prepost_row.pack(fill=tk.X, pady=8)
        ttk.Label(prepost_row, text='前缀:').pack(side=tk.LEFT, padx=(10, 5))
        self.prefix_edit = ttk.Entry(prepost_row, width=12, font=('微软雅黑', 12))
        self.prefix_edit.pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(prepost_row, text='后缀:').pack(side=tk.LEFT, padx=(0, 5))
        self.suffix_edit = ttk.Entry(prepost_row, width=12, font=('微软雅黑', 12))
        self.suffix_edit.pack(side=tk.LEFT)

        # 用法说明标签
        usage_label = ttk.Label(
            create_group,
            text=(
                "说明：\n"
                "1. “文件夹名称”输入框：每行输入一个文件夹名，支持批量创建/删除。\n"
                "2. “前缀”“后缀”输入框：可为所有文件夹名统一加前缀/后缀。\n"
                "3. 批量重命名时，输入格式为：原名,新名（注意：两者之间采用英文逗号分隔）。\n"
                "   （前缀/后缀同样会加在原名和新名前后）"
            ),
            font=('微软雅黑', 11),
            foreground='#888',
            anchor='w',
            justify='left'
        )
        usage_label.pack(fill=tk.X, padx=10, pady=(2, 8))

        # 批量操作组（仅包裹按钮，去除fill和expand）
        batch_group = ttk.LabelFrame(main_layout, text='批量操作')
        batch_group.pack(padx=10, pady=10, anchor='nw')

        # 操作按钮横向排列
        btns_row = ttk.Frame(batch_group)
        btns_row.pack(padx=10, pady=10)
        self.create_btn = ttk.Button(btns_row, text='批量创建', width=16, command=self.on_batch_create)
        self.create_btn.pack(side=tk.LEFT, padx=18)
        self.delete_btn = ttk.Button(btns_row, text='批量删除', width=16, command=self.on_batch_delete)
        self.delete_btn.pack(side=tk.LEFT, padx=18)
        self.rename_btn = ttk.Button(btns_row, text='批量重命名', width=16, command=self.on_batch_rename)
        self.rename_btn.pack(side=tk.LEFT, padx=18)

    def create_search_tab(self, notebook):
        """创建智能搜索标签页"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text='🔍 智能搜索')

        # 搜索条件组
        search_group = ttk.LabelFrame(tab, text='搜索条件')
        search_group.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(search_group, text='搜索类型:').grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.search_type = ttk.Combobox(
            search_group,
            values=['文件夹搜索', '文件搜索', 'AI智能搜索'],
            font=('微软雅黑', 12)
        )
        self.search_type.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.search_type.current(0)

        self.search_edit = ttk.Entry(search_group)
        self.search_edit.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)
        self.search_btn = ttk.Button(search_group, text='搜索', command=self.on_search)
        self.search_btn.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)

    def browse_folder(self):
        """浏览文件夹"""
        folder = filedialog.askdirectory()
        if folder:
            self.path_edit.delete(0, tk.END)
            self.path_edit.insert(0, folder)
            self.refresh_tree_view(folder)

    def on_classify(self):
        folder = self.path_edit.get()
        classify_type = self.classify_type.get()
        if not os.path.isdir(folder):
            messagebox.showerror("错误", "请选择有效的文件夹路径")
            return
        if classify_type == '按文件类型':
            classify_by_type(folder)
        elif classify_type == '按文件大小':
            # 示例：自定义size_ranges，实际可做成可配置
            size_ranges = {
                '小文件': (0, 1024 * 1024),           # <1MB
                '中等文件': (1024 * 1024, 10 * 1024 * 1024), # 1MB-10MB
                '大文件': (10 * 1024 * 1024, float('inf'))   # >10MB
            }
            classify_by_size(folder, size_ranges)
        elif classify_type == '按创建日期':
            classify_by_date(folder, mode='created')
        elif classify_type == 'AI智能分类':
            classify_by_ai(folder)
        else:
            messagebox.showinfo("提示", "请选择分类方式")
            return
        self.status_bar.config(text='分类完成')
        self.refresh_tree_view(folder)  # 分类后刷新文件树
        messagebox.showinfo("完成", "分类完成！")

    def on_batch_create(self):
        folder = self.path_edit.get()
        names = self.folder_names.get("1.0", tk.END).strip().splitlines()
        prefix = self.prefix_edit.get().strip()
        suffix = self.suffix_edit.get().strip()
        names = [f"{prefix}{name}{suffix}" for name in names if name]
        if not names:
            messagebox.showwarning("提示", "请输入要创建的文件夹名称")
            return
        batch_create_folders(folder, names)
        self.status_bar.config(text='批量创建完成')
        messagebox.showinfo("完成", "批量创建完成！")

    def on_batch_delete(self):
        folder = self.path_edit.get()
        names = self.folder_names.get("1.0", tk.END).strip().splitlines()
        prefix = self.prefix_edit.get().strip()
        suffix = self.suffix_edit.get().strip()
        names = [f"{prefix}{name}{suffix}" for name in names if name]
        if not names:
            messagebox.showwarning("提示", "请输入要删除的文件夹名称")
            return
        batch_delete_folders(folder, names)
        self.status_bar.config(text='批量删除完成')
        messagebox.showinfo("完成", "批量删除完成！")

    def on_batch_rename(self):
        folder = self.path_edit.get()
        names = self.folder_names.get("1.0", tk.END).strip().splitlines()
        prefix = self.prefix_edit.get().strip()
        suffix = self.suffix_edit.get().strip()
        # 假设每行格式为 oldname,newname
        old_new_names = []
        for line in names:
            parts = line.split(',')
            if len(parts) == 2:
                old = f"{prefix}{parts[0].strip()}{suffix}"
                new = f"{prefix}{parts[1].strip()}{suffix}"
                old_new_names.append((old, new))
        if not old_new_names:
            messagebox.showwarning("提示", "请输入重命名对（格式：原名,新名）")
            return
        batch_rename_folders(folder, old_new_names)
        self.status_bar.config(text='批量重命名完成')
        messagebox.showinfo("完成", "批量重命名完成！")

    def on_search(self):
        folder = self.path_edit.get()
        search_type = self.search_type.get()
        keyword = self.search_edit.get().strip()
        if search_type == '名称搜索':
            result = search_folders(folder, name=keyword)
        elif search_type == '文件名搜索':
            result = search_files(folder, name=keyword)
        elif search_type == 'AI智能搜索':
            result = ai_search(folder, keyword)
        else:
            result = []
        if result:
            msg = "搜索结果：\n" + "\n".join(result)
        else:
            msg = "未找到符合条件的文件或文件夹"
        messagebox.showinfo("搜索结果", msg)

    # 删除自定义规则相关回调
    def on_edit_rules(self):
        pass

    def on_preview_classify(self):
        folder = self.path_edit.get()
        classify_type = self.classify_type.get()
        if not os.path.isdir(folder):
            messagebox.showerror("错误", "请选择有效的文件夹路径")
            return

        preview_result = []
        files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        if not files:
            messagebox.showinfo("提示", "该目录下没有可分类的文件")
            return

        if classify_type == '按文件类型':
            type_map = {
                '文档': ['.doc', '.docx', '.pdf', '.txt', '.xls', '.xlsx', '.ppt', '.pptx'],
                '图片': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
                '视频': ['.mp4', '.avi', '.mov', '.wmv'],
            }
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                found = False
                for k, v in type_map.items():
                    if ext in v:
                        preview_result.append(f"{f}  →  {k}")
                        found = True
                        break
                if not found:
                    preview_result.append(f"{f}  →  其它")
        elif classify_type == '按文件大小':
            size_ranges = {
                '小文件': (0, 1024 * 1024),           # <1MB
                '中等文件': (1024 * 1024, 10 * 1024 * 1024), # 1MB-10MB
                '大文件': (10 * 1024 * 1024, float('inf'))   # >10MB
            }
            for f in files:
                size = os.path.getsize(os.path.join(folder, f))
                found = False
                for label, (min_s, max_s) in size_ranges.items():
                    if min_s <= size < max_s:
                        preview_result.append(f"{f}  →  {label}")
                        found = True
                        break
                if not found:
                    preview_result.append(f"{f}  →  未知")
        elif classify_type == '按创建日期':
            for f in files:
                path = os.path.join(folder, f)
                t = os.path.getctime(path)
                date_str = time.strftime('%Y-%m-%d', time.localtime(t))
                preview_result.append(f"{f}  →  {date_str}")
        elif classify_type == 'AI智能分类':
            from ai_utils import classify_file_by_content
            for f in files:
                path = os.path.join(folder, f)
                label = classify_file_by_content(path)
                preview_result.append(f"{f}  →  {label}")
        else:
            messagebox.showinfo("提示", "请选择分类方式")
            return

        msg = "\n".join(preview_result)
        messagebox.showinfo("分类预览结果", msg)


if __name__ == '__main__':
    app = SmartFolderManagerUI()
    app.mainloop()
