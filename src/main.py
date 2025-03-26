import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import random
import subprocess
import threading
from typing import List, Optional
import json
import math

class VideoMixerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("TikTok视频混剪工具")
        self.root.geometry("800x600")
        
        # 配置文件路径
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        
        # 状态变量
        self.selected_folder: Optional[str] = None
        self.output_folder: Optional[str] = None
        self.sound_effect_path: Optional[str] = None  # 新增：音效文件路径
        self.video_files: List[str] = []
        self.processing = False
        
        # 加载配置
        self._load_config()
        
        self._create_widgets()
        self._setup_layout()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.selected_folder = config.get('input_folder', '')
                    self.output_folder = config.get('output_folder', '')
                    self.sound_effect_path = config.get('sound_effect_path', '')  # 新增：加载音效路径
        except Exception as e:
            print(f"加载配置文件失败: {e}")
    
    def _save_config(self):
        """保存配置文件"""
        try:
            config = {
                'input_folder': self.selected_folder or '',
                'output_folder': self.output_folder or '',
                'sound_effect_path': self.sound_effect_path or ''  # 新增：保存音效路径
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def _create_widgets(self):
        # 文件夹选择区域
        self.folder_frame = ttk.LabelFrame(self.root, text="文件夹选择", padding=5)
        
        # 输入文件夹选择
        self.input_frame = ttk.Frame(self.folder_frame)
        ttk.Label(self.input_frame, text="输入文件夹:").pack(side="left", padx=5)
        self.folder_path = tk.StringVar(value=self.selected_folder or '')  # 设置初始值
        self.folder_entry = ttk.Entry(self.input_frame, textvariable=self.folder_path, width=50)
        self.folder_entry.pack(side="left", expand=True, fill="x", padx=5)
        self.browse_btn = ttk.Button(self.input_frame, text="浏览", command=self._browse_input_folder)
        self.browse_btn.pack(side="left", padx=5)
        
        # 输出文件夹选择
        self.output_frame = ttk.Frame(self.folder_frame)
        ttk.Label(self.output_frame, text="输出文件夹:").pack(side="left", padx=5)
        self.output_path = tk.StringVar(value=self.output_folder or '')  # 设置初始值
        self.output_entry = ttk.Entry(self.output_frame, textvariable=self.output_path, width=50)
        self.output_entry.pack(side="left", expand=True, fill="x", padx=5)
        self.output_btn = ttk.Button(self.output_frame, text="浏览", command=self._browse_output_folder)
        self.output_btn.pack(side="left", padx=5)
        
        # 参数设置区域
        self.params_frame = ttk.LabelFrame(self.root, text="参数设置", padding=5)
        
        # 新增：模式选择区域
        self.mode_frame = ttk.Frame(self.params_frame)
        self.mode_frame.grid(row=0, column=0, columnspan=6, padx=5, pady=5, sticky="ew")
        
        self.mode_var = tk.StringVar(value="manual")  # 手动模式/自动模式
        
        self.manual_mode_radio = ttk.Radiobutton(
            self.mode_frame,
            text="手动设置片段参数",
            variable=self.mode_var,
            value="manual",
            command=self._update_mode_state
        )
        self.manual_mode_radio.pack(side="left", padx=5)
        
        self.auto_mode_radio = ttk.Radiobutton(
            self.mode_frame,
            text="按总时长自动计算",
            variable=self.mode_var,
            value="auto",
            command=self._update_mode_state
        )
        self.auto_mode_radio.pack(side="left", padx=5)
        
        # 手动模式参数（原有）
        self.manual_frame = ttk.Frame(self.params_frame)
        self.manual_frame.grid(row=1, column=0, columnspan=6, padx=5, pady=5, sticky="ew")
        
        self.duration_var = tk.StringVar(value="5")
        self.clips_var = tk.StringVar(value="10")
        self.total_duration_var = tk.StringVar(value="总时长: 0 秒")
        
        ttk.Label(self.manual_frame, text="片段时长(秒):").pack(side="left", padx=5)
        self.duration_entry = ttk.Entry(self.manual_frame, textvariable=self.duration_var, width=10)
        self.duration_entry.pack(side="left", padx=5)
        
        ttk.Label(self.manual_frame, text="片段数量:").pack(side="left", padx=5)
        self.clips_entry = ttk.Entry(self.manual_frame, textvariable=self.clips_var, width=10)
        self.clips_entry.pack(side="left", padx=5)
        
        self.calc_btn = ttk.Button(self.manual_frame, text="计算总时长", command=self._calculate_total)
        self.calc_btn.pack(side="left", padx=5)
        
        ttk.Label(self.manual_frame, textvariable=self.total_duration_var).pack(side="left", padx=5)
        
        # 自动模式参数（新增）
        self.auto_frame = ttk.Frame(self.params_frame)
        self.auto_frame.grid(row=2, column=0, columnspan=6, padx=5, pady=5, sticky="ew")
        
        self.target_duration_var = tk.StringVar(value="60")  # 目标总时长
        self.auto_duration_var = tk.StringVar(value="5")  # 建议片段时长
        self.auto_clips_var = tk.StringVar(value="12")  # 建议片段数量
        
        ttk.Label(self.auto_frame, text="目标总时长(秒):").pack(side="left", padx=5)
        self.target_duration_entry = ttk.Entry(self.auto_frame, textvariable=self.target_duration_var, width=10)
        self.target_duration_entry.pack(side="left", padx=5)
        
        self.auto_calc_btn = ttk.Button(self.auto_frame, text="自动计算参数", command=self._auto_calculate)
        self.auto_calc_btn.pack(side="left", padx=5)
        
        ttk.Label(self.auto_frame, text="建议片段时长:").pack(side="left", padx=5)
        ttk.Label(self.auto_frame, textvariable=self.auto_duration_var).pack(side="left", padx=5)
        ttk.Label(self.auto_frame, text="秒").pack(side="left")
        
        ttk.Label(self.auto_frame, text="建议片段数量:").pack(side="left", padx=5)
        ttk.Label(self.auto_frame, textvariable=self.auto_clips_var).pack(side="left", padx=5)
        ttk.Label(self.auto_frame, text="个").pack(side="left")
        
        # 其他参数（原有）
        self.other_params_frame = ttk.Frame(self.params_frame)
        self.other_params_frame.grid(row=3, column=0, columnspan=6, padx=5, pady=5, sticky="ew")
        
        self.generate_count_var = tk.StringVar(value="1")
        self.output_name_var = tk.StringVar(value="混剪视频")
        
        ttk.Label(self.other_params_frame, text="生成数量:").pack(side="left", padx=5)
        self.generate_count_entry = ttk.Entry(self.other_params_frame, textvariable=self.generate_count_var, width=10)
        self.generate_count_entry.pack(side="left", padx=5)
        
        ttk.Label(self.other_params_frame, text="输出文件名:").pack(side="left", padx=5)
        self.output_name_entry = ttk.Entry(self.other_params_frame, textvariable=self.output_name_var, width=20)
        self.output_name_entry.pack(side="left", padx=5, expand=True, fill="x")
        
        # 第三行参数
        self.voice_only_var = tk.BooleanVar(value=False)
        self.no_audio_var = tk.BooleanVar(value=False)
        
        self.voice_only_check = ttk.Checkbutton(
            self.params_frame, 
            text="仅保留人声（去除背景音乐）",
            variable=self.voice_only_var,
            command=self._update_audio_options
        )
        self.voice_only_check.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # 新增：完全无声选项
        self.no_audio_check = ttk.Checkbutton(
            self.params_frame, 
            text="完全去除音频",
            variable=self.no_audio_var,
            command=self._update_audio_options
        )
        self.no_audio_check.grid(row=4, column=2, columnspan=2, padx=5, pady=5, sticky="w")
        
        # 新增：音效设置区域（第四行）
        self.sound_effect_frame = ttk.Frame(self.params_frame)
        self.sound_effect_frame.grid(row=5, column=0, columnspan=6, padx=5, pady=5, sticky="ew")
        
        # 音效类型选择
        self.sound_effect_type_var = tk.StringVar(value="none")  # 新增：音效类型选择
        
        self.no_effect_radio = ttk.Radiobutton(
            self.sound_effect_frame,
            text="不添加音效",
            variable=self.sound_effect_type_var,
            value="none",
            command=self._update_sound_effect_state
        )
        self.no_effect_radio.pack(side="left", padx=5)
        
        self.clip_effect_radio = ttk.Radiobutton(
            self.sound_effect_frame,
            text="每个片段添加音效",
            variable=self.sound_effect_type_var,
            value="clips",
            command=self._update_sound_effect_state
        )
        self.clip_effect_radio.pack(side="left", padx=5)
        
        self.video_effect_radio = ttk.Radiobutton(
            self.sound_effect_frame,
            text="仅在视频开头添加音效",
            variable=self.sound_effect_type_var,
            value="video",
            command=self._update_sound_effect_state
        )
        self.video_effect_radio.pack(side="left", padx=5)
        
        self.sound_effect_path_var = tk.StringVar(value=self.sound_effect_path or '')
        self.sound_effect_entry = ttk.Entry(
            self.sound_effect_frame,
            textvariable=self.sound_effect_path_var,
            width=40,
            state="disabled"
        )
        self.sound_effect_entry.pack(side="left", expand=True, fill="x", padx=5)
        
        self.sound_effect_btn = ttk.Button(
            self.sound_effect_frame,
            text="选择音效",
            command=self._browse_sound_effect,
            state="disabled"
        )
        self.sound_effect_btn.pack(side="left", padx=5)
        
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
        folder = filedialog.askdirectory(initialdir=self.selected_folder)  # 设置初始目录
        if folder:
            self.selected_folder = folder
            self.folder_path.set(folder)
            self._load_videos()
            self._save_config()  # 保存配置
    
    def _browse_output_folder(self):
        folder = filedialog.askdirectory(initialdir=self.output_folder)  # 设置初始目录
        if folder:
            self.output_folder = folder
            self.output_path.set(folder)
            self._save_config()  # 保存配置
    
    def _load_videos(self):
        # 如果没有选择文件夹但有保存的路径，使用保存的路径
        if not self.selected_folder and self.folder_path.get():
            self.selected_folder = self.folder_path.get()
        
        if not self.selected_folder:
            return
            
        # 清空现有列表
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 加载视频文件
        video_extensions = ('.mp4', '.mov', '.avi')
        try:
            self.video_files = [
                f for f in os.listdir(self.selected_folder)
                if f.lower().endswith(video_extensions)
            ]
            
            # 添加到树形视图
            for file in self.video_files:
                self.tree.insert("", "end", values=("✓", file))
        except Exception as e:
            messagebox.showerror("错误", f"加载视频文件失败: {str(e)}")
            self.video_files = []
    
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
            # 根据当前模式获取参数
            if self.mode_var.get() == "auto":
                # 使用自动计算的参数
                duration = float(self.auto_duration_var.get())
                clips = int(self.auto_clips_var.get())
            else:
                # 使用手动设置的参数
                duration = float(self.duration_var.get())
                clips = int(self.clips_var.get())
            
            generate_count = int(self.generate_count_var.get())
            if generate_count < 1:
                raise ValueError("生成数量必须大于0")
                
        except ValueError as e:
            messagebox.showerror("错误", str(e) if str(e) else "请输入有效的参数")
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
        thread = threading.Thread(target=self._process_videos, args=(selected_videos, duration, clips, temp_dir, generate_count))
        thread.daemon = True
        thread.start()
    
    def _update_audio_options(self):
        """更新音频选项的互斥状态"""
        if self.no_audio_var.get():
            self.voice_only_var.set(False)
            self.voice_only_check.state(['disabled'])
        elif self.voice_only_var.get():
            self.no_audio_var.set(False)
            self.no_audio_check.state(['disabled'])
        else:
            self.voice_only_check.state(['!disabled'])
            self.no_audio_check.state(['!disabled'])

    def _update_sound_effect_state(self):
        """更新音效相关控件的状态"""
        if self.sound_effect_type_var.get() != "none":
            self.sound_effect_entry.configure(state="normal")
            self.sound_effect_btn.configure(state="normal")
        else:
            self.sound_effect_entry.configure(state="disabled")
            self.sound_effect_btn.configure(state="disabled")
    
    def _browse_sound_effect(self):
        """选择音效文件"""
        filetypes = (
            ("音频文件", "*.mp3;*.wav;*.aac;*.m4a"),
            ("所有文件", "*.*")
        )
        file_path = filedialog.askopenfilename(
            title="选择音效文件",
            filetypes=filetypes,
            initialdir=os.path.dirname(self.sound_effect_path) if self.sound_effect_path else None
        )
        if file_path:
            self.sound_effect_path = file_path
            self.sound_effect_path_var.set(file_path)
            self._save_config()

    def _process_videos(self, videos: List[str], duration: float, clips: int, temp_dir: str, generate_count: int):
        try:
            base_name = self.output_name_var.get()
            voice_only = self.voice_only_var.get()
            no_audio = self.no_audio_var.get()
            sound_effect_type = self.sound_effect_type_var.get()
            sound_effect_path = self.sound_effect_path if sound_effect_type != "none" else None
            
            for video_index in range(generate_count):
                # 随机选择视频
                selected_clips = random.sample(videos, clips)
                temp_files = []
                
                # 处理每个视频片段
                for i, video in enumerate(selected_clips, 1):
                    self.status_var.set(f"处理第 {video_index + 1}/{generate_count} 个视频的片段 {i}/{clips}")
                    input_path = os.path.join(self.selected_folder, video)
                    temp_path = os.path.join(temp_dir, f"temp_{video_index}_{i}.mp4")
                    processed_path = os.path.join(temp_dir, f"processed_{video_index}_{i}.mp4")
                    output_path = os.path.join(temp_dir, f"clip_{video_index}_{i}.mp4")
                    temp_files.append(output_path)
                    
                    # 首先裁剪视频片段
                    if no_audio:
                        # 完全去除音频
                        cmd = [
                            "ffmpeg", "-y",
                            "-i", input_path,
                            "-t", str(duration),
                            "-vf", "scale=w=1080:h=1920:force_original_aspect_ratio=decrease,"
                                  "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
                            "-an",  # 去除音频
                            "-c:v", "libx264",
                            "-preset", "medium",
                            "-crf", "18",
                            processed_path
                        ]
                    else:
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
                            processed_path
                        ]
                    subprocess.run(cmd, check=True)
                    
                    if not no_audio and voice_only:
                        # 使用FFmpeg的语音分离功能处理音频
                        cmd = [
                            "ffmpeg", "-y",
                            "-i", processed_path,
                            "-af", "pan=stereo|c0=c0,lowpass=3000,highpass=200",
                            "-c:v", "copy",
                            temp_path
                        ]
                        subprocess.run(cmd, check=True)
                        os.remove(processed_path)
                        processed_path = temp_path
                    
                    if sound_effect_type == "clips" and sound_effect_path:
                        # 在每个片段开头添加音效
                        cmd = [
                            "ffmpeg", "-y",
                            "-i", processed_path,
                            "-i", sound_effect_path,
                            "-filter_complex", "[1:a]adelay=0|0[delayed];[0:a][delayed]amix=inputs=2:duration=first",
                            "-c:v", "copy",
                            output_path
                        ]
                        subprocess.run(cmd, check=True)
                        if os.path.exists(processed_path):
                            os.remove(processed_path)
                    else:
                        # 如果不需要添加音效，直接使用处理后的视频
                        os.rename(processed_path, output_path)
                
                # 合并视频片段
                self.status_var.set(f"合并第 {video_index + 1}/{generate_count} 个视频...")
                
                # 创建文件列表
                list_file = os.path.join(temp_dir, f"list_{video_index}.txt")
                with open(list_file, "w", encoding="utf-8") as f:
                    for temp_file in temp_files:
                        f.write(f"file '{temp_file}'\n")
                
                # 合并视频
                merged_path = os.path.join(temp_dir, f"merged_{video_index}.mp4")
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", list_file,
                    "-c", "copy",
                    merged_path
                ]
                subprocess.run(cmd, check=True)
                
                # 如果需要在完整视频开头添加音效
                output_file = os.path.join(self.output_folder, f"{base_name}-{video_index + 1}.mp4")
                if sound_effect_type == "video" and sound_effect_path:
                    cmd = [
                        "ffmpeg", "-y",
                        "-i", merged_path,
                        "-i", sound_effect_path,
                        "-filter_complex", "[1:a]adelay=0|0[delayed];[0:a][delayed]amix=inputs=2:duration=first",
                        "-c:v", "copy",
                        output_file
                    ]
                    subprocess.run(cmd, check=True)
                    os.remove(merged_path)
                else:
                    os.rename(merged_path, output_file)
                
                # 删除临时文件
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                os.remove(list_file)
            
            # 删除临时文件夹
            os.rmdir(temp_dir)
            
            self.status_var.set("处理完成!")
            self.processing = False
            messagebox.showinfo("完成", f"已成功生成 {generate_count} 个混剪视频!")
            
        except subprocess.CalledProcessError as e:
            self.status_var.set("处理出错!")
            self.processing = False
            messagebox.showerror("错误", f"视频处理失败: {str(e)}")
            
        except Exception as e:
            self.status_var.set("处理出错!")
            self.processing = False
            messagebox.showerror("错误", f"发生错误: {str(e)}")
        
        finally:
            # 确保清理临时文件
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    try:
                        os.remove(os.path.join(temp_dir, file))
                    except:
                        pass
                try:
                    os.rmdir(temp_dir)
                except:
                    pass

    def _update_mode_state(self):
        """更新模式相关控件的状态"""
        if self.mode_var.get() == "manual":
            # 启用手动模式控件
            self.duration_entry.configure(state="normal")
            self.clips_entry.configure(state="normal")
            self.calc_btn.configure(state="normal")
            # 禁用自动模式控件
            self.target_duration_entry.configure(state="disabled")
            self.auto_calc_btn.configure(state="disabled")
        else:
            # 禁用手动模式控件
            self.duration_entry.configure(state="disabled")
            self.clips_entry.configure(state="disabled")
            self.calc_btn.configure(state="disabled")
            # 启用自动模式控件
            self.target_duration_entry.configure(state="normal")
            self.auto_calc_btn.configure(state="normal")
    
    def _auto_calculate(self):
        """自动计算片段参数"""
        try:
            target_duration = float(self.target_duration_var.get())
            if target_duration <= 0:
                raise ValueError("目标时长必须大于0")
            
            # 使用5秒作为默认片段时长
            default_clip_duration = 5
            
            # 计算建议的片段数量（向上取整）
            suggested_clips = math.ceil(target_duration / default_clip_duration)
            
            # 计算实际的片段时长
            suggested_duration = target_duration / suggested_clips
            
            # 更新显示
            self.auto_duration_var.set(f"{suggested_duration:.1f}")
            self.auto_clips_var.set(str(suggested_clips))
            
            # 同步到手动模式的输入框
            self.duration_var.set(f"{suggested_duration:.1f}")
            self.clips_var.set(str(suggested_clips))
            
            # 更新总时长显示
            self.total_duration_var.set(f"总时长: {target_duration:.1f} 秒")
            
        except ValueError as e:
            messagebox.showerror("错误", "请输入有效的目标时长")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoMixerApp(root)
    root.mainloop() 