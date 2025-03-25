import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import random
import subprocess
import threading
from typing import List, Optional
import json

class VideoMixerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("TikTok视频混剪工具")
        self.root.geometry("800x600")
        
        # 状态变量
        self.selected_folder: Optional[str] = None
        self.output_folder: Optional[str] = None
        self.video_files: List[str] = []
        self.processing = False
        
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        # 文件夹选择区域
        self.folder_frame = ttk.LabelFrame(self.root, text="文件夹选择", padding=5)
        
        # 输入文件夹选择
        self.input_frame = ttk.Frame(self.folder_frame)
        ttk.Label(self.input_frame, text="输入文件夹:").pack(side="left", padx=5)
        self.folder_path = tk.StringVar()
        self.folder_entry = ttk.Entry(self.input_frame, textvariable=self.folder_path, width=50)
        self.folder_entry.pack(side="left", expand=True, fill="x", padx=5)
        self.browse_btn = ttk.Button(self.input_frame, text="浏览", command=self._browse_input_folder)
        self.browse_btn.pack(side="left", padx=5)
        
        # 输出文件夹选择
        self.output_frame = ttk.Frame(self.folder_frame)
        ttk.Label(self.output_frame, text="输出文件夹:").pack(side="left", padx=5)
        self.output_path = tk.StringVar()
        self.output_entry = ttk.Entry(self.output_frame, textvariable=self.output_path, width=50)
        self.output_entry.pack(side="left", expand=True, fill="x", padx=5)
        self.output_btn = ttk.Button(self.output_frame, text="浏览", command=self._browse_output_folder)
        self.output_btn.pack(side="left", padx=5)
        
        # 参数设置区域
        self.params_frame = ttk.LabelFrame(self.root, text="参数设置", padding=5)
        self.duration_var = tk.StringVar(value="5")
        self.clips_var = tk.StringVar(value="10")
        self.total_duration_var = tk.StringVar(value="总时长: 0 秒")
        
        ttk.Label(self.params_frame, text="片段时长(秒):").grid(row=0, column=0, padx=5)
        self.duration_entry = ttk.Entry(self.params_frame, textvariable=self.duration_var, width=10)
        self.duration_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(self.params_frame, text="片段数量:").grid(row=0, column=2, padx=5)
        self.clips_entry = ttk.Entry(self.params_frame, textvariable=self.clips_var, width=10)
        self.clips_entry.grid(row=0, column=3, padx=5)
        
        self.calc_btn = ttk.Button(self.params_frame, text="计算总时长", command=self._calculate_total)
        self.calc_btn.grid(row=0, column=4, padx=5)
        
        ttk.Label(self.params_frame, textvariable=self.total_duration_var).grid(row=0, column=5, padx=5)
        
        # 视频列表区域
        self.list_frame = ttk.LabelFrame(self.root, text="视频列表", padding=5)
        
        # 创建Treeview
        self.tree = ttk.Treeview(self.list_frame, columns=("checked", "filename"), show="headings")
        self.tree.heading("checked", text="选择")
        self.tree.heading("filename", text="文件名")
        self.tree.column("checked", width=50)
        self.tree.column("filename", width=500)
        
        # 添加滚动条
        self.scrollbar = ttk.Scrollbar(self.list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        # 按钮区域
        self.button_frame = ttk.Frame(self.list_frame)
        self.select_all_btn = ttk.Button(self.button_frame, text="全选", command=self._select_all)
        self.deselect_all_btn = ttk.Button(self.button_frame, text="取消全选", command=self._deselect_all)
        
        # 处理按钮和状态
        self.process_frame = ttk.Frame(self.root)
        self.start_btn = ttk.Button(self.process_frame, text="开始混剪", command=self._start_processing)
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(self.process_frame, textvariable=self.status_var)
        
        # 绑定事件
        self.tree.bind("<Double-1>", self._preview_video)
        self.tree.bind("<Button-1>", self._toggle_checkbox)
        
    def _setup_layout(self):
        # 文件夹选择区域布局
        self.folder_frame.pack(fill="x", padx=5, pady=5)
        self.input_frame.pack(fill="x", pady=2)
        self.output_frame.pack(fill="x", pady=2)
        
        # 参数设置区域布局
        self.params_frame.pack(fill="x", padx=5, pady=5)
        
        # 视频列表区域布局
        self.list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.tree.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # 按钮区域布局
        self.button_frame.pack(fill="x", pady=5)
        self.select_all_btn.pack(side="left", padx=5)
        self.deselect_all_btn.pack(side="left", padx=5)
        
        # 处理按钮和状态布局
        self.process_frame.pack(fill="x", padx=5, pady=5)
        self.start_btn.pack(side="left", padx=5)
        self.status_label.pack(side="left", padx=5)
    
    def _browse_input_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.selected_folder = folder
            self.folder_path.set(folder)
            self._load_videos()
    
    def _browse_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder = folder
            self.output_path.set(folder)
    
    def _load_videos(self):
        # 清空现有列表
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 加载视频文件
        video_extensions = ('.mp4', '.mov', '.avi')
        self.video_files = [
            f for f in os.listdir(self.selected_folder)
            if f.lower().endswith(video_extensions)
        ]
        
        # 添加到树形视图
        for file in self.video_files:
            self.tree.insert("", "end", values=("✓", file))
    
    def _calculate_total(self):
        try:
            duration = float(self.duration_var.get())
            clips = int(self.clips_var.get())
            total = duration * clips
            self.total_duration_var.set(f"总时长: {total:.1f} 秒")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
    
    def _toggle_checkbox(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.tree.identify_row(event.y)
            if item:
                values = self.tree.item(item)["values"]
                if values:
                    new_value = "✓" if values[0] != "✓" else " "
                    self.tree.set(item, "checked", new_value)
    
    def _select_all(self):
        for item in self.tree.get_children():
            self.tree.set(item, "checked", "✓")
    
    def _deselect_all(self):
        for item in self.tree.get_children():
            self.tree.set(item, "checked", " ")
    
    def _preview_video(self, event):
        item = self.tree.selection()[0]
        filename = self.tree.item(item)["values"][1]
        video_path = os.path.join(self.selected_folder, filename)
        if os.path.exists(video_path):
            os.startfile(video_path)
    
    def _start_processing(self):
        if not self.selected_folder or not self.video_files:
            messagebox.showerror("错误", "请先选择输入视频文件夹")
            return
            
        if not self.output_folder:
            messagebox.showerror("错误", "请选择输出文件夹")
            return
        
        try:
            duration = float(self.duration_var.get())
            clips = int(self.clips_var.get())
        except ValueError:
            messagebox.showerror("错误", "请输入有效的参数")
            return
        
        # 获取选中的视频
        selected_videos = []
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            if values[0] == "✓":
                selected_videos.append(values[1])
        
        if not selected_videos:
            messagebox.showerror("错误", "请至少选择一个视频")
            return
        
        if len(selected_videos) < clips:
            messagebox.showerror("错误", "选中的视频数量少于需要的片段数量")
            return
        
        # 创建临时文件夹
        temp_dir = os.path.join(self.output_folder, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 开始处理线程
        self.processing = True
        thread = threading.Thread(target=self._process_videos, args=(selected_videos, duration, clips, temp_dir))
        thread.daemon = True
        thread.start()
    
    def _process_videos(self, videos: List[str], duration: float, clips: int, temp_dir: str):
        try:
            # 随机选择视频
            selected_clips = random.sample(videos, clips)
            temp_files = []
            
            # 处理每个视频片段
            for i, video in enumerate(selected_clips, 1):
                self.status_var.set(f"处理片段 {i}/{clips}")
                input_path = os.path.join(self.selected_folder, video)
                output_path = os.path.join(temp_dir, f"clip_{i}.mp4")
                temp_files.append(output_path)
                
                # 裁剪并调整视频大小
                cmd = [
                    "ffmpeg", "-y",
                    "-i", input_path,
                    "-t", str(duration),
                    "-vf", "scale=w=1080:h=1920:force_original_aspect_ratio=decrease,"
                          "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "18",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    output_path
                ]
                subprocess.run(cmd, check=True)
            
            # 创建文件列表
            files_list = os.path.join(temp_dir, "files.txt")
            with open(files_list, "w") as f:
                for temp_file in temp_files:
                    f.write(f"file '{temp_file}'\n")
            
            # 合并视频
            self.status_var.set("合并视频中...")
            output_file = os.path.join(self.output_folder, "mixed_output.mp4")
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", files_list,
                "-c:v", "copy",
                "-c:a", "copy",
                output_file
            ]
            subprocess.run(cmd, check=True)
            
            # 清理临时文件
            for temp_file in temp_files:
                os.remove(temp_file)
            os.remove(files_list)
            os.rmdir(temp_dir)
            
            self.status_var.set("处理完成!")
            messagebox.showinfo("成功", f"视频混剪完成!\n输出文件: {output_file}")
            
        except Exception as e:
            self.status_var.set("处理失败")
            messagebox.showerror("错误", f"处理过程中出错: {str(e)}")
        
        finally:
            self.processing = False

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoMixerApp(root)
    root.mainloop() 