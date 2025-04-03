import os
import json
from file_utils import compute_md5, list_text_files, detect_updates, extract_chapters


class ProjectManager:
    def __init__(self, project_path):
        self.project_path = project_path  # 设定工程路径
        self.project_file = os.path.join(project_path, "project.json")  # 工程配置文件路径
        self.novels = []  # 存储小说信息
        self.last_viewed = {}  # 存储上次查看的章节

        # 加载工程（注意去掉 `project_path` 参数，因为已经有 `self.project_path`）
        self.load_project()
        self.get_project_root_folder_name()
        
    def get_project_root_folder_name(self):
        """获取工程根目录文件夹的名字"""
        return os.path.basename(self.project_path)
        
    def load_project(self):
        """加载工程信息并自动修正路径"""
        if not os.path.exists(self.project_file):
            return

        with open(self.project_file, "r", encoding="utf-8") as f:
            project_data = json.load(f)

        self.novels = project_data.get("novels", [])
        self.last_viewed = project_data.get("last_viewed", {})

        # 自动路径修正
        for novel in self.novels:
            old_path = novel["path"]
            
            # 提取相对novels目录后的路径部分
            parts = old_path.split("novels" + os.sep)[0]
            
            if len(parts) > 1:
                relative_path = parts
                #print(f"relative_path:{relative_path}")
                new_base = os.path.join(self.project_path, "novels")
                new_path = os.path.join(new_base, os.path.basename(relative_path))
               
                
                # 如果新路径存在则更新
                if os.path.exists(new_path):
                    novel["path"] = new_path.replace("\\", "/")  # 统一使用斜杠
                    
        # 如果检测到修改则自动保存
        if any(novel["path"].startswith(self.project_path) for novel in self.novels):
            self.save_project()


    def save_project(self):
        """保存工程的状态，包括小说路径、排序、MD5 以及上次查看章节"""
        project_data = {
            "novels": self.novels,
            "last_viewed": self.last_viewed  # 记录用户上次查看的小说和章节
        }
        
        with open(self.project_file, "w", encoding="utf-8") as f:
            json.dump(project_data, f, ensure_ascii=False, indent=4)


    def add_novel(self, novel_path):
        """添加小说文件到工程"""
        novel_name = os.path.basename(novel_path)
        md5=compute_md5(novel_path)
        novel_entry = {"name": novel_name, "path": novel_path, "md5": md5, "chapters": []}
        
        if novel_entry not in self.novels:
            self.novels.append(novel_entry)
            self.save_project()
            return True
        return False

    def remove_novel(self, novel_name):
        """从工程中移除小说并删除文件"""
        removed_novels = [n for n in self.novels if n["name"] == novel_name]
        self.novels = [n for n in self.novels if n["name"] != novel_name]
        
        if removed_novels:
            try:
                os.remove(removed_novels[0]["path"])
            except Exception as e:
                print(f"文件删除失败: {str(e)}")
            
            self.save_project()
            return True
        return False
    
    def get_novels(self):
        """返回小说列表"""
        return self.novels
