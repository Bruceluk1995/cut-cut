import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import random
import subprocess
import threading
from typing import List, Optional
import json
import math
import time

class MusicListWindow:
    def __init__(self, parent, pool_name: str, pool_path: str, music_files: list):
        self.window = tk.Toplevel(parent)
        self.window.title(f"音乐列表 - {pool_name}")
        self.window.geometry("600x400")
        
        # 创建音乐列表
        self.list_frame = ttk.Frame(self.window)
        self.list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建Treeview
        self.tree = ttk.Treeview(
            self.list_frame,
            columns=("checked", "filename", "duration"),
            show="headings",
            height=15
        )
        self.tree.heading("checked", text="选择")
        self.tree.heading("filename", text="文件名")
        self.tree.heading("duration", text="时长")
        
        self.tree.column("checked", width=50)
        self.tree.column("filename", width=400)
        self.tree.column("duration", width=100)
        
        # 添加滚动条
        self.scrollbar = ttk.Scrollbar(
            self.list_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # 按钮区域
        self.button_frame = ttk.Frame(self.window)
        self.button_frame.pack(fill="x", padx=5, pady=5)
        
        self.select_all_btn = ttk.Button(
            self.button_frame,
            text="全选",
            command=self._select_all
        )
        self.select_all_btn.pack(side="left", padx=5)
        
        self.deselect_all_btn = ttk.Button(
            self.button_frame,
            text="取消全选",
            command=self._deselect_all
        )
        self.deselect_all_btn.pack(side="left", padx=5)
        
        # 加载音乐文件
        self._load_music_files(pool_path, music_files)
        
        # 绑定事件
        self.tree.bind("<Button-1>", self._toggle_checkbox)
    
    def _load_music_files(self, pool_path: str, music_files: list):
        for file in music_files:
            file_path = os.path.join(pool_path, file)
            duration = self._get_music_duration(file_path)
            duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "未知"
            self.tree.insert("", "end", values=("✓", file, duration_str))
    
    def _get_music_duration(self, file_path: str) -> float:
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip())
        except:
            return 0
    
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

class VideoMixerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("TikTok视频混剪工具")
        self.root.geometry("1200x600")  # 增加窗口宽度以适应右侧音乐池列表
        
        # 设置自定义样式
        style = ttk.Style()
        style.configure(
            "Accent.TButton",
            font=("微软雅黑", 12, "bold"),
            padding=10,
            background="#4CAF50",  # 使用绿色背景
            foreground="black"     # 使用黑色文字
        )
        
        # 配置文件路径
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        
        # 状态变量
        self.selected_folder: Optional[str] = None
        self.output_folder: Optional[str] = None
        self.sound_effect_path: Optional[str] = None  # 新增：音效文件路径
        self.video_files: List[str] = []
        self.processing = False
        self.last_save_time = 0  # 上次保存配置的时间
        
        # 音乐池相关变量
        self.music_pools: dict = {}  # 存储音乐池路径和名称的映射
        self.music_files: dict = {}  # 存储每个音乐池的音乐文件列表
        self.selected_pool: Optional[str] = None  # 当前选中的音乐池
        
        # 加载配置
        self._load_config()
        
        self._create_widgets()
        self._setup_layout()
        
        # 启动定时更新
        self._start_auto_update()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.selected_folder = config.get('input_folder', '')
                    self.output_folder = config.get('output_folder', '')
                    self.sound_effect_path = config.get('sound_effect_path', '')
                    # 加载音乐池配置
                    self.music_pools = config.get('music_pools', {})
                    self.selected_pool = config.get('selected_pool', None)
                    # 加载每个音乐池的文件
                    self.music_files = {}
                    for pool_path in self.music_pools.values():
                        if os.path.exists(pool_path):
                            self._load_music_files(pool_path)
                    # 保存音乐池选中状态
                    self.music_pool_states = config.get('music_pool_states', {})
                    # 加载使用背景音乐的状态
                    self.use_bgm = config.get('use_bgm', False)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
    
    def _save_config(self):
        """保存配置文件"""
        try:
            # 获取音乐池选中状态
            selected_states = {}
            for name in self.music_pools.keys():
                selected_states[name] = True  # 默认选中状态
            
            config = {
                'input_folder': self.selected_folder or '',
                'output_folder': self.output_folder or '',
                'sound_effect_path': self.sound_effect_path or '',
                'music_pools': self.music_pools,  # 只保存当前存在的音乐池
                'selected_pool': self.selected_pool,
                'music_pool_states': selected_states,
                'use_bgm': self.use_bgm_var.get()
            }
            
            # 确保配置文件目录存在
            config_dir = os.path.dirname(self.config_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
    
    def _load_music_files(self, pool_path: str):
        """加载音乐池中的音乐文件"""
        if not os.path.exists(pool_path):
            return
        
        music_extensions = ('.mp3', '.wav', '.m4a', '.aac')
        try:
            # 获取所有音乐文件
            music_files = [
                f for f in os.listdir(pool_path)
                if f.lower().endswith(music_extensions)
            ]
            
            # 存储音乐文件列表
            self.music_files[pool_path] = music_files
            
        except Exception as e:
            print(f"加载音乐文件失败: {str(e)}")
            self.music_files[pool_path] = []
    
    def _create_widgets(self):
        # 创建左右分隔的主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 左侧主要内容区域
        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0,5))
        
        # 右侧音乐池列表区域
        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.pack(side="right", fill="y", padx=(5,0))
        
        # 文件夹选择区域
        self.folder_frame = ttk.LabelFrame(self.left_frame, text="文件夹选择", padding=5)
        
        # 输入文件夹选择
        self.input_frame = ttk.Frame(self.folder_frame)
        ttk.Label(self.input_frame, text="输入文件夹:").pack(side="left", padx=5)
        self.folder_path = tk.StringVar(value=self.selected_folder or '')  # 设置初始值
        self.folder_entry = ttk.Entry(self.input_frame, textvariable=self.folder_path, width=50)
        self.folder_entry.pack(side="left", expand=True, fill="x", padx=5)
        self.browse_btn = ttk.Button(self.input_frame, text="浏览", command=self._browse_input_folder)
        self.browse_btn.pack(side="left", padx=5)
        self.open_input_btn = ttk.Button(self.input_frame, text="打开输入文件夹", command=self._open_input_folder)
        self.open_input_btn.pack(side="left", padx=5)
        
        # 输出文件夹选择
        self.output_frame = ttk.Frame(self.folder_frame)
        ttk.Label(self.output_frame, text="输出文件夹:").pack(side="left", padx=5)
        self.output_path = tk.StringVar(value=self.output_folder or '')  # 设置初始值
        self.output_entry = ttk.Entry(self.output_frame, textvariable=self.output_path, width=50)
        self.output_entry.pack(side="left", expand=True, fill="x", padx=5)
        self.output_btn = ttk.Button(self.output_frame, text="浏览", command=self._browse_output_folder)
        self.output_btn.pack(side="left", padx=5)
        self.open_output_btn = ttk.Button(self.output_frame, text="打开输出文件夹", command=self._open_output_folder)
        self.open_output_btn.pack(side="left", padx=5)
        
        # 参数设置区域
        self.params_frame = ttk.LabelFrame(self.left_frame, text="参数设置", padding=10)
        
        # 新增：模式选择区域
        self.mode_frame = ttk.Frame(self.params_frame)
        self.mode_frame.pack(fill="x", pady=(0,10))
        
        self.mode_var = tk.StringVar(value="manual")  # 手动模式/自动模式
        
        self.manual_mode_radio = ttk.Radiobutton(
            self.mode_frame,
            text="手动设置片段参数",
            variable=self.mode_var,
            value="manual",
            command=self._update_mode_state
        )
        self.manual_mode_radio.pack(side="left", padx=(0,20))
        
        self.auto_mode_radio = ttk.Radiobutton(
            self.mode_frame,
            text="按总时长自动计算",
            variable=self.mode_var,
            value="auto",
            command=self._update_mode_state
        )
        self.auto_mode_radio.pack(side="left")
        
        # 手动模式参数
        self.manual_frame = ttk.Frame(self.params_frame)
        self.manual_frame.pack(fill="x", pady=(0,10))
        
        self.duration_var = tk.StringVar(value="5")
        self.clips_var = tk.StringVar(value="10")
        self.total_duration_var = tk.StringVar(value="总时长: 0 秒")
        
        # 使用Grid布局来对齐控件
        ttk.Label(self.manual_frame, text="片段时长(秒):", width=12).grid(row=0, column=0, padx=(0,5))
        self.duration_entry = ttk.Entry(self.manual_frame, textvariable=self.duration_var, width=10)
        self.duration_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(self.manual_frame, text="片段数量:", width=12).grid(row=0, column=2, padx=(20,5))
        self.clips_entry = ttk.Entry(self.manual_frame, textvariable=self.clips_var, width=10)
        self.clips_entry.grid(row=0, column=3, padx=5)
        
        self.calc_btn = ttk.Button(self.manual_frame, text="计算总时长", command=self._calculate_total)
        self.calc_btn.grid(row=0, column=4, padx=(20,5))
        
        ttk.Label(self.manual_frame, textvariable=self.total_duration_var).grid(row=0, column=5, padx=5)
        
        # 自动模式参数
        self.auto_frame = ttk.Frame(self.params_frame)
        self.auto_frame.pack(fill="x", pady=(0,10))
        
        self.target_duration_var = tk.StringVar(value="60")  # 目标总时长
        self.auto_duration_var = tk.StringVar(value="5")  # 建议片段时长
        self.auto_clips_var = tk.StringVar(value="12")  # 建议片段数量
        
        # 使用Grid布局来对齐控件
        ttk.Label(self.auto_frame, text="目标总时长(秒):", width=12).grid(row=0, column=0, padx=(0,5))
        self.target_duration_entry = ttk.Entry(self.auto_frame, textvariable=self.target_duration_var, width=10)
        self.target_duration_entry.grid(row=0, column=1, padx=5)
        
        self.auto_calc_btn = ttk.Button(self.auto_frame, text="自动计算参数", command=self._auto_calculate)
        self.auto_calc_btn.grid(row=0, column=2, padx=(20,5))
        
        ttk.Label(self.auto_frame, text="建议片段时长:").grid(row=0, column=3, padx=(20,5))
        ttk.Label(self.auto_frame, textvariable=self.auto_duration_var).grid(row=0, column=4, padx=(0,5))
        ttk.Label(self.auto_frame, text="秒").grid(row=0, column=5)
        
        ttk.Label(self.auto_frame, text="建议片段数量:").grid(row=0, column=6, padx=(20,5))
        ttk.Label(self.auto_frame, textvariable=self.auto_clips_var).grid(row=0, column=7, padx=(0,5))
        ttk.Label(self.auto_frame, text="个").grid(row=0, column=8)
        
        # 其他参数
        self.other_params_frame = ttk.Frame(self.params_frame)
        self.other_params_frame.pack(fill="x", pady=(0,10))
        
        self.generate_count_var = tk.StringVar(value="1")
        self.output_name_var = tk.StringVar(value="混剪视频")
        
        # 使用Grid布局来对齐控件
        ttk.Label(self.other_params_frame, text="生成数量:", width=12).grid(row=0, column=0, padx=(0,5))
        self.generate_count_entry = ttk.Entry(self.other_params_frame, textvariable=self.generate_count_var, width=10)
        self.generate_count_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(self.other_params_frame, text="输出文件名:", width=12).grid(row=0, column=2, padx=(20,5))
        self.output_name_entry = ttk.Entry(self.other_params_frame, textvariable=self.output_name_var, width=30)
        self.output_name_entry.grid(row=0, column=3, padx=5, sticky="ew")
        
        # 音频选项
        self.audio_frame = ttk.Frame(self.params_frame)
        self.audio_frame.pack(fill="x")
        
        self.voice_only_var = tk.BooleanVar(value=False)
        self.no_audio_var = tk.BooleanVar(value=False)
        
        self.voice_only_check = ttk.Checkbutton(
            self.audio_frame, 
            text="仅保留人声（去除背景音乐）",
            variable=self.voice_only_var,
            command=self._update_audio_options
        )
        self.voice_only_check.pack(side="left", padx=(0,20))
        
        self.no_audio_check = ttk.Checkbutton(
            self.audio_frame, 
            text="完全去除音频",
            variable=self.no_audio_var,
            command=self._update_audio_options
        )
        self.no_audio_check.pack(side="left")
        
        # 音乐池设置区域移动到右侧
        self.music_pool_frame = ttk.LabelFrame(self.right_frame, text="背景音乐设置", padding=5)
        self.music_pool_frame.pack(fill="both", expand=True, pady=5)
        
        # 音乐池控制按钮
        self.music_pool_btn_frame = ttk.Frame(self.music_pool_frame)
        self.music_pool_btn_frame.pack(fill="x", pady=2)
        
        self.add_pool_btn = ttk.Button(
            self.music_pool_btn_frame,
            text="添加音乐池",
            command=self._add_music_pool
        )
        self.add_pool_btn.pack(side="left", padx=5)
        
        self.remove_pool_btn = ttk.Button(
            self.music_pool_btn_frame,
            text="删除音乐池",
            command=self._remove_music_pool
        )
        self.remove_pool_btn.pack(side="left", padx=5)
        
        # 创建水平分割的框架
        self.music_container = ttk.Frame(self.music_pool_frame)
        self.music_container.pack(fill="both", expand=True, pady=2)
        
        # 左侧音乐池列表
        self.pool_list_frame = ttk.Frame(self.music_container)
        self.pool_list_frame.pack(side="left", fill="y", padx=(0, 5))
        
        # 创建音乐池Listbox
        self.pool_listbox = tk.Listbox(
            self.pool_list_frame,
            width=10,
            height=10,
            selectmode=tk.EXTENDED  # 改为EXTENDED支持多选
        )
        self.pool_listbox.pack(side="left", fill="y")
        
        # 音乐池滚动条
        self.pool_scrollbar = ttk.Scrollbar(
            self.pool_list_frame,
            orient="vertical",
            command=self.pool_listbox.yview
        )
        self.pool_listbox.configure(yscrollcommand=self.pool_scrollbar.set)
        self.pool_scrollbar.pack(side="right", fill="y")
        
        # 右侧音乐列表
        self.music_list_frame = ttk.Frame(self.music_container)
        self.music_list_frame.pack(side="right", fill="both", expand=True)
        
        # 创建音乐列表Treeview
        self.music_tree = ttk.Treeview(
            self.music_list_frame,
            columns=("checked", "filename", "duration"),
            show="headings",
            height=10
        )
        self.music_tree.heading("checked", text="选择")
        self.music_tree.heading("filename", text="文件名")
        self.music_tree.heading("duration", text="时长")
        
        self.music_tree.column("checked", width=50)
        self.music_tree.column("filename", width=300)
        self.music_tree.column("duration", width=80)
        
        # 音乐列表滚动条
        self.music_scrollbar = ttk.Scrollbar(
            self.music_list_frame,
            orient="vertical",
            command=self.music_tree.yview
        )
        self.music_tree.configure(yscrollcommand=self.music_scrollbar.set)
        
        self.music_tree.pack(side="left", fill="both", expand=True)
        self.music_scrollbar.pack(side="right", fill="y")
        
        # 绑定音乐池选择事件
        self.pool_listbox.bind('<<ListboxSelect>>', self._on_pool_select)
        # 绑定音乐选择事件
        self.music_tree.bind("<Button-1>", self._toggle_music)
        
        # 音频处理选项
        self.audio_options_frame = ttk.Frame(self.music_pool_frame)
        self.audio_options_frame.pack(fill="x", pady=2)
        
        self.use_bgm_var = tk.BooleanVar(value=self.use_bgm)
        self.use_bgm_check = ttk.Checkbutton(
            self.audio_options_frame,
            text="使用随机背景音乐",
            variable=self.use_bgm_var,
            command=self._update_audio_options
        )
        self.use_bgm_check.pack(side="left", padx=5)
        
        # 背景音乐模式选择
        self.bgm_mode_frame = ttk.Frame(self.music_pool_frame)
        self.bgm_mode_frame.pack(fill="x", pady=2)
        
        self.bgm_mode_var = tk.StringVar(value="follow_video")
        
        self.follow_video_radio = ttk.Radiobutton(
            self.bgm_mode_frame,
            text="跟随视频模式",
            variable=self.bgm_mode_var,
            value="follow_video",
            state="disabled"
        )
        self.follow_video_radio.pack(side="left", padx=5)
        
        self.follow_music_radio = ttk.Radiobutton(
            self.bgm_mode_frame,
            text="跟随音乐模式",
            variable=self.bgm_mode_var,
            value="follow_music",
            state="disabled",
            command=self._update_bgm_mode
        )
        self.follow_music_radio.pack(side="left", padx=5)
        
        # 音乐池控制按钮和列表（初始隐藏）
        self.music_pool_controls = [
            self.music_pool_btn_frame,
            self.music_container,
            self.bgm_mode_frame
        ]
        for control in self.music_pool_controls:
            control.pack_forget()
        
        # 视频列表区域
        self.list_frame = ttk.LabelFrame(self.left_frame, text="视频列表", padding=5)
        
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
        self.process_frame = ttk.Frame(self.list_frame)
        self.start_btn = ttk.Button(
            self.process_frame, 
            text="开始混剪", 
            command=self._start_processing,
            style="Accent.TButton",  # 使用强调样式
            width=20  # 设置按钮宽度
        )
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(self.process_frame, textvariable=self.status_var)
        
        # 绑定事件
        self.tree.bind("<Double-1>", self._preview_video)
        self.tree.bind("<Button-1>", self._toggle_checkbox)
        
        # 初始化时根据配置显示或隐藏音乐池控件
        if self.use_bgm_var.get():
            for control in self.music_pool_controls:
                control.pack(fill="x", pady=2)
            # 启用模式选择
            self.follow_video_radio.configure(state="normal")
            self.follow_music_radio.configure(state="normal")
        else:
            for control in self.music_pool_controls:
                control.pack_forget()
            # 禁用模式选择
            self.follow_video_radio.configure(state="disabled")
            self.follow_music_radio.configure(state="disabled")
        
        # 刷新音乐池列表显示
        self._refresh_music_pools()
        
        # 修改输入文件夹Entry的绑定
        self.folder_entry.bind('<KeyRelease>', lambda e: self._update_input_folder())
        
        # 修改输出文件夹Entry的绑定
        self.output_entry.bind('<KeyRelease>', lambda e: self._update_output_folder())
    
    def _setup_layout(self):
        # 文件夹选择区域布局
        self.folder_frame.pack(fill="x", pady=5)
        self.input_frame.pack(fill="x", pady=2)
        self.output_frame.pack(fill="x", pady=2)
        
        # 参数设置区域布局
        self.params_frame.pack(fill="x", pady=5)
        
        # 视频列表区域布局
        self.list_frame.pack(fill="both", expand=True, pady=5)
        self.tree.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # 全选/取消全选按钮区域布局
        self.button_frame.pack(fill="x", pady=5)
        self.select_all_btn.pack(side="left", padx=5)
        self.deselect_all_btn.pack(side="left", padx=5)
        
        # 开始混剪按钮和状态布局
        self.process_frame.pack(fill="x", pady=10)
        self.start_btn.pack(side="left", padx=5, pady=5, expand=True)
        self.status_label.pack(side="right", padx=5)
    
    def _browse_input_folder(self):
        folder = filedialog.askdirectory(initialdir=self.selected_folder)
        if folder:
            self.selected_folder = folder
            self.folder_path.set(folder)
            self._load_videos()
            self._auto_save_config()
    
    def _open_input_folder(self):
        """打开输入文件夹"""
        if not self.selected_folder:
            messagebox.showerror("错误", "请先选择输入文件夹")
            return
        
        if not os.path.exists(self.selected_folder):
            messagebox.showerror("错误", "输入文件夹不存在")
            return
            
        os.startfile(self.selected_folder)
    
    def _browse_output_folder(self):
        folder = filedialog.askdirectory(initialdir=self.output_folder)
        if folder:
            self.output_folder = folder
            self.output_path.set(folder)
            self._auto_save_config()
    
    def _open_output_folder(self):
        """打开输出文件夹"""
        if not self.output_folder:
            messagebox.showerror("错误", "请先选择输出文件夹")
            return
        
        if not os.path.exists(self.output_folder):
            messagebox.showerror("错误", "输出文件夹不存在")
            return
            
        os.startfile(self.output_folder)
    
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
        if self.use_bgm_var.get():
            # 如果使用背景音乐，禁用其他音频选项
            self.voice_only_var.set(False)
            self.no_audio_var.set(False)
            self.voice_only_check.state(['disabled'])
            self.no_audio_check.state(['disabled'])
            # 显示音乐池控件
            for control in self.music_pool_controls:
                control.pack(fill="x", pady=2)
            # 启用模式选择
            self.follow_video_radio.configure(state="normal")
            self.follow_music_radio.configure(state="normal")
        else:
            # 恢复其他音频选项
            self.voice_only_check.state(['!disabled'])
            self.no_audio_check.state(['!disabled'])
            # 隐藏音乐池控件
            for control in self.music_pool_controls:
                control.pack_forget()
            # 禁用模式选择
            self.follow_video_radio.configure(state="disabled")
            self.follow_music_radio.configure(state="disabled")
    
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

    def _get_unique_filename(self, base_name: str, index: int) -> str:
        """生成不冲突的文件名"""
        # 基础文件名格式
        filename = f"{base_name}-{index}.mp4"
        # 如果文件已存在，增加序号直到找到不存在的文件名
        counter = 1
        while os.path.exists(os.path.join(self.output_folder, filename)):
            filename = f"{base_name}-{index}-{counter}.mp4"
            counter += 1
        return filename

    def _process_videos(self, videos: List[str], duration: float, clips: int, temp_dir: str, generate_count: int):
        try:
            base_name = self.output_name_var.get()
            voice_only = self.voice_only_var.get()
            no_audio = self.no_audio_var.get()
            use_bgm = self.use_bgm_var.get()
            sound_effect_type = self.sound_effect_type_var.get()
            sound_effect_path = self.sound_effect_path if sound_effect_type != "none" else None
            
            for video_index in range(generate_count):
                # 随机选择视频
                selected_clips = random.sample(videos, clips)
                temp_files = []
                
                # 如果使用背景音乐，随机选择一个
                background_music = None
                if use_bgm:
                    background_music = self._get_random_background_music()
                    if not background_music:
                        messagebox.showerror("错误", "没有可用的背景音乐，请检查音乐池设置")
                        return
                
                # 处理每个视频片段
                for i, video in enumerate(selected_clips, 1):
                    self.status_var.set(f"处理第 {video_index + 1}/{generate_count} 个视频的片段 {i}/{clips}")
                    input_path = os.path.join(self.selected_folder, video)
                    temp_path = os.path.join(temp_dir, f"temp_{video_index}_{i}.mp4")
                    processed_path = os.path.join(temp_dir, f"processed_{video_index}_{i}.mp4")
                    output_path = os.path.join(temp_dir, f"clip_{video_index}_{i}.mp4")
                    temp_files.append(output_path)
                    
                    # 首先裁剪视频片段
                    if no_audio or use_bgm:  # 如果使用背景音乐，也需要去除原音频
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
                    
                    if not no_audio and not use_bgm and voice_only:
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
                
                # 如果需要添加背景音乐
                output_file = os.path.join(self.output_folder, self._get_unique_filename(base_name, video_index + 1))
                if use_bgm and background_music:
                    if self.bgm_mode_var.get() == "follow_video":
                        # 跟随视频模式：音乐循环或裁剪到视频长度
                        cmd = [
                            "ffmpeg", "-y",
                            "-i", merged_path,
                            "-i", background_music,
                            "-filter_complex",
                            "[1:a]aloop=loop=-1:size=2e+09[loop];[loop]aresample=44100[a];[a]volume=0.5[bgm];[bgm]atrim=duration=" + str(duration * clips) + "[final]",
                            "-map", "0:v",
                            "-map", "[final]",
                            "-c:v", "copy",
                            "-c:a", "aac",
                            "-b:a", "192k",
                            output_file
                        ]
                    else:
                        # 跟随音乐模式：视频长度适应音乐长度
                        cmd = [
                            "ffmpeg", "-y",
                            "-i", merged_path,
                            "-i", background_music,
                            "-filter_complex",
                            "[0:v]setpts=PTS*{video_speed}[v];[1:a]volume=0.5[a]".format(
                                video_speed=duration * clips / float(subprocess.check_output([
                                    "ffprobe",
                                    "-v", "error",
                                    "-show_entries", "format=duration",
                                    "-of", "default=noprint_wrappers=1:nokey=1",
                                    background_music
                                ]).decode().strip())
                            ),
                            "-map", "[v]",
                            "-map", "[a]",
                            "-c:v", "libx264",
                            "-preset", "medium",
                            "-crf", "18",
                            "-c:a", "aac",
                            "-b:a", "192k",
                            output_file
                        ]
                    subprocess.run(cmd, check=True)
                    os.remove(merged_path)
                elif sound_effect_type == "video" and sound_effect_path:
                    # 如果需要在完整视频开头添加音效
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

    def _add_music_pool(self):
        """添加新的音乐池"""
        folder = filedialog.askdirectory(title="选择音乐池文件夹")
        if not folder:
            return
        
        # 获取默认音乐池名称
        default_name = os.path.basename(folder)
        
        # 检查路径是否已存在
        if folder in self.music_pools.values():
            messagebox.showerror("错误", "该音乐池文件夹已存在")
            return
        
        # 显示名称输入对话框
        dialog = MusicPoolNameDialog(self.root, default_name)
        if not dialog.result:
            return
        
        name = dialog.result
        
        # 如果名称已存在，使用带序号的名称
        base_name = name
        counter = 1
        while name in self.music_pools:
            name = f"{base_name}_{counter}"
            counter += 1
            # 再次询问用户
            dialog = MusicPoolNameDialog(self.root, name)
            if not dialog.result:
                return
            name = dialog.result
        
        # 添加到音乐池列表
        self.music_pools[name] = folder
        self._load_music_files(folder)
        
        # 更新显示
        self._refresh_music_pools()
        self._save_config()
    
    def _remove_music_pool(self):
        """删除选中的音乐池"""
        selection = self.pool_listbox.curselection()
        if not selection:
            messagebox.showerror("错误", "请先选择要删除的音乐池")
            return
        
        # 获取所有选中的音乐池名称
        pool_names = [self.pool_listbox.get(idx) for idx in selection]
        
        # 确认删除
        if len(pool_names) > 1:
            confirm = messagebox.askyesno(
                "确认删除",
                f"确定要删除选中的 {len(pool_names)} 个音乐池吗？\n{', '.join(pool_names)}"
            )
        else:
            confirm = messagebox.askyesno(
                "确认删除",
                f"确定要删除音乐池：{pool_names[0]}？"
            )
        
        if not confirm:
            return
        
        # 删除选中的音乐池
        for pool_name in pool_names:
            if pool_name in self.music_pools:
                pool_path = self.music_pools[pool_name]
                # 从音乐池字典中删除
                del self.music_pools[pool_name]
                # 从音乐文件字典中删除
                if pool_path in self.music_files:
                    del self.music_files[pool_path]
                
                # 如果删除的是当前选中的音乐池，清除选中状态
                if self.selected_pool == pool_name:
                    self.selected_pool = None
        
        # 清空音乐列表显示
        for item in self.music_tree.get_children():
            self.music_tree.delete(item)
        
        # 更新显示
        self._refresh_music_pools()
        # 立即保存配置
        self._save_config()
        
        # 显示成功消息
        if len(pool_names) > 1:
            messagebox.showinfo("成功", f"已删除 {len(pool_names)} 个音乐池")
        else:
            messagebox.showinfo("成功", f"已从列表中移除音乐池：{pool_names[0]}")

    def _open_music_pool(self):
        """打开选中的音乐池文件夹"""
        selected = self.music_pool_tree.selection()
        if not selected:
            messagebox.showerror("错误", "请先选择要打开的音乐池")
            return
        
        item = selected[0]
        values = self.music_pool_tree.item(item)["values"]
        path = values[2]  # 音乐池路径在第三列
        
        if not os.path.exists(path):
            messagebox.showerror("错误", "音乐池文件夹不存在")
            return
            
        os.startfile(path)
    
    def _toggle_music(self, event):
        """切换音乐的选中状态"""
        region = self.music_tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.music_tree.identify_row(event.y)
            if item:
                values = self.music_tree.item(item)["values"]
                if values:
                    new_value = "✓" if values[0] != "✓" else " "
                    self.music_tree.set(item, "checked", new_value)
    
    def _refresh_music_pools(self):
        """刷新音乐池列表显示"""
        # 清空现有列表
        self.pool_listbox.delete(0, tk.END)
        
        # 添加音乐池名称
        for name in self.music_pools.keys():
            self.pool_listbox.insert(tk.END, name)

    def _on_pool_select(self, event):
        """处理音乐池选择事件"""
        selection = self.pool_listbox.curselection()
        if not selection:
            return
        
        # 只显示最后选中的音乐池的内容
        last_selected = selection[-1]
        pool_name = self.pool_listbox.get(last_selected)
        pool_path = self.music_pools.get(pool_name)
        
        if not pool_path:
            return
        
        # 如果音乐池路径不存在，重新加载
        if pool_path not in self.music_files:
            self._load_music_files(pool_path)
        
        # 清空音乐列表
        for item in self.music_tree.get_children():
            self.music_tree.delete(item)
        
        # 加载音乐文件到列表
        if pool_path in self.music_files:
            for file in self.music_files[pool_path]:
                file_path = os.path.join(pool_path, file)
                try:
                    duration = self._get_music_duration(file_path)
                    duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "未知"
                except:
                    duration_str = "未知"
                self.music_tree.insert("", "end", values=("✓", file, duration_str))
        
        # 保存当前选中的音乐池
        self.selected_pool = pool_name

    def _update_bgm_mode(self):
        """更新背景音乐模式"""
        if self.bgm_mode_var.get() == "follow_music":
            # 获取选中的音乐池中的音乐
            selected_pools = []
            for item in self.music_tree.get_children():
                values = self.music_tree.item(item)["values"]
                if values[0] == "✓":
                    pool_path = values[1]
                    if pool_path in self.music_files:
                        selected_pools.append(pool_path)
            
            if not selected_pools:
                messagebox.showerror("错误", "请先选择音乐池")
                self.bgm_mode_var.set("follow_video")
                return
            
            # 随机选择一个音乐文件
            pool_path = random.choice(selected_pools)
            music_files = self.music_files[pool_path]
            if not music_files:
                messagebox.showerror("错误", "选中的音乐池中没有音乐文件")
                self.bgm_mode_var.set("follow_video")
                return
            
            music_file = random.choice(music_files)
            music_path = os.path.join(pool_path, music_file)
            
            try:
                # 使用ffprobe获取音乐时长
                cmd = [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    music_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                duration = float(result.stdout.strip())
                
                # 设置建议的片段参数
                suggested_duration = 5  # 默认5秒
                suggested_clips = math.ceil(duration / suggested_duration)
                
                # 更新界面显示
                if self.mode_var.get() == "auto":
                    self.target_duration_var.set(str(duration))
                    self._auto_calculate()
                else:
                    self.duration_var.set(str(suggested_duration))
                    self.clips_var.set(str(suggested_clips))
                    self._calculate_total()
                
            except Exception as e:
                messagebox.showerror("错误", f"获取音乐时长失败: {str(e)}")
                self.bgm_mode_var.set("follow_video")

    def _show_music_list(self, event):
        """显示音乐池中的音乐列表"""
        item = self.music_pool_tree.identify_row(event.y)
        if not item:
            return
            
        values = self.music_pool_tree.item(item)["values"]
        if not values:
            return
            
        pool_name = values[1]
        pool_path = values[2]
        
        if pool_path not in self.music_files:
            messagebox.showerror("错误", "该音乐池中没有音乐文件")
            return
        
        # 创建音乐列表窗口
        MusicListWindow(
            self.root,
            pool_name,
            pool_path,
            self.music_files[pool_path]
        )

    def _start_auto_update(self):
        """启动定时更新"""
        def update():
            if not self.processing:  # 如果不在处理视频
                self._check_folders()  # 检查文件夹状态
                self._auto_save_config()  # 自动保存配置
                self._refresh_music_pools()  # 刷新音乐池
            self.root.after(3000, update)  # 每3秒更新一次
        
        update()  # 开始第一次更新

    def _check_folders(self):
        """检查文件夹状态并更新显示"""
        # 检查输入文件夹
        if self.selected_folder:
            if not os.path.exists(self.selected_folder):
                self.folder_path.set("文件夹不存在: " + self.selected_folder)
            elif self.folder_path.get() != self.selected_folder:
                self.folder_path.set(self.selected_folder)
                self._load_videos()
        
        # 检查输出文件夹
        if self.output_folder:
            if not os.path.exists(self.output_folder):
                self.output_path.set("文件夹不存在: " + self.output_folder)
            elif self.output_path.get() != self.output_folder:
                self.output_path.set(self.output_folder)

    def _auto_save_config(self):
        """自动保存配置（限制保存频率）"""
        current_time = time.time()
        if current_time - self.last_save_time >= 3:  # 至少间隔3秒
            self._save_config()
            self.last_save_time = current_time

    def _update_input_folder(self):
        """实时更新输入文件夹路径"""
        new_path = self.folder_path.get().strip()
        if new_path and os.path.exists(new_path) and new_path != self.selected_folder:
            self.selected_folder = new_path
            self._load_videos()
            self._auto_save_config()

    def _update_output_folder(self):
        """实时更新输出文件夹路径"""
        new_path = self.output_path.get().strip()
        if new_path and os.path.exists(new_path) and new_path != self.output_folder:
            self.output_folder = new_path
            self._auto_save_config()

    def _get_random_background_music(self):
        """获取随机背景音乐"""
        # 获取选中的音乐池
        selection = self.pool_listbox.curselection()
        if not selection:
            return None
        
        pool_name = self.pool_listbox.get(selection[0])
        pool_path = self.music_pools.get(pool_name)
        if not pool_path or pool_path not in self.music_files:
            return None
        
        # 获取选中的音乐
        selected_music = []
        for item in self.music_tree.get_children():
            values = self.music_tree.item(item)["values"]
            if values[0] == "✓":
                selected_music.append(values[1])
        
        if not selected_music:
            return None
        
        # 随机选择一个音乐文件
        music_file = random.choice(selected_music)
        return os.path.join(pool_path, music_file)

class MusicPoolNameDialog:
    def __init__(self, parent, default_name):
        self.result = None
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("音乐池名称")
        self.dialog.geometry("300x120")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # 创建输入框
        ttk.Label(self.dialog, text="请输入音乐池名称:").pack(pady=10)
        self.name_var = tk.StringVar(value=default_name)
        self.name_entry = ttk.Entry(self.dialog, textvariable=self.name_var, width=30)
        self.name_entry.pack(pady=5)
        
        # 按钮区域
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="确定", command=self._on_ok).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="取消", command=self._on_cancel).pack(side="left", padx=10)
        
        # 绑定回车键
        self.name_entry.bind("<Return>", lambda e: self._on_ok())
        self.name_entry.focus_set()
        
        # 等待对话框关闭
        parent.wait_window(self.dialog)
    
    def _on_ok(self):
        name = self.name_var.get().strip()
        if name:
            self.result = name
            self.dialog.destroy()
    
    def _on_cancel(self):
        self.dialog.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoMixerApp(root)
    root.mainloop() 