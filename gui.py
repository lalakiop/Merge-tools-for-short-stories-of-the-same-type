import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES

import os
import re
from project_manager import ProjectManager
from file_utils import compute_md5, list_text_files, detect_updates, extract_chapters, replace_spaces_in_filename, copy_file_to_path, replace_space, convert_to_utf8


class NovelManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("短篇小说管理工具")
        self.root.geometry("1500x600")

        self.project_manager = None

        # 顶部按钮栏
        self.button_frame = ttk.Frame(self.root)
        self.button_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        self.btn_new_project = ttk.Button(self.button_frame, text="新建工程", command=self.create_project)
        self.btn_new_project.pack(side="left", padx=2)

        self.btn_open_project = ttk.Button(self.button_frame, text="导入工程", command=self.open_project)
        self.btn_open_project.pack(side="left", padx=2)

        self.btn_import_novel = ttk.Button(self.button_frame, text="导入小说", command=self.import_novel)
        self.btn_import_novel.pack(side="left", padx=2)
        
        # 导出按钮
        self.btn_merge_novel = ttk.Button(self.button_frame, text="合并小说", command=self.merge_novels)
        self.btn_merge_novel.pack(side="left", padx=2)
        
        # 删除按钮
        self.btn_remove_novel = ttk.Button(self.button_frame, text="删除小说", command=self.delete_selected_novel)
        self.btn_remove_novel.pack(side="left", padx=2)
       
        # 配置列权重，让左侧和中间宽度为右侧的三分之一
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=3)
        self.root.columnconfigure(2, weight=1)
        # 配置行权重，让主体部分能垂直扩展
        self.root.rowconfigure(1, weight=1)

        # 左侧：小说列表
        self.novel_frame = ttk.Frame(self.root)
        self.novel_frame.grid(row=1, column=0, sticky="nsew")

        self.novel_tree = ttk.Treeview(self.novel_frame, columns=("novel"), show="tree")
        # 设置列宽
        self.novel_tree.column("#0", width=400)
        self.novel_vscroll = ttk.Scrollbar(self.novel_frame, orient="vertical", command=self.novel_tree.yview)
        self.novel_hscroll = ttk.Scrollbar(self.novel_frame, orient="horizontal", command=self.novel_tree.xview)
        self.novel_tree.configure(yscrollcommand=self.novel_vscroll.set, xscrollcommand=self.novel_hscroll.set)

        self.novel_vscroll.pack(side="right", fill="y")
        self.novel_hscroll.pack(side="bottom", fill="x")
        self.novel_tree.pack(side="left", fill="both", expand=True)
        self.novel_tree.bind("<<TreeviewSelect>>", self.load_chapters)

        

        # 中间：章节列表
        self.chapter_frame = ttk.Frame(self.root)
        self.chapter_frame.grid(row=1, column=1, sticky="nsew")

        self.chapter_tree = ttk.Treeview(self.chapter_frame, columns=("chapter"), show="tree")
        # 设置列宽
        self.chapter_tree.column("#0", width=400)
        self.chapter_vscroll = ttk.Scrollbar(self.chapter_frame, orient="vertical", command=self.chapter_tree.yview)
        self.chapter_hscroll = ttk.Scrollbar(self.chapter_frame, orient="horizontal", command=self.chapter_tree.xview)
        self.chapter_tree.configure(yscrollcommand=self.chapter_vscroll.set, xscrollcommand=self.chapter_hscroll.set)

        self.chapter_vscroll.pack(side="right", fill="y")
        self.chapter_hscroll.pack(side="bottom", fill="x")
        self.chapter_tree.pack(side="left", fill="both", expand=True)
        self.chapter_tree.bind("<<TreeviewSelect>>", self.display_content)

        # 右侧：内容显示
        self.content_frame = ttk.Frame(self.root)
        self.content_frame.grid(row=1, column=2, sticky="nsew")

        self.text_area = tk.Text(self.content_frame, wrap="word")
        self.text_vscroll = ttk.Scrollbar(self.content_frame, orient="vertical", command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=self.text_vscroll.set)
        self.text_vscroll.pack(side="right", fill="y")
        self.text_area.pack(side="left", fill="both", expand=True)
    
    def on_file_drop(self, event):
        file_path = event.data.strip()  # 去掉路径两端的空白字符
       # print(file_path)  # 打印拖拽的文件路径，检查路径是否正确

        # 处理可能包含大括号的网络路径（某些网络路径会被大括号包裹）
        if file_path.startswith('{') and file_path.endswith('}'):  # 检查路径是否被大括号包裹
            file_path = file_path[1:-1]  # 去掉路径两端的花括号

        # 确保路径指向的是一个txt文件
        if file_path.endswith(".txt"):  
            self.import_novel(file_path)  # 如果是txt文件，调用方法添加小说
        else:
            print (f"请拖放一个有效的txt文件！")  # 如果不是txt文件，弹出警告
    
    def create_project(self):
        project_path = filedialog.askdirectory(title="选择工程文件夹")
        if project_path:
            self.project_manager = ProjectManager(project_path)
            #创建放置小说的文件夹
            novels_folder = os.path.join(project_path, 'novels')
            #print(novels_folder)
            if not os.path.exists(novels_folder):
                
                os.makedirs(novels_folder, exist_ok=True)
               
            messagebox.showinfo("成功", "工程已创建！")
            self.refresh_novel_list()

    def open_project(self):
        project_path = filedialog.askdirectory(title="选择工程文件夹")
        if project_path:
            self.project_manager = ProjectManager(project_path)
            messagebox.showinfo("成功", "工程加载成功！")
            self.refresh_novel_list()

    def import_novel(self,new_path=None):
        """导入小说文件"""
        if not self.project_manager:
            messagebox.showerror("错误", "请先创建或打开工程")
            return
        if not new_path:
            new_path = filedialog.askopenfilename(filetypes=[("文本文件", "*.txt")])
        # 选择小说文件
        
        project_path = os.path.join(self.project_manager.project_path, "cache")
        file_path = copy_file_to_path(new_path, project_path)  # 复制新文件
        convert_to_utf8(file_path)
        new_path=file_path
        if not new_path:
            return

        # 获取原始文件名，并转换为标准格式（空格替换为 '-'）
        new_filename = replace_spaces_in_filename(os.path.basename(new_path))

        # 查找同名小说（基于文件名匹配，空格替换后）
        existing_novel = next(
            (n for n in self.project_manager.get_novels() if replace_spaces_in_filename(os.path.basename(n["path"])) == new_filename), 
            None
        )

        if existing_novel:
            # 进行更新检测
            updated, new_md5 = detect_updates(existing_novel, new_path)

            if updated:
                messagebox.showinfo("检测到更新", f"《{existing_novel['name']}》有更新，正在更新……")

                # 复制新文件到工程文件夹
                project_path = os.path.join(self.project_manager.project_path, "novels")
                file_path = copy_file_to_path(new_path, project_path)  # 复制新文件

                if file_path:
                    # 更新 MD5 和路径
                    existing_novel["md5"] = new_md5
                    existing_novel["path"] = file_path  

                    # 保存工程
                    self.project_manager.save_project()
                    self.refresh_novel_list()
            else:
                messagebox.showinfo("提示", f"《{existing_novel['name']}》无变化")

        else:
            # 复制新小说到工程
            project_path = os.path.join(self.project_manager.project_path, "novels")
            file_path = copy_file_to_path(new_path, project_path)

            if file_path:
                # 添加小说信息
                self.project_manager.add_novel(file_path)
                self.refresh_novel_list()


    def refresh_novel_list(self):
        """
        刷新小说列表的函数。
        此函数会清空当前显示的小说列表，然后从项目管理器中获取最新的小说信息，并将其添加到小说列表的树形视图中。
        """
        # 清空小说列表树形视图中的所有现有条目
        # self.novel_tree.get_children() 会返回树形视图中所有子项的标识符
        # * 是解包操作符，将这些标识符作为参数传递给 delete 方法，从而删除所有子项
        self.novel_tree.delete(*self.novel_tree.get_children())

        # 检查项目管理器是否已经初始化
        if self.project_manager:
            # 遍历项目管理器中获取的所有小说信息
            for novel in self.project_manager.get_novels():
                # 在小说列表树形视图中插入一个新的条目
                # "" 表示插入到根节点下
                # "end" 表示将新条目添加到列表的末尾
                # novel["name"] 是该条目的唯一标识符
                # text=novel["name"] 表示在树形视图中显示的文本为小说的名称
                self.novel_tree.insert("", "end", novel["name"], text=novel["name"])

    def load_chapters(self, event):
        """加载选中的小说章节，并自动展开章节列表"""
        selected_item = self.novel_tree.selection()
        
        if not selected_item:
            print("未选中任何小说")  # 调试信息
            return
        
        selected_item = selected_item[0]  # 获取第一个选中的项
        novel_name = self.novel_tree.item(selected_item, "text")
        
        if not novel_name:
            print("无法获取小说名称")  # 调试信息
            return
        
        novel_path = next((n["path"] for n in self.project_manager.get_novels() if n["name"] == novel_name), None)
        
        if not novel_path:
            print(f"未找到小说路径: {novel_name}")  # 调试信息
            return

        chapters = extract_chapters(novel_path)
        self.chapter_tree.delete(*self.chapter_tree.get_children())

        for ch in chapters:
            chapter_id = self.chapter_tree.insert("", "end", text=ch["title"], values=(ch["start_line"],))
            self.chapter_tree.see(chapter_id)  # 让章节可见


    def display_content(self, event):
        """显示选中的章节内容"""
        selected_item = self.chapter_tree.selection()
       # print(f"选中的项目{selected_item}")
        if not selected_item:
            return

        chapter_title = self.chapter_tree.item(selected_item, "text")
        #print(chapter_title)
        novel_name = self.novel_tree.item(self.novel_tree.selection(), "text").strip()
        #print(novel_name)

        novel_path = next((n["path"] for n in self.project_manager.get_novels() if n["name"] == novel_name), None)
       # print(novel_path)
        if not novel_path:
            return

        chapters = extract_chapters(novel_path)
        chapter_index = next((i for i, ch in enumerate(chapters) if ch["title"] == chapter_title), None)
        if chapter_index is None:
            return

        with open(novel_path, "r", encoding="utf-8") as f:
            content = f.readlines()

        start_line = chapters[chapter_index]["start_line"]
        end_line = chapters[chapter_index + 1]["start_line"] if chapter_index + 1 < len(chapters) else len(content)
        chapter_text = "".join(content[start_line:end_line])

        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", chapter_text)
        

    def merge_novels(self):
        """合并选定的小说并保存到一个TXT文件"""
        if not self.project_manager:
            messagebox.showerror("错误", "请先创建或打开工程")
            return

        # 获取工程根目录路径和文件夹名字
        project_root_path = self.project_manager.project_path
        project_folder_name = os.path.basename(project_root_path)

        # 构建保存路径
        save_path = os.path.join(project_root_path, f"{project_folder_name}.txt")
        if not save_path:
            return

        novels = self.project_manager.get_novels()

        if not novels:
            messagebox.showerror("错误", "当前工程没有可合并的小说")
            return

        try:
            with open(save_path, "w", encoding="utf-8") as output_file:
                chapter_counter = 1  # 全局章节编号

                # 按顺序遍历每个小说
                for novel in sorted(novels, key=lambda n: n.get("order", 0)):
                    novel_path = novel["path"]
                    novel_name = novel["name"]

                    with open(novel_path, "r", encoding="utf-8") as f:
                        content = f.readlines()
                        chapters = extract_chapters(novel_path)

                        # 遍历当前小说的每个章节
                        for i, chapter in enumerate(chapters):
                            raw_title = chapter["title"].strip()

                            # 处理章节标题格式
                            match = re.match(r"^第(\d+)章\s*(.*)", raw_title)
                            if match:
                                chapter_num = match.group(1)
                                chapter_name = match.group(2).strip()
                                # 判断是否有章节名称
                                if chapter_name:
                                    processed_title = chapter_name
                                else:
                                    processed_title = f"第{chapter_num}章"
                            else:
                                processed_title = raw_title  # 保留非标准格式的标题

                            # 构建新章节标题
                            new_header = f"第{chapter_counter}章-{novel_name}-{processed_title}\n"
                            
                            # 确定内容范围（跳过原章节标题行）
                            start_line = chapter["start_line"]
                            content_start = start_line + 1  # 跳过原标题行
                            
                            # 计算结束行
                            if i + 1 < len(chapters):
                                end_line = chapters[i+1]["start_line"]
                            else:
                                end_line = len(content)
                            
                            # 提取章节内容（排除原标题行）
                            chapter_content = content[content_start:end_line]

                            # 写入新标题和内容
                            output_file.write(new_header)
                            output_file.writelines(chapter_content)
                            output_file.write("\n\n")  # 章节间空两行

                            chapter_counter += 1

            messagebox.showinfo("成功", f"合并完成，文件保存至：{save_path}")

        except Exception as e:
            messagebox.showerror("错误", f"合并过程中发生错误：{str(e)}")

    def delete_selected_novel(self):
        if not self.project_manager:
            messagebox.showerror("错误", "请先打开工程")
            return

        selected = self.novel_tree.selection()
        if not selected:
            messagebox.showerror("错误", "请先选择要删除的小说")
            return

        novel_name = self.novel_tree.item(selected[0], "text")
        if not novel_name:
            return

        # 确认对话框
        confirm = messagebox.askyesno(
            "确认删除",
            f"确定要删除《{novel_name}》吗？\n（该操作不会删除原始文件）",
            parent=self.root
        )
        
        if confirm:
            success = self.project_manager.remove_novel(novel_name)
            if success:
                # 清除相关显示
                self.chapter_tree.delete(*self.chapter_tree.get_children())
                self.text_area.delete("1.0", tk.END)
                # 刷新列表
                self.refresh_novel_list()
                messagebox.showinfo("成功", "小说已从工程移除")
            else:
                messagebox.showerror("错误", "删除失败，小说不存在")



if __name__ == "__main__":
    root = tk.Tk()
    app = NovelManagerGUI(root)
    root.mainloop()
    