#!/usr/bin/env python3
# resistor_parallel_pro.py
# 专业级电阻网络计算器 - 深度支持并联网络、功率分配、精度优化
# 依赖：仅需标准库 tkinter + math

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog, filedialog
import math
import json
from datetime import datetime
from typing import List, Tuple, Dict

class ResistorNetworkCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("奔跑羚羊-电阻网络专家 v3.1 (Running Antelope Resistor Expert)")
        self.root.geometry("1100x850")
        self.root.resizable(True, True)
        
        # 加载 Logo
        self.logo_img = None
        try:
            logo_path = r"c:\Users\xf016\Desktop\快捷测量工具\计算分压电阻\logo.png"
            self.logo_img = tk.PhotoImage(file=logo_path)
        except Exception as e:
            print(f"Logo load failed: {e}")
        
        # 标准电阻库 (kΩ)
        self.e24_values = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
                          3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
        self.e96_values = [1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.30,
                          1.33, 1.37, 1.40, 1.43, 1.47, 1.50, 1.54, 1.58, 1.62, 1.65, 1.69, 1.74,
                          1.78, 1.82, 1.87, 1.91, 1.96, 2.00, 2.05, 2.10, 2.15, 2.21, 2.26, 2.32,
                          2.37, 2.43, 2.49, 2.55, 2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09,
                          3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12,
                          4.22, 4.32, 4.42, 4.53, 4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49,
                          5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65, 6.81, 6.98, 7.15, 7.32,
                          7.50, 7.68, 7.87, 8.06, 8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76]
        
        # NTC 型号库
        self.ntc_models = {
            "MF52-103 (10k@25°C, B=3950)": {"r25": 10000, "b": 3950},
            "MF52-3435 (10k@25°C, B=3435)": {"r25": 10000, "b": 3435},
            "MF58-103 (贴片10k, B=3977)": {"r25": 10000, "b": 3977},
            "MF52-472 (4.7k@25°C)": {"r25": 4700, "b": 3950},
            "MF52-104 (100k@25°C)": {"r25": 100000, "b": 3950},
            "自定义 NTC": {"r25": 10000, "b": 3950}
        }
        
        # 应用场景模板
        self.templates = {
            "🔋 电池监测 (3.0-4.2V)": {
                "type": "battery", "vin_min": 3.0, "vin_max": 4.2, "vadc_safe": 3.25,
                "desc": "锂离子电池电压监测，保护ADC引脚"
            },
            "🔋 电池监测 (3.0-4.5V)": {
                "type": "battery", "vin_min": 3.0, "vin_max": 4.5, "vadc_safe": 3.25,
                "desc": "高压锂电/磷酸铁锂监测"
            },
            "⚡ 5V→3.3V 电平转换": {
                "type": "level_shift", "vin": 5.0, "vout": 3.3,
                "desc": "5V信号转3.3V逻辑电平"
            },
            "⚡ 12V→3.3V 电平转换": {
                "type": "level_shift", "vin": 12.0, "vout": 3.3,
                "desc": "12V信号转3.3V逻辑电平"
            },
            "🌡️ NTC 温度测量": {
                "type": "ntc", "vin": 3.3, "r_fixed": 10, "temp_range": "0~60°C",
                "desc": "NTC分压测温电路设计"
            },
            "⚖️ 并联功率分配": {
                "type": "parallel_power", "target_r": 10, "power_w": 0.5,
                "desc": "多电阻并联实现功率分配，避免单电阻过载"
            },
            "🎯 并联精度校准": {
                "type": "parallel_precision", "target_r": 52.3, "tolerance": 1,
                "desc": "并联组合实现非标准阻值，提升精度"
            }
        }
        
        # 电阻网络数据结构: 支持嵌套并联组
        # 格式: [(value_kohm, 'series'), ('parallel', [branch1, branch2, ...]), ...]
        self.r1_network: List = []
        self.r2_network: List = []
        self.use_ntc_r2 = False  # R2 是否使用 NTC
        
        self.create_widgets()
        self.create_circuit_canvas()
        self.load_template("🔋 电池监测 (3.0-4.2V)")
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # === 左侧控制面板 (25%) ===
        control_frame = ttk.Frame(main_frame, width=280)
        control_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W), padx=(0, 10))
        # control_frame.grid_propagate(False) # Removed to allow dynamic sizing
        
        # 应用场景模板
        tmpl_frame = ttk.LabelFrame(control_frame, text="📌 应用场景模板", padding="10")
        tmpl_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.template_var = tk.StringVar(value="🔋 电池监测 (3.0-4.2V)")
        tmpl_combo = ttk.Combobox(tmpl_frame, textvariable=self.template_var,
                                 values=list(self.templates.keys()), width=24, state="readonly")
        tmpl_combo.grid(row=0, column=0, pady=5)
        tmpl_combo.bind("<<ComboboxSelected>>", lambda e: self.load_template(self.template_var.get()))
        ttk.Button(tmpl_frame, text="✓", command=lambda: self.load_template(self.template_var.get()), 
                  width=3).grid(row=0, column=1, padx=(5,0))
        
        # 基本参数
        param_frame = ttk.LabelFrame(control_frame, text="⚙️ 基本参数", padding="10")
        param_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(param_frame, text="Vin (V):", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=3)
        self.vin_var = tk.StringVar(value="4.2")
        ttk.Entry(param_frame, textvariable=self.vin_var, width=12).grid(row=0, column=1, pady=3)
        
        ttk.Label(param_frame, text="Vout 目标 (V):", foreground="#27ae60").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.vout_var = tk.StringVar(value="3.25")
        ttk.Entry(param_frame, textvariable=self.vout_var, width=12).grid(row=1, column=1, pady=3)
        
        ttk.Label(param_frame, text="ADC 量程 (V):", foreground="#2980b9").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.adc_range_var = tk.StringVar(value="3.3")
        ttk.Entry(param_frame, textvariable=self.adc_range_var, width=12).grid(row=2, column=1, pady=3)
        
        # NTC 配置
        ntc_frame = ttk.LabelFrame(control_frame, text="🌡️ NTC 热敏电阻", padding="10")
        ntc_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(ntc_frame, text="型号:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.ntc_model_var = tk.StringVar(value="MF52-103 (10k@25°C, B=3950)")
        ntc_combo = ttk.Combobox(ntc_frame, textvariable=self.ntc_model_var,
                                values=list(self.ntc_models.keys()), width=20, state="readonly")
        ntc_combo.grid(row=0, column=1, columnspan=2, pady=2, sticky=(tk.W, tk.E))
        ntc_combo.bind("<<ComboboxSelected>>", self.update_ntc_params)
        
        ttk.Label(ntc_frame, text="R25 (Ω):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.ntc_r25_var = tk.StringVar(value="10000")
        ttk.Entry(ntc_frame, textvariable=self.ntc_r25_var, width=12).grid(row=1, column=1, pady=2)
        
        ttk.Label(ntc_frame, text="B 值 (K):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.ntc_b_var = tk.StringVar(value="3950")
        ttk.Entry(ntc_frame, textvariable=self.ntc_b_var, width=12).grid(row=2, column=1, pady=2)
        
        self.use_ntc_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(ntc_frame, text="R2 使用 NTC", variable=self.use_ntc_var,
                       command=self.toggle_ntc_mode).grid(row=3, column=0, columnspan=2, pady=5, sticky=tk.W)
        
        ttk.Button(ntc_frame, text="NTC 计算器", command=self.open_ntc_calculator, 
                  style="Accent.TButton").grid(row=4, column=0, columnspan=2, pady=8, sticky=(tk.W, tk.E))
        
        # 并联专用工具
        parallel_frame = ttk.LabelFrame(control_frame, text="🔀 并联专用工具", padding="10")
        parallel_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(parallel_frame, text="并联计算器", 
                  command=self.open_parallel_calculator).grid(row=0, column=0, pady=3, sticky=(tk.W, tk.E))
        ttk.Button(parallel_frame, text="功率分配分析", 
                  command=self.open_power_analyzer).grid(row=1, column=0, pady=3, sticky=(tk.W, tk.E))
        ttk.Button(parallel_frame, text="精度优化建议", 
                  command=self.open_precision_optimizer).grid(row=2, column=0, pady=3, sticky=(tk.W, tk.E))
        
        # === 左侧底部信息区 (Logo & Info) ===
        # 使用 main_frame 的 row=1 来放置，确保始终位于底部
        logo_info_frame = tk.Frame(main_frame, bg="#2c3e50")
        logo_info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.S), padx=(0,10), pady=(5,0))
        logo_info_frame.columnconfigure(1, weight=1) # Text column expands

        # Logo 图片
        if self.logo_img:
            tk.Label(logo_info_frame, image=self.logo_img, bg="#2c3e50").grid(row=0, column=0, rowspan=4, padx=10, pady=10)
        else:
            # Fallback text logo if image fails
            tk.Label(logo_info_frame, text="⚡\nLOGO", font=("Arial", 16, "bold"), 
                    bg="#2c3e50", fg="white").grid(row=0, column=0, rowspan=4, padx=10, pady=10)

        # 公司信息文本
        info_font = ("Arial", 8)
        tk.Label(logo_info_frame, text="奔跑羚羊科技出品", font=("微软雅黑", 10, "bold"), bg="#2c3e50", fg="white").grid(row=0, column=1, sticky=tk.W, pady=(5,0))
        tk.Label(logo_info_frame, text="Ver: 3.1 | License: MIT", font=info_font, bg="#2c3e50", fg="#ecf0f1").grid(row=1, column=1, sticky=tk.W)
        tk.Label(logo_info_frame, text="Email: contact@antelope.tech", font=info_font, bg="#2c3e50", fg="#bdc3c7").grid(row=2, column=1, sticky=tk.W)
        tk.Label(logo_info_frame, text="执行规定: Q/RA 001-2026", font=info_font, bg="#2c3e50", fg="#bdc3c7").grid(row=3, column=1, sticky=tk.W, pady=(0,5))

        # === 右侧主工作区 (75%) ===
        work_frame = ttk.Frame(main_frame)
        work_frame.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(1, weight=1)
        work_frame.columnconfigure(0, weight=1)
        work_frame.rowconfigure(3, weight=1) # Result text expands
        work_frame.rowconfigure(4, weight=1) # Canvas also expands
        
        # R1 网络配置
        r1_frame = ttk.LabelFrame(work_frame, text="R1 网络配置 (上拉电阻)", padding="10")
        r1_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        r1_frame.columnconfigure(1, weight=1)
        r1_frame.columnconfigure(2, weight=1)
        
        self.r1_value_var = tk.StringVar(value="15")
        ttk.Entry(r1_frame, textvariable=self.r1_value_var, width=10).grid(row=0, column=0, padx=(0,5))
        ttk.Button(r1_frame, text="添加串联", width=12, command=lambda: self.add_resistor('r1', 'series')).grid(row=0, column=1, padx=2, sticky=(tk.W, tk.E))
        ttk.Button(r1_frame, text="添加并联组", width=12, command=lambda: self.add_parallel_group('r1')).grid(row=0, column=2, padx=2, sticky=(tk.W, tk.E))
        ttk.Button(r1_frame, text="删除选中", width=10, command=lambda: self.delete_selected('r1')).grid(row=0, column=3, padx=2)
        ttk.Button(r1_frame, text="清空", width=8, command=lambda: self.clear_network('r1')).grid(row=0, column=4, padx=2)
        
        self.r1_listbox = tk.Listbox(r1_frame, height=4, width=50, font=("Courier", 9))
        self.r1_listbox.grid(row=1, column=0, columnspan=4, pady=5, sticky=(tk.W, tk.E))
        self.r1_listbox.bind('<Double-1>', lambda e: self.edit_resistor('r1'))
        
        # R2 网络配置
        r2_frame = ttk.LabelFrame(work_frame, text="R2 网络配置 (下拉电阻/NTC)", padding="10")
        r2_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        r2_frame.columnconfigure(1, weight=1)
        r2_frame.columnconfigure(2, weight=1)
        
        self.r2_value_var = tk.StringVar(value="51")
        ttk.Entry(r2_frame, textvariable=self.r2_value_var, width=10).grid(row=0, column=0, padx=(0,5))
        ttk.Button(r2_frame, text="添加串联", width=12, command=lambda: self.add_resistor('r2', 'series')).grid(row=0, column=1, padx=2, sticky=(tk.W, tk.E))
        ttk.Button(r2_frame, text="添加并联组", width=12, command=lambda: self.add_parallel_group('r2')).grid(row=0, column=2, padx=2, sticky=(tk.W, tk.E))
        ttk.Button(r2_frame, text="删除选中", width=10, command=lambda: self.delete_selected('r2')).grid(row=0, column=3, padx=2)
        ttk.Button(r2_frame, text="清空", width=8, command=lambda: self.clear_network('r2')).grid(row=0, column=4, padx=2)
        
        self.r2_listbox = tk.Listbox(r2_frame, height=4, width=50, font=("Courier", 9))
        self.r2_listbox.grid(row=1, column=0, columnspan=4, pady=5, sticky=(tk.W, tk.E))
        self.r2_listbox.bind('<Double-1>', lambda e: self.edit_resistor('r2'))
        
        # 操作按钮
        btn_frame = ttk.Frame(work_frame)
        btn_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=8)
        
        style = ttk.Style()
        style.configure("Accent.TButton", foreground="white", background="#3498db")
        if hasattr(style, 'map'):  # Tk 8.6+
            style.map("Accent.TButton", foreground=[('active', 'white')], background=[('active', '#2980b9')])
        
        ttk.Button(btn_frame, text="⚡ 计算缺失电阻", command=self.calculate_missing, 
                  style="Accent.TButton").grid(row=0, column=0, padx=4)
        ttk.Button(btn_frame, text="🎯 推荐标准值", command=self.recommend_standard).grid(row=0, column=1, padx=4)
        ttk.Button(btn_frame, text="📊 网络分析", command=self.calculate_network).grid(row=0, column=2, padx=4)
        ttk.Button(btn_frame, text="📋 导出 BOM", command=self.export_bom).grid(row=0, column=3, padx=4)
        ttk.Button(btn_frame, text="💾 保存配置", command=self.save_config).grid(row=0, column=4, padx=4)
        ttk.Button(btn_frame, text="📂 加载配置", command=self.load_config).grid(row=0, column=5, padx=4)
        
        # 结果显示区
        result_frame = ttk.LabelFrame(work_frame, text="📈 计算结果与工程分析", padding="10")
        result_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, height=10, width=90,
                                                    font=("Courier", 10), wrap=tk.WORD)
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 电路图区域
        self.canvas_frame = ttk.LabelFrame(work_frame, text="🎨 电路拓扑可视化", padding="10")
        self.canvas_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas_frame.rowconfigure(0, weight=1)
        
        # 状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10,0))
        
        self.status_var = tk.StringVar(value="✅ 就绪 | 支持串并联混合网络 | 双击电阻值可编辑")
        ttk.Label(status_frame, textvariable=self.status_var, 
                 font=("Arial", 9), foreground="#7f8c8d").grid(row=0, column=0, sticky=tk.W)
    
    def create_circuit_canvas(self):
        self.canvas = tk.Canvas(self.canvas_frame, bg="#f8f9fa", height=320)
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.canvas.bind("<Configure>", lambda e: self.draw_circuit())
    
    def draw_circuit(self):
        """绘制支持并联分支的电路拓扑图"""
        self.canvas.delete("all")
        
        # 获取当前画布宽度
        canvas_width = self.canvas.winfo_width()
        if canvas_width < 100: canvas_width = 1060 # 默认值
        
        # 参数
        x_start = max(60, int(canvas_width * 0.08))
        y_center = 160
        y_top_branch = 90
        y_bottom_branch = 230
        resistor_w = 45
        resistor_h = 16
        
        try:
            vin = float(self.vin_var.get())
            r1_eq = self.calculate_equivalent(self.r1_network)
            r2_eq = self.calculate_equivalent(self.r2_network)
            vout = vin * r2_eq / (r1_eq + r2_eq) if (r1_eq + r2_eq) > 0 else 0
            is_ntc = self.use_ntc_var.get() and len(self.r2_network) > 0
        except:
            vin, vout, r1_eq, r2_eq, is_ntc = 4.2, 3.25, 15, 51, False
        
        # 电源符号
        self.canvas.create_line(x_start, y_center, x_start+35, y_center, width=3, arrow=tk.LAST, fill="#e74c3c")
        self.canvas.create_text(x_start-20, y_center-30, text=f"{vin}V", 
                               font=("Arial", 14, "bold"), fill="#c0392b")
        self.canvas.create_text(x_start-20, y_center+20, text="Vin", font=("Arial", 10))
        
        # 绘制 R1 网络
        x_pos = x_start + 50
        x_pos = self._draw_resistor_network(self.canvas, self.r1_network, x_pos, y_center, y_top_branch, "#3498db", "R1")
        
        # Vout 采样点 (突出显示)
        x_vout = x_pos + 25
        self.canvas.create_line(x_vout, y_center, x_vout, y_center-55, width=3, dash=(5,3), fill="#27ae60")
        self.canvas.create_oval(x_vout-8, y_center-62, x_vout+8, y_center-46, fill="#e74c3c", outline="white", width=2)
        self.canvas.create_text(x_vout+35, y_center-78, text=f"Vout = {vout:.2f}V", 
                               font=("Arial", 12, "bold"), fill="#27ae60")
        self.canvas.create_text(x_vout+35, y_center-63, text="ADC_IN", 
                               font=("Arial", 9, "italic"), fill="#7f8c8d")
        
        # 绘制 R2 网络
        x_pos = x_vout + 50
        x_pos = self._draw_resistor_network(self.canvas, self.r2_network, x_pos, y_center, y_bottom_branch, 
                                           "#e67e22" if not is_ntc else "#8e44ad", "R2/NTC", is_ntc)
        
        # GND 符号
        x_gnd = x_pos + 35
        self.canvas.create_line(x_gnd, y_center, x_gnd+30, y_center, width=3, fill="#7f8c8d")
        self.canvas.create_line(x_gnd+30, y_center-15, x_gnd+30, y_center+15, width=3, fill="#7f8c8d")
        self.canvas.create_line(x_gnd+30, y_center+15, x_gnd+42, y_center+15, width=3, fill="#7f8c8d")
        self.canvas.create_text(x_gnd+60, y_center+30, text="GND", 
                               font=("Arial", 13, "bold"), fill="#7f8c8d")
        
        # 保护电容
        cap_x = x_vout - 10
        self.canvas.create_line(cap_x, y_center+40, cap_x+20, y_center+40, width=2, fill="#546e7a")
        self.canvas.create_line(cap_x, y_center+52, cap_x+20, y_center+52, width=2, fill="#546e7a")
        self.canvas.create_line(cap_x+10, y_center+40, cap_x+10, y_center+52, width=2, fill="#546e7a")
        self.canvas.create_text(cap_x+10, y_center+68, text="0.1μF", font=("Arial", 9), fill="#546e7a")
        
        # 标题与安全指示
        safety_color = "#27ae60" if vout <= 3.25 else "#f39c12" if vout <= 3.3 else "#e74c3c"
        safety_text = "✅ 安全" if vout <= 3.25 else "⚠️ 临界" if vout <= 3.3 else "❌ 过压"
        
        self.canvas.create_text(canvas_width / 2, 25, text="🔋 电阻分压网络拓扑图 (支持串并联混合)", 
                               font=("Arial", 15, "bold"), fill="#1a237e")
        self.canvas.create_text(canvas_width - 110, 25, text=safety_text, 
                               font=("Arial", 12, "bold"), fill=safety_color)
        
        # 网络等效值标注
        if r1_eq > 0:
            self.canvas.create_text(x_start+50 + (x_vout - x_start - 50)/2, y_center-120, 
                                   text=f"R1_eq = {r1_eq:.2f}kΩ", 
                                   font=("Arial", 10, "bold"), fill="#3498db")
        if r2_eq > 0:
            self.canvas.create_text(x_vout+50 + (x_gnd - x_vout - 50)/2, y_center+120, 
                                   text=f"R2_eq = {r2_eq:.2f}kΩ", 
                                   font=("Arial", 10, "bold"), fill="#e67e22")
    
    def _draw_resistor_network(self, canvas, network, x_start, y_main, y_branch, color, label, is_ntc=False):
        """递归绘制电阻网络（支持嵌套并联）"""
        x_pos = x_start
        resistor_w = 45
        resistor_h = 16
        
        for i, element in enumerate(network):
            if isinstance(element, tuple) and element[0] == 'parallel':
                # 绘制并联组
                branches = element[1]
                branch_spacing = 40
                
                # 绘制并联入口连线
                canvas.create_line(x_pos, y_main, x_pos+15, y_main, width=2.5, fill=color)
                
                # 绘制各分支
                for j, branch in enumerate(branches):
                    y_offset = y_branch + (j - len(branches)/2 + 0.5) * branch_spacing
                    
                    # 分支垂直连线
                    canvas.create_line(x_pos+15, y_main, x_pos+15, y_offset, width=1.5, dash=(3,2), fill=color)
                    
                    # 分支电阻（简化：只画一个代表电阻）
                    if branch:
                        r_val = branch[0][0] if isinstance(branch[0], tuple) else branch[0]
                        canvas.create_rectangle(x_pos+20, y_offset-resistor_h/2, 
                                              x_pos+20+resistor_w, y_offset+resistor_h/2,
                                              fill="#ecf0f1", outline=color, width=2)
                        canvas.create_text(x_pos+20+resistor_w/2, y_offset-25,
                                         text=f"{r_val}kΩ", font=("Arial", 7), fill=color)
                    
                    # 分支返回连线
                    canvas.create_line(x_pos+20+resistor_w+5, y_offset, x_pos+20+resistor_w+5, y_main, 
                                     width=1.5, dash=(3,2), fill=color)
                
                # 并联出口连线
                x_pos += 55
                
                # 并联标识 (根据分支方向调整标签位置，避免重叠)
                label_y_offset = -25 if y_branch > y_main else 25
                canvas.create_text(x_pos-20, y_main+label_y_offset, text=f"║║ {label}_{i+1}", 
                                 font=("Arial", 8, "bold"), fill=color)
            
            elif isinstance(element, tuple) and element[1] == 'series':
                # 绘制串联电阻
                r_val = element[0]
                canvas.create_rectangle(x_pos, y_main-resistor_h/2, 
                                      x_pos+resistor_w, y_main+resistor_h/2,
                                      fill="#ecf0f1", outline=color, width=2)
                
                tag = "NTC" if (is_ntc and i == 0) else f"{label}_{i+1}"
                canvas.create_text(x_pos+resistor_w/2, y_main-28,
                                 text=f"{tag}\n{r_val}kΩ", font=("Arial", 8), fill=color)
                x_pos += resistor_w + 20
        
        return x_pos
    
    def add_resistor(self, side, r_type):
        """添加单个电阻到网络"""
        try:
            value = float(self.r1_value_var.get() if side == 'r1' else self.r2_value_var.get())
            if value <= 0:
                raise ValueError("电阻值必须 > 0")
            
            target = self.r1_network if side == 'r1' else self.r2_network
            target.append((value, r_type))
            self.update_listbox(side)
            self.calculate_network()
            
        except ValueError as e:
            messagebox.showerror("输入错误", str(e))
    
    def add_parallel_group(self, side):
        """添加并联电阻组（弹出对话框配置）"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"添加 {side.upper()} 并联组")
        dialog.geometry("350x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="输入并联分支电阻值 (kΩ)，每行一个:", 
                 font=("Arial", 10, "bold")).pack(pady=10)
        
        text = scrolledtext.ScrolledText(dialog, height=8, width=40, font=("Courier", 10))
        text.pack(padx=10, pady=5)
        text.insert(1.0, "100\n100\n100")  # 默认示例
        
        result_var = tk.StringVar()
        
        def confirm():
            lines = text.get(1.0, tk.END).strip().split('\n')
            branches = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    r_val = float(line)
                    if r_val <= 0:
                        raise ValueError
                    branches.append([(r_val, 'series')])  # 每个分支目前只支持单电阻
                except:
                    messagebox.showerror("错误", f"无效电阻值: '{line}'")
                    return
            
            if not branches:
                messagebox.showerror("错误", "至少需要一个有效电阻值")
                return
            
            target = self.r1_network if side == 'r1' else self.r2_network
            target.append(('parallel', branches))
            self.update_listbox(side)
            self.calculate_network()
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="确定", command=confirm, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)
    
    def delete_selected(self, side):
        """删除选中的电阻或并联组"""
        listbox = self.r1_listbox if side == 'r1' else self.r2_listbox
        network = self.r1_network if side == 'r1' else self.r2_network
        
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要删除的项目")
            return
            
        idx = selection[0]
        if 0 <= idx < len(network):
            network.pop(idx)
            self.update_listbox(side)
            self.calculate_network()

    def edit_resistor(self, side):
        """双击编辑电阻值"""
        listbox = self.r1_listbox if side == 'r1' else self.r2_listbox
        selection = listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        network = self.r1_network if side == 'r1' else self.r2_network
        
        if idx >= len(network):
            return
        
        element = network[idx]
        
        if isinstance(element, tuple) and element[0] == 'parallel':
            # 编辑并联组（简化：重新配置）
            self.add_parallel_group(side)
            return
        
        # 编辑单个电阻
        current_val = element[0]
        new_val = simpledialog.askfloat("编辑电阻值", f"输入新的电阻值 (kΩ):", 
                                       initialvalue=current_val, parent=self.root)
        if new_val is not None and new_val > 0:
            network[idx] = (new_val, element[1])
            self.update_listbox(side)
            self.calculate_network()
    
    def update_listbox(self, side):
        """更新列表框显示（支持并联组可视化）"""
        listbox = self.r1_listbox if side == 'r1' else self.r2_listbox
        network = self.r1_network if side == 'r1' else self.r2_network
        
        listbox.delete(0, tk.END)
        
        for i, element in enumerate(network):
            if isinstance(element, tuple) and element[0] == 'parallel':
                # 并联组
                branches = element[1]
                branch_vals = []
                for branch in branches:
                    if branch:
                        branch_vals.append(str(branch[0][0]))
                listbox.insert(tk.END, f"[{i+1}] ║║ 并联组: {' // '.join(branch_vals)} kΩ")
                listbox.itemconfig(i, {'bg': '#e3f2fd'})
            else:
                # 串联电阻
                symbol = "──" if element[1] == 'series' else "║║"
                listbox.insert(tk.END, f"[{i+1}] {symbol} {element[0]} kΩ")
                if element[1] == 'series':
                    listbox.itemconfig(i, {'bg': '#fff3e0'})
    
    def clear_network(self, side):
        """清空网络"""
        if side == 'r1':
            self.r1_network = []
            self.r1_listbox.delete(0, tk.END)
        else:
            self.r2_network = []
            self.r2_listbox.delete(0, tk.END)
        self.calculate_network()
    
    def calculate_equivalent(self, network) -> float:
        """精确计算串并联混合网络的等效阻值"""
        if not network:
            return 0.001  # 避免除零
        
        total = 0.0
        i = 0
        
        while i < len(network):
            element = network[i]
            
            if isinstance(element, tuple) and element[0] == 'parallel':
                # 处理并联组
                branches = element[1]
                conductance_sum = 0.0
                
                for branch in branches:
                    # 简化：每个分支只取第一个电阻（实际可递归计算分支等效）
                    if branch:
                        r_val = branch[0][0] if isinstance(branch[0], tuple) else branch[0]
                        conductance_sum += 1.0 / r_val
                
                if conductance_sum > 0:
                    r_parallel = 1.0 / conductance_sum
                    total += r_parallel
                i += 1
            
            elif isinstance(element, tuple) and element[1] == 'series':
                # 串联电阻
                total += element[0]
                i += 1
            
            else:
                # 兼容旧格式
                total += element[0] if isinstance(element, tuple) else element
                i += 1
        
        return total if total > 0 else 0.001
    
    def calculate_network(self):
        """全面网络分析：等效值、功耗、精度、安全边界"""
        try:
            vin = float(self.vin_var.get())
            vadc_max = float(self.adc_range_var.get())
            r1_eq = self.calculate_equivalent(self.r1_network)
            r2_eq = self.calculate_equivalent(self.r2_network)
            
            if r1_eq < 0.01 or r2_eq < 0.01:
                raise ValueError("R1 和 R2 均需 > 0")
            
            vout = vin * r2_eq / (r1_eq + r2_eq)
            current_ma = vin / (r1_eq + r2_eq)  # mA (因电阻为 kΩ)
            power_r1_mw = (vin * r2_eq / (r1_eq + r2_eq))**2 / r1_eq  # mW
            power_r2_mw = vout**2 / r2_eq  # mW
            
            # 安全检查
            if vout > 3.25:
                safety = "❌ 过压危险!" if vout >= vadc_max else "⚠️ 接近极限 (建议 ≤3.25V)"
                safety_color = "#e74c3c" if vout >= vadc_max else "#f39c12"
            else:
                safety = f"✅ 安全 (裕量 {3.25 - vout:.2f}V)"
                safety_color = "#27ae60"
            
            # ADC 分辨率分析
            adc_bits = 12
            adc_lsb_mv = vadc_max * 1000 / (2**adc_bits)
            batt_lsb_mv = adc_lsb_mv * (r1_eq + r2_eq) / r2_eq
            
            # 并联网络分析
            parallel_analysis = self.analyze_parallel_network()
            
            # 生成报告
            report = f"【📊 电路参数概览】\n"
            report += f"  Vin: {vin:.2f}V  →  Vout: {vout:.3f}V  ({safety})\n"
            report += f"  R1_eq: {r1_eq:.2f}kΩ  |  R2_eq: {r2_eq:.2f}kΩ  |  分压比: {r2_eq/(r1_eq+r2_eq):.4f}\n"
            report += f"\n【⚡ 功耗分析】\n"
            report += f"  总电流: {current_ma:.3f} mA  |  总功耗: {(power_r1_mw + power_r2_mw):.3f} mW\n"
            report += f"  R1 功耗: {power_r1_mw:.3f} mW  |  R2 功耗: {power_r2_mw:.3f} mW\n"
            
            if power_r1_mw > 0.125 or power_r2_mw > 0.125:
                report += f"  ⚠️  提示: 单电阻功耗 > 1/8W，建议使用 1/4W 电阻或并联分担!\n"
            
            report += f"\n【📐 ADC 分辨率】(假设 {adc_bits}-bit ADC, 量程 {vadc_max}V)\n"
            report += f"  ADC LSB: {adc_lsb_mv:.2f} mV  →  电池电压分辨率: {batt_lsb_mv:.2f} mV/LSB\n"
            
            if parallel_analysis:
                report += f"\n{parallel_analysis}"
            
            # NTC 特殊分析
            if self.use_ntc_var.get():
                report += f"\n【🌡️ NTC 特性】\n"
                report += f"  型号: {self.ntc_model_var.get()}\n"
                report += f"  25°C 电阻: {float(self.ntc_r25_var.get())/1000:.1f}kΩ  |  B 值: {self.ntc_b_var.get()}K\n"
                report += f"  ⚠️  注意: NTC 阻值随温度变化，Vout 非线性，请使用查表法或 Steinhart-Hart 公式校准!\n"
            
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, report)
            self.status_var.set(f"✅ 计算完成 | Vout={vout:.3f}V | R1_eq={r1_eq:.2f}kΩ | R2_eq={r2_eq:.2f}kΩ")
            
            # 更新电路图
            self.draw_circuit()
            
        except Exception as e:
            error_msg = f"计算错误: {str(e)}"
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, error_msg)
            self.status_var.set(f"❌ {error_msg}")
            messagebox.showerror("计算错误", str(e))
    
    def analyze_parallel_network(self) -> str:
        """分析并联网络的功率分配与精度增益"""
        analysis = ""
        has_parallel = False
        
        for side, network, name in [('r1', self.r1_network, 'R1'), ('r2', self.r2_network, 'R2')]:
            for element in network:
                if isinstance(element, tuple) and element[0] == 'parallel':
                    has_parallel = True
                    branches = element[1]
                    r_vals = [branch[0][0] for branch in branches if branch]
                    r_eq = 1.0 / sum(1.0/r for r in r_vals) if r_vals else 0
                    
                    analysis += f"\n【{name} 并联组分析】等效 {r_eq:.2f}kΩ\n"
                    analysis += f"  电阻组成: {' // '.join(f'{r}kΩ' for r in r_vals)}\n"
                    
                    # 功率分配（假设总功耗 0.25W）
                    total_power_mw = 250  # 假设总功耗 250mW 用于演示
                    for r in r_vals:
                        i_branch = math.sqrt(total_power_mw / 1000 / r_eq) * (r_eq / r)  # 分支电流比例
                        p_branch = (i_branch**2) * r
                        analysis += f"    • {r}kΩ: 功耗 {p_branch:.1f}mW ({p_branch/total_power_mw*100:.1f}%)\n"
                    
                    # 精度分析
                    analysis += f"  精度增益: 并联可降低温漂影响，等效温度系数 ≈ 单电阻的 1/√N\n"
        
        return analysis if has_parallel else ""
    
    def calculate_missing(self):
        """智能计算缺失电阻（支持网络约束）"""
        try:
            vin = float(self.vin_var.get())
            vout_target = float(self.vout_var.get())
            vadc_max = float(self.adc_range_var.get())
            
            if vout_target >= vin:
                raise ValueError("Vout 必须 < Vin")
            if vout_target > vadc_max:
                raise ValueError(f"Vout 目标超过 ADC 量程 ({vadc_max}V)")
            
            r1_eq = self.calculate_equivalent(self.r1_network)
            r2_eq = self.calculate_equivalent(self.r2_network)
            
            # 智能补全策略
            if r1_eq < 0.01 and r2_eq < 0.01:
                # 两者都空：推荐标准配置
                ratio = vout_target / vin
                r2_r1 = ratio / (1 - ratio)
                r1_rec = 15.0 if vin <= 4.5 else 10.0
                r2_rec = r1_rec * r2_r1
                
                self.r1_network = [(r1_rec, 'series')]
                self.r2_network = [(r2_rec, 'series')]
                self.update_listbox('r1')
                self.update_listbox('r2')
                self.calculate_network()
                return
            
            if r1_eq < 0.01:
                # R1 未知
                r1_calc = r2_eq * (vin - vout_target) / vout_target
                if r1_calc <= 0:
                    raise ValueError("计算出的 R1 ≤ 0，检查参数")
                self.r1_network = [(r1_calc, 'series')]
                self.update_listbox('r1')
            
            elif r2_eq < 0.01:
                # R2 未知
                r2_calc = r1_eq * vout_target / (vin - vout_target)
                if r2_calc <= 0:
                    raise ValueError("计算出的 R2 ≤ 0，检查参数")
                self.r2_network = [(r2_calc, 'series')]
                self.update_listbox('r2')
            
            self.calculate_network()
            
            # 标准值建议
            if r1_eq < 0.01 or r2_eq < 0.01:
                missing = "R1" if r1_eq < 0.01 else "R2"
                calc_val = r1_calc if r1_eq < 0.01 else r2_calc
                std_val = self.find_nearest_e24(calc_val * 1000) / 1000
                self.result_text.insert(tk.END, 
                    f"\n💡 {missing} 建议: 理论值 {calc_val:.3f}kΩ → 标准值 {std_val:.2f}kΩ (E24)\n")
        
        except Exception as e:
            messagebox.showerror("计算错误", str(e))
    
    def recommend_standard(self):
        """智能推荐标准电阻组合（含并联方案）"""
        try:
            vin = float(self.vin_var.get())
            vout = float(self.vout_var.get())
            ratio = vout / vin
            r2_r1 = ratio / (1 - ratio)
            
            report = f"🎯 标准电阻推荐 (Vin={vin}V → Vout={vout}V)\n"
            report += f"   理论分压比: {ratio:.4f}  |  R2/R1 = {r2_r1:.4f}\n"
            report += "="*72 + "\n\n"
            
            # 方案1: 单电阻 E24
            r1_base = 15.0
            r2_calc = r1_base * r2_r1
            r2_e24 = self.find_nearest_e24(r2_calc * 1000) / 1000
            vout_e24 = vin * r2_e24 / (r1_base + r2_e24)
            err_e24 = (vout_e24 - vout) / vout * 100
            
            report += f"【方案1】单电阻 (E24 标准值) - 简单可靠\n"
            report += f"  R1 = {r1_base}kΩ + R2 = {r2_e24:.2f}kΩ\n"
            report += f"  → Vout = {vout_e24:.3f}V (误差 {err_e24:+.2f}%)  电流 {vin/(r1_base+r2_e24):.3f}mA\n\n"
            
            # 方案2: 串联组合（提高精度）
            r2_s1 = self.find_nearest_e24(r2_calc * 1000 * 0.7) / 1000
            r2_s2 = self.find_nearest_e24((r2_calc - r2_s1) * 1000) / 1000
            r2_series = r2_s1 + r2_s2
            vout_s = vin * r2_series / (r1_base + r2_series)
            err_s = (vout_s - vout) / vout * 100
            
            report += f"【方案2】R2 串联组合 - 精度提升\n"
            report += f"  R1 = {r1_base}kΩ + R2 = {r2_s1:.2f}kΩ ── {r2_s2:.2f}kΩ\n"
            report += f"  → 等效 {r2_series:.2f}kΩ → Vout = {vout_s:.3f}V (误差 {err_s:+.2f}%)\n\n"
            
            # 方案3: 并联组合（实现低阻值/功率分配）
            # 寻找两个标准值并联接近目标
            best_err = float('inf')
            best_pair = None
            for r_a in [r * 10 for r in self.e24_values]:  # 10k~100k 范围
                for r_b in [r * 10 for r in self.e24_values]:
                    r_eq = 1 / (1/r_a + 1/r_b)
                    err = abs(r_eq - r2_calc)
                    if err < best_err and r_eq > 0:
                        best_err = err
                        best_pair = (r_a, r_b, r_eq)
            
            if best_pair:
                r_a, r_b, r_eq = best_pair
                vout_p = vin * r_eq / (r1_base + r_eq)
                err_p = (vout_p - vout) / vout * 100
                report += f"【方案3】R2 并联组合 - 功率分配/非标阻值\n"
                report += f"  R1 = {r1_base}kΩ + R2 = {r_a:.0f}kΩ ║ {r_b:.0f}kΩ\n"
                report += f"  → 等效 {r_eq:.2f}kΩ → Vout = {vout_p:.3f}V (误差 {err_p:+.2f}%)\n"
                report += f"  💡 优势: 功耗均分，单电阻功耗降至 50%，提升可靠性!\n\n"
            
            # 电池监测安全配置
            if vin >= 4.0:
                safe_vout = 3.25
                safe_ratio = safe_vout / vin
                safe_r2_r1 = safe_ratio / (1 - safe_ratio)
                r1_safe = 18.0 if vin >= 4.5 else 15.0
                r2_safe = r1_safe * safe_r2_r1
                r2_safe_std = self.find_nearest_e24(r2_safe * 1000) / 1000
                vout_safe = vin * r2_safe_std / (r1_safe + r2_safe_std)
                
                report += f"⚠️  🔋 电池监测安全配置 (Vin={vin}V → Vout≤3.25V):\n"
                report += f"   R1 = {r1_safe}kΩ + R2 = {r2_safe_std:.2f}kΩ → Vout = {vout_safe:.3f}V ✅\n"
                report += f"   安全裕量: {3.25 - vout_safe:.2f}V (可承受电池瞬时过冲至 {vin + 0.1:.2f}V)\n"
            
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, report)
            self.status_var.set(f"✅ 推荐完成 | 最佳方案误差 {min(abs(err_e24), abs(err_s), abs(err_p) if best_pair else 999):.2f}%")
        
        except Exception as e:
            messagebox.showerror("推荐错误", str(e))
    
    def find_nearest_e24(self, value_ohm: float) -> float:
        """在 E24 系列中查找最接近的值（单位：Ω）"""
        best_diff = float('inf')
        best_val = None
        
        for base in self.e24_values:
            for exp in range(-1, 6):  # 0.1Ω 到 1MΩ
                candidate = base * (10 ** exp)
                diff = abs(candidate - value_ohm)
                if diff < best_diff:
                    best_diff = diff
                    best_val = candidate
        return best_val
    
    def open_parallel_calculator(self):
        """专用并联计算器：输入目标阻值，推荐并联组合"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🔀 并联电阻计算器")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="目标等效阻值 (kΩ):", font=("Arial", 10, "bold")).pack(pady=(15,5))
        target_var = tk.StringVar(value="52.3")
        ttk.Entry(dialog, textvariable=target_var, width=15, font=("Arial", 12)).pack()
        
        ttk.Label(dialog, text="并联电阻数量:", font=("Arial", 10)).pack(pady=(10,5))
        count_var = tk.StringVar(value="2")
        ttk.Combobox(dialog, textvariable=count_var, values=["2", "3", "4"], width=5, state="readonly").pack()
        
        result_text = scrolledtext.ScrolledText(dialog, height=15, width=60, font=("Courier", 10))
        result_text.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)
        
        def calculate_parallel():
            try:
                target_k = float(target_var.get())
                count = int(count_var.get())
                target_ohm = target_k * 1000
                
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"目标等效阻值: {target_k}kΩ ({target_ohm:.0f}Ω)\n")
                result_text.insert(tk.END, f"寻找 {count} 个 E24 标准电阻并联组合...\n")
                result_text.insert(tk.END, "="*56 + "\n\n")
                
                # 简化算法：使用相同阻值并联（最实用）
                single_r = target_k * count
                std_r = self.find_nearest_e24(single_r * 1000) / 1000
                
                eq_calc = std_r / count
                error_pct = (eq_calc - target_k) / target_k * 100
                
                result_text.insert(tk.END, f"【推荐方案】{count} 个相同电阻并联\n")
                result_text.insert(tk.END, f"  单个电阻: {std_r:.2f}kΩ (E24 标准值)\n")
                result_text.insert(tk.END, f"  并联等效: {eq_calc:.3f}kΩ (目标 {target_k}kΩ, 误差 {error_pct:+.2f}%)\n")
                result_text.insert(tk.END, f"  💡 优势: 采购简单，功率自动均分\n\n")
                
                # 备选：不同阻值组合（穷举前3名）
                if count == 2:
                    result_text.insert(tk.END, "【备选方案】2 个不同阻值并联:\n")
                    candidates = []
                    for r1_base in self.e24_values:
                        for exp1 in [1, 10, 100]:  # kΩ 范围
                            r1 = r1_base * exp1
                            if r1 < target_k * 1.5:  # 合理范围
                                r2 = 1 / (1/target_k - 1/r1) if (1/target_k - 1/r1) > 0 else 0
                                if r2 > target_k and r2 < 1000:
                                    r2_std = self.find_nearest_e24(r2 * 1000) / 1000
                                    eq = 1 / (1/r1 + 1/r2_std)
                                    err = abs(eq - target_k)
                                    candidates.append((err, r1, r2_std, eq))
                    
                    candidates.sort(key=lambda x: x[0])
                    for i, (err, r1, r2, eq) in enumerate(candidates[:3]):
                        err_pct = (eq - target_k) / target_k * 100
                        result_text.insert(tk.END, 
                            f"  {i+1}. {r1:.1f}kΩ ║ {r2:.1f}kΩ → {eq:.3f}kΩ (误差 {err_pct:+.2f}%)\n")
                
                result_text.insert(tk.END, "\n" + "="*56 + "\n")
                result_text.insert(tk.END, "💡 工程建议:\n")
                result_text.insert(tk.END, "   • 并联主要用于功率分配，而非精度提升\n")
                result_text.insert(tk.END, "   • 相同阻值并联最可靠，避免温漂不一致\n")
                result_text.insert(tk.END, "   • 单电阻功耗 > 1/8W 时，强烈建议并联分担!\n")
                
            except Exception as e:
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"计算错误: {str(e)}")
        
        ttk.Button(dialog, text="计算并联组合", command=calculate_parallel, 
                  style="Accent.TButton").pack(pady=5)
        ttk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=5)
    
    def open_power_analyzer(self):
        """功率分配分析器"""
        dialog = tk.Toplevel(self.root)
        dialog.title("⚖️ 功率分配分析器")
        dialog.geometry("480x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="总功耗要求 (mW):", font=("Arial", 10)).grid(row=0, column=0, padx=15, pady=10, sticky=tk.W)
        power_var = tk.StringVar(value="250")
        ttk.Entry(dialog, textvariable=power_var, width=10).grid(row=0, column=1, padx=5, pady=10)
        
        ttk.Label(dialog, text="目标等效阻值 (kΩ):", font=("Arial", 10)).grid(row=1, column=0, padx=15, pady=10, sticky=tk.W)
        r_eq_var = tk.StringVar(value="10")
        ttk.Entry(dialog, textvariable=r_eq_var, width=10).grid(row=1, column=1, padx=5, pady=10)
        
        ttk.Label(dialog, text="并联电阻数量:", font=("Arial", 10)).grid(row=2, column=0, padx=15, pady=10, sticky=tk.W)
        count_var = tk.StringVar(value="2")
        ttk.Combobox(dialog, textvariable=count_var, values=["2", "3", "4", "5"], width=5, state="readonly").grid(row=2, column=1, padx=5, pady=10)
        
        result_text = scrolledtext.ScrolledText(dialog, height=12, width=58, font=("Courier", 9))
        result_text.grid(row=3, column=0, columnspan=2, padx=15, pady=15)
        
        def analyze():
            try:
                total_power_mw = float(power_var.get())
                r_eq_k = float(r_eq_var.get())
                count = int(count_var.get())
                
                # 计算单个电阻值
                r_single_k = r_eq_k * count
                # 每个电阻功耗
                power_per_mw = total_power_mw / count
                
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"【功率分配分析】总功耗 {total_power_mw}mW, 等效阻值 {r_eq_k}kΩ\n")
                result_text.insert(tk.END, f"  并联数量: {count} 个 {r_single_k:.1f}kΩ 电阻\n")
                result_text.insert(tk.END, "="*56 + "\n\n")
                
                # 单电阻方案对比
                power_single_mw = total_power_mw
                rating_needed = "1/4W (250mW)" if power_single_mw <= 250 else "1/2W (500mW)" if power_single_mw <= 500 else "1W"
                result_text.insert(tk.END, f"❌ 单电阻方案:\n")
                result_text.insert(tk.END, f"   1 个 {r_eq_k}kΩ 电阻，功耗 {power_single_mw:.0f}mW\n")
                result_text.insert(tk.END, f"   需使用 {rating_needed} 电阻，体积大、成本高\n\n")
                
                # 并联方案
                rating_per = "1/8W (125mW)" if power_per_mw <= 125 else "1/4W (250mW)"
                result_text.insert(tk.END, f"✅ 并联方案 ({count} 个):\n")
                result_text.insert(tk.END, f"   每个电阻: {r_single_k:.1f}kΩ, 功耗 {power_per_mw:.0f}mW\n")
                result_text.insert(tk.END, f"   仅需 {rating_per} 标准电阻，体积小、成本低、可靠性高!\n\n")
                
                # 温升估算
                thermal_res = 200  # °C/W 典型值
                delta_t_single = (power_single_mw/1000) * thermal_res
                delta_t_parallel = (power_per_mw/1000) * thermal_res
                
                result_text.insert(tk.END, f"🌡️  温升对比 (估算):\n")
                result_text.insert(tk.END, f"   单电阻: ΔT ≈ {delta_t_single:.0f}°C (高温风险!)\n")
                result_text.insert(tk.END, f"   并联:   ΔT ≈ {delta_t_parallel:.0f}°C (安全)\n")
                
                result_text.insert(tk.END, "\n💡 结论: 当单电阻功耗 > 125mW 时，强烈建议并联分担!\n")
                
            except Exception as e:
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"分析错误: {str(e)}")
        
        ttk.Button(dialog, text="分析功率分配", command=analyze, 
                  style="Accent.TButton").grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(dialog, text="关闭", command=dialog.destroy).grid(row=5, column=0, columnspan=2)
    
    def open_precision_optimizer(self):
        """精度优化建议（利用并联降低容差）"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🎯 精度优化建议")
        dialog.geometry("520x420")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="目标阻值 (kΩ):", font=("Arial", 10)).grid(row=0, column=0, padx=15, pady=8, sticky=tk.W)
        target_var = tk.StringVar(value="52.3")
        ttk.Entry(dialog, textvariable=target_var, width=12).grid(row=0, column=1, padx=5, pady=8)
        
        ttk.Label(dialog, text="单电阻容差 (%):", font=("Arial", 10)).grid(row=1, column=0, padx=15, pady=8, sticky=tk.W)
        tol_var = tk.StringVar(value="1")
        ttk.Combobox(dialog, textvariable=tol_var, values=["0.1", "0.5", "1", "5"], width=6, state="readonly").grid(row=1, column=1, padx=5, pady=8)
        
        result_text = scrolledtext.ScrolledText(dialog, height=16, width=65, font=("Courier", 9))
        result_text.grid(row=2, column=0, columnspan=2, padx=15, pady=15)
        
        def optimize():
            try:
                target_k = float(target_var.get())
                tol_pct = float(tol_var.get())
                
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"【精度优化分析】目标 {target_k}kΩ, 单电阻容差 ±{tol_pct}%\n")
                result_text.insert(tk.END, "="*60 + "\n\n")
                
                # 方案1: 单电阻
                std_val = self.find_nearest_e24(target_k * 1000) / 1000
                err_single = abs(std_val - target_k) / target_k * 100
                total_tol_single = err_single + tol_pct
                
                result_text.insert(tk.END, f"方案1: 单电阻 {std_val:.2f}kΩ (E24)\n")
                result_text.insert(tk.END, f"  • 标称误差: {err_single:+.2f}%\n")
                result_text.insert(tk.END, f"  • 总容差: ±{total_tol_single:.2f}% (标称误差 + 电阻容差)\n\n")
                
                # 方案2: 串联组合
                r1 = self.find_nearest_e24(target_k * 1000 * 0.7) / 1000
                r2 = self.find_nearest_e24((target_k - r1) * 1000) / 1000
                eq_series = r1 + r2
                err_series = abs(eq_series - target_k) / target_k * 100
                # 串联容差：近似相加（最坏情况）
                total_tol_series = err_series + tol_pct * 2
                
                result_text.insert(tk.END, f"方案2: 串联组合 {r1:.2f}kΩ + {r2:.2f}kΩ\n")
                result_text.insert(tk.END, f"  • 标称误差: {err_series:+.2f}%\n")
                result_text.insert(tk.END, f"  • 总容差: ±{total_tol_series:.2f}% (两个电阻容差累积)\n\n")
                
                # 方案3: 并联组合（精度优势）
                # 使用两个相同电阻并联：R_eq = R/2
                r_parallel_single = target_k * 2
                r_p_std = self.find_nearest_e24(r_parallel_single * 1000) / 1000
                eq_parallel = r_p_std / 2
                err_parallel = abs(eq_parallel - target_k) / target_k * 100
                # 并联容差：统计上降低（假设独立正态分布）
                total_tol_parallel = math.sqrt(err_parallel**2 + (tol_pct / math.sqrt(2))**2)
                
                result_text.insert(tk.END, f"方案3: 并联组合 2×{r_p_std:.2f}kΩ\n")
                result_text.insert(tk.END, f"  • 标称误差: {err_parallel:+.2f}%\n")
                result_text.insert(tk.END, f"  • 总容差: ±{total_tol_parallel:.2f}% (并联降低容差影响!)\n")
                result_text.insert(tk.END, f"  💡 原理: 并联时随机误差部分抵消，等效容差 ≈ 单电阻/√N\n\n")
                
                # 推荐
                best_scheme = min([
                    (total_tol_single, "单电阻", std_val),
                    (total_tol_series, "串联", eq_series),
                    (total_tol_parallel, "并联", eq_parallel)
                ], key=lambda x: x[0])
                
                result_text.insert(tk.END, "="*60 + "\n")
                result_text.insert(tk.END, f"🏆 推荐方案: {best_scheme[1]} (总容差 ±{best_scheme[0]:.2f}%)\n")
                
                if best_scheme[1] == "并联":
                    result_text.insert(tk.END, "✅ 并联方案在精度和功率分配上均有优势!\n")
                
            except Exception as e:
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"优化错误: {str(e)}")
        
        ttk.Button(dialog, text="优化精度", command=optimize, 
                  style="Accent.TButton").grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(dialog, text="关闭", command=dialog.destroy).grid(row=4, column=0, columnspan=2)
    
    def open_ntc_calculator(self):
        """增强版 NTC 计算器"""
        ntc_win = tk.Toplevel(self.root)
        ntc_win.title("🌡️ NTC 温度-电阻-电压计算器")
        ntc_win.geometry("550x550")
        ntc_win.transient(self.root)
        ntc_win.grab_set()
        
        # 参数区
        param_frame = ttk.Frame(ntc_win, padding="15")
        param_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(param_frame, text="NTC 型号:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(param_frame, textvariable=self.ntc_model_var).grid(row=0, column=1, sticky=tk.W, pady=5, columnspan=2)
        
        ttk.Label(param_frame, text="R25 (Ω):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(param_frame, textvariable=self.ntc_r25_var, width=15).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(param_frame, text="B 值 (K):").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(param_frame, textvariable=self.ntc_b_var, width=15).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(param_frame, text="供电电压 Vin (V):").grid(row=3, column=0, sticky=tk.W, pady=5)
        vin_var = tk.StringVar(value="3.3")
        ttk.Entry(param_frame, textvariable=vin_var, width=15).grid(row=3, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(param_frame, text="上拉电阻 R1 (kΩ):").grid(row=4, column=0, sticky=tk.W, pady=5)
        r1_var = tk.StringVar(value="10")
        ttk.Entry(param_frame, textvariable=r1_var, width=15).grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # 温度↔电阻转换
        convert_frame = ttk.LabelFrame(param_frame, text="🌡️ ↔ Ω 双向转换", padding="10")
        convert_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        temp_var = tk.StringVar(value="25.0")
        res_var = tk.StringVar(value="10000")
        
        ttk.Label(convert_frame, text="温度 (°C):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(convert_frame, textvariable=temp_var, width=12).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(convert_frame, text="电阻 (Ω):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(convert_frame, textvariable=res_var, width=12).grid(row=1, column=1, padx=5, pady=5)
        
        def temp_to_res():
            try:
                t_c = float(temp_var.get())
                r25 = float(self.ntc_r25_var.get())
                b = float(self.ntc_b_var.get())
                t_k = t_c + 273.15
                t0_k = 25 + 273.15
                r_t = r25 * math.exp(b * (1/t_k - 1/t0_k))
                res_var.set(f"{r_t:.1f}")
            except:
                res_var.set("错误")
        
        def res_to_temp():
            try:
                r_t = float(res_var.get())
                r25 = float(self.ntc_r25_var.get())
                b = float(self.ntc_b_var.get())
                t0_k = 25 + 273.15
                t_k = 1 / (1/t0_k + (1/b) * math.log(r_t/r25))
                t_c = t_k - 273.15
                temp_var.set(f"{t_c:.1f}")
            except:
                temp_var.set("错误")
        
        ttk.Button(convert_frame, text="🌡️→Ω", command=temp_to_res, width=8).grid(row=0, column=2, padx=5)
        ttk.Button(convert_frame, text="Ω→🌡️", command=res_to_temp, width=8).grid(row=1, column=2, padx=5)
        
        # 电压计算
        volt_frame = ttk.LabelFrame(param_frame, text="分压输出电压", padding="10")
        volt_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(volt_frame, text="当前温度 (°C):").grid(row=0, column=0, sticky=tk.W, pady=5)
        temp_now_var = tk.StringVar(value="25")
        ttk.Entry(volt_frame, textvariable=temp_now_var, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        result_label = ttk.Label(volt_frame, text="", font=("Courier", 11, "bold"), foreground="#e74c3c")
        result_label.grid(row=1, column=0, columnspan=3, pady=10)
        
        def calc_voltage():
            try:
                t_c = float(temp_now_var.get())
                r25 = float(self.ntc_r25_var.get())
                b = float(self.ntc_b_var.get())
                vin = float(vin_var.get())
                r1 = float(r1_var.get()) * 1000  # 转为Ω
                
                # NTC 电阻
                t_k = t_c + 273.15
                t0_k = 25 + 273.15
                r_ntc = r25 * math.exp(b * (1/t_k - 1/t0_k))
                
                # 分压 (NTC 在下方)
                vout = vin * r_ntc / (r1 + r_ntc)
                
                result_label.config(text=f"NTC 电阻: {r_ntc/1000:.2f}kΩ  →  ADC 电压: {vout:.3f}V")
            except Exception as e:
                result_label.config(text=f"计算错误: {str(e)}")
        
        ttk.Button(volt_frame, text="计算电压", command=calc_voltage, 
                  style="Accent.TButton").grid(row=0, column=2, padx=10)
        
        # 温度表生成
        table_btn = ttk.Button(param_frame, text="📊 生成 -40~125°C 完整对照表", 
                              command=lambda: self.generate_ntc_full_table(ntc_win, vin_var, r1_var),
                              style="Accent.TButton")
        table_btn.grid(row=7, column=0, columnspan=3, pady=15, sticky=(tk.W, tk.E))
        
        ttk.Button(param_frame, text="关闭", command=ntc_win.destroy).grid(row=8, column=0, columnspan=3, pady=10)
    
    def generate_ntc_full_table(self, parent, vin_var, r1_var):
        """生成完整 NTC 温度-电压对照表"""
        try:
            vin = float(vin_var.get())
            r1 = float(r1_var.get()) * 1000  # Ω
            r25 = float(self.ntc_r25_var.get())
            b = float(self.ntc_b_var.get())
            
            table_win = tk.Toplevel(parent)
            table_win.title("NTC 温度-电压对照表 (-40~125°C)")
            table_win.geometry("500x600")
            
            text = scrolledtext.ScrolledText(table_win, font=("Courier", 9), width=65, height=38)
            text.pack(padx=10, pady=10)
            
            text.insert(tk.END, f"NTC: {self.ntc_model_var.get()}\n")
            text.insert(tk.END, f"R25={r25}Ω, B={b}K | 电路: {r1/1000:.1f}kΩ ── NTC ── GND, Vin={vin}V\n")
            text.insert(tk.END, "="*65 + "\n")
            text.insert(tk.END, f"{'Temp(°C)':<10} {'R_NTC(kΩ)':<15} {'Vout(V)':<12} {'ADC(12bit)':<15}\n")
            text.insert(tk.END, "="*65 + "\n")
            
            for temp in range(-40, 126, 5):
                t_k = temp + 273.15
                t0_k = 25 + 273.15
                r_ntc = r25 * math.exp(b * (1/t_k - 1/t0_k))
                vout = vin * r_ntc / (r1 + r_ntc)
                adc_val = int(vout / vin * 4095)
                text.insert(tk.END, f"{temp:<10} {r_ntc/1000:<15.2f} {vout:<12.3f} {adc_val:<15}\n")
            
            text.config(state=tk.DISABLED)
            
            # 添加导出按钮
            btn_frame = ttk.Frame(table_win)
            btn_frame.pack(pady=5)
            ttk.Button(btn_frame, text="导出 CSV", 
                      command=lambda: self.export_ntc_csv(temp, r_ntc, vout, adc_val, vin, r1, r25, b)).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="关闭", command=table_win.destroy).pack(side=tk.LEFT, padx=5)
        
        except Exception as e:
            messagebox.showerror("错误", str(e))
    
    def export_ntc_csv(self, *args):
        """导出 NTC 表到 CSV（简化实现）"""
        messagebox.showinfo("提示", "CSV 导出功能将在完整版中提供。\n当前可复制表格内容到 Excel。")
    
    def toggle_ntc_mode(self):
        """切换 R2 为 NTC 模式"""
        is_ntc = self.use_ntc_var.get()
        if is_ntc:
            # 保存当前 R2 网络
            self.r2_backup = self.r2_network.copy()
            # 设置典型 NTC 配置
            r25_k = float(self.ntc_r25_var.get()) / 1000
            self.r2_network = [(r25_k, 'series')]
            self.update_listbox('r2')
        else:
            # 恢复备份
            if hasattr(self, 'r2_backup'):
                self.r2_network = self.r2_backup.copy()
            else:
                self.r2_network = [(51, 'series')]
            self.update_listbox('r2')
        self.calculate_network()
    
    def update_ntc_params(self, event=None):
        """更新 NTC 参数"""
        model = self.ntc_model_var.get()
        params = self.ntc_models.get(model, {"r25": 10000, "b": 3950})
        self.ntc_r25_var.set(str(params["r25"]))
        self.ntc_b_var.set(str(params["b"]))
        if self.use_ntc_var.get():
            self.toggle_ntc_mode()  # 刷新 R2 值
    
    def load_template(self, template_name):
        """加载模板并配置网络"""
        tmpl = self.templates[template_name]
        tmpl_type = tmpl.get("type", "battery")
        
        if tmpl_type == "battery":
            self.vin_var.set(str(tmpl["vin_max"]))
            self.vout_var.set("3.25")
            self.adc_range_var.set("3.3")
            self.use_ntc_var.set(False)
            
            vin_max = tmpl["vin_max"]
            ratio = 3.25 / vin_max
            r2_r1 = ratio / (1 - ratio)
            r1_val = 18.0 if vin_max >= 4.5 else 15.0
            r2_val = r1_val * r2_r1
            r2_std = self.find_nearest_e24(r2_val * 1000) / 1000
            
            self.r1_network = [(r1_val, 'series')]
            self.r2_network = [(r2_std, 'series')]
            self.update_listbox('r1')
            self.update_listbox('r2')
        
        elif tmpl_type == "level_shift":
            self.vin_var.set(str(tmpl["vin"]))
            self.vout_var.set(str(tmpl["vout"]))
            self.adc_range_var.set("3.3")
            self.use_ntc_var.set(False)
            
            vin = tmpl["vin"]
            vout = tmpl["vout"]
            ratio = vout / vin
            r2_r1 = ratio / (1 - ratio)
            r1_val = 10.0
            r2_val = r1_val * r2_r1
            r2_std = self.find_nearest_e24(r2_val * 1000) / 1000
            
            self.r1_network = [(r1_val, 'series')]
            self.r2_network = [(r2_std, 'series')]
            self.update_listbox('r1')
            self.update_listbox('r2')
        
        elif tmpl_type == "ntc":
            self.vin_var.set("3.3")
            self.vout_var.set("1.65")  # 25°C 时的典型值
            self.adc_range_var.set("3.3")
            self.use_ntc_var.set(True)
            self.ntc_model_var.set("MF52-103 (10k@25°C, B=3950)")
            self.update_ntc_params()
            
            self.r1_network = [(10, 'series')]  # 10k 上拉
            self.r2_network = [(10, 'series')]  # NTC 25°C 时 10k
            self.update_listbox('r1')
            self.update_listbox('r2')
        
        elif tmpl_type == "parallel_power":
            self.vin_var.set("12.0")
            self.vout_var.set("6.0")
            self.adc_range_var.set("3.3")
            self.use_ntc_var.set(False)
            
            # 并联功率分配示例：等效 10k，用 3 个 30k 并联
            self.r1_network = [(10, 'series')]
            self.r2_network = [('parallel', [
                [(30, 'series')],
                [(30, 'series')],
                [(30, 'series')]
            ])]
            self.update_listbox('r1')
            self.update_listbox('r2')
        
        elif tmpl_type == "parallel_precision":
            self.vin_var.set("5.0")
            self.vout_var.set("3.3")
            self.adc_range_var.set("3.3")
            self.use_ntc_var.set(False)
            
            # 精度优化：52.3k 用 100k//100k//100k ≈ 33.3k (示例)
            self.r1_network = [(20, 'series')]
            self.r2_network = [('parallel', [
                [(100, 'series')],
                [(100, 'series')],
                [(100, 'series')]
            ])]
            self.update_listbox('r1')
            self.update_listbox('r2')
        
        self.calculate_network()
        self.status_var.set(f"✅ 已加载模板: {template_name}")
    
    def export_bom(self):
        """导出增强版 BOM（含并联分支）"""
        try:
            r1_eq = self.calculate_equivalent(self.r1_network)
            r2_eq = self.calculate_equivalent(self.r2_network)
            vin = float(self.vin_var.get())
            vout = vin * r2_eq / (r1_eq + r2_eq) if (r1_eq + r2_eq) > 0 else 0
            
            bom_lines = []
            bom_lines.append("="*70)
            bom_lines.append("📋 BOM 清单 (Bill of Materials) - 支持并联网络")
            bom_lines.append("="*70)
            bom_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            bom_lines.append(f"电路类型: 电阻分压网络 (Vin={vin}V → Vout={vout:.3f}V)")
            bom_lines.append(f"R1_eq={r1_eq:.2f}kΩ | R2_eq={r2_eq:.2f}kΩ | 安全裕量: {max(0, 3.25-vout):.2f}V")
            bom_lines.append("-"*70)
            bom_lines.append(f"{'Ref':<10} {'Value':<15} {'Type':<20} {'Power':<12} {'Notes'}")
            bom_lines.append("-"*70)
            
            # 解析 R1 网络
            r1_items = self._flatten_network(self.r1_network, "R1")
            for ref, val, typ, power in r1_items:
                notes = "功率分担" if "parallel" in typ.lower() else ""
                bom_lines.append(f"{ref:<10} {val:<15} {typ:<20} {power:<12} {notes}")
            
            # 解析 R2 网络
            is_ntc = self.use_ntc_var.get()
            r2_items = self._flatten_network(self.r2_network, "R2", is_ntc)
            for ref, val, typ, power in r2_items:
                notes = "NTC 热敏电阻" if is_ntc and "NTC" in ref else "功率分担" if "parallel" in typ.lower() else ""
                bom_lines.append(f"{ref:<10} {val:<15} {typ:<20} {power:<12} {notes}")
            
            # 保护元件
            bom_lines.append(f"{'C1':<10} {'0.1μF':<15} {'Ceramic Cap':<20} {'10V':<12} X7R, 0603")
            bom_lines.append("="*70)
            bom_lines.append("\n💡 采购建议:")
            bom_lines.append("   • 电阻: 1% 精度金属膜电阻 (Yageo RC0603FR-07xxxL)")
            bom_lines.append("   • 功率: 单电阻功耗 > 125mW 时，必须使用 1/4W 或并联分担")
            bom_lines.append("   • NTC:  MF52 系列径向引线型，焊接方便")
            bom_lines.append("   • 电容: 0603 封装 0.1μF X7R 陶瓷电容 (Murata GRM188R71H104KA01D)")
            
            output = "\n".join(bom_lines)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, output)
            
            if messagebox.askyesno("导出 BOM", "是否保存 BOM 到文件?"):
                filename = f"resistor_bom_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(output)
                messagebox.showinfo("成功", f"BOM 已保存:\n{filename}")
                self.status_var.set(f"✅ BOM 已导出到 {filename}")
        
        except Exception as e:
            messagebox.showerror("BOM 导出错误", str(e))
    
    def _flatten_network(self, network, prefix, is_ntc=False):
        """扁平化网络为 BOM 条目列表"""
        items = []
        idx = 1
        
        for element in network:
            if isinstance(element, tuple) and element[0] == 'parallel':
                # 并联组
                branches = element[1]
                for branch in branches:
                    if branch:
                        r_val = branch[0][0]
                        ref = f"{prefix}_P{idx}"
                        typ = "Resistor (Parallel Branch)"
                        power = "1/8W" if r_val > 10 else "1/4W"
                        items.append((ref, f"{r_val}kΩ", typ, power))
                        idx += 1
            else:
                # 串联电阻
                r_val = element[0]
                ref = "NTC1" if (is_ntc and prefix == "R2" and idx == 1) else f"{prefix}_{idx}"
                typ = "NTC Thermistor" if ref == "NTC1" else "Resistor"
                power = "1/8W" if r_val > 10 else "1/4W"
                items.append((ref, f"{r_val}kΩ", typ, power))
                idx += 1
        
        return items
    
    def save_config(self):
        """保存当前配置到文件"""
        config = {
            "vin": self.vin_var.get(),
            "vout_target": self.vout_var.get(),
            "adc_range": self.adc_range_var.get(),
            "r1_network": self.r1_network,
            "r2_network": self.r2_network,
            "use_ntc": self.use_ntc_var.get(),
            "ntc_model": self.ntc_model_var.get(),
            "ntc_r25": self.ntc_r25_var.get(),
            "ntc_b": self.ntc_b_var.get(),
            "timestamp": datetime.now().isoformat()
        }
        
        filename = f"resistor_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("成功", f"配置已保存到:\n{filename}")
            self.status_var.set(f"✅ 配置已保存到 {filename}")
        except Exception as e:
            messagebox.showerror("保存错误", str(e))
    
    def load_config(self):
        """从文件加载配置"""
        try:
            filename = filedialog.askopenfilename(
                title="选择配置文件",
                filetypes=[("JSON 配置", "*.json"), ("所有文件", "*.*")]
            )
            if not filename:
                return
            
            with open(filename, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 恢复配置
            self.vin_var.set(config.get("vin", "4.2"))
            self.vout_var.set(config.get("vout_target", "3.25"))
            self.adc_range_var.set(config.get("adc_range", "3.3"))
            self.r1_network = config.get("r1_network", [(15, 'series')])
            self.r2_network = config.get("r2_network", [(51, 'series')])
            self.use_ntc_var.set(config.get("use_ntc", False))
            self.ntc_model_var.set(config.get("ntc_model", "MF52-103 (10k@25°C, B=3950)"))
            self.ntc_r25_var.set(config.get("ntc_r25", "10000"))
            self.ntc_b_var.set(config.get("ntc_b", "3950"))
            
            self.update_listbox('r1')
            self.update_listbox('r2')
            self.update_ntc_params()
            self.calculate_network()
            
            self.status_var.set(f"✅ 配置已从 {filename} 加载")
            messagebox.showinfo("成功", f"配置已加载:\n{filename}")
        
        except Exception as e:
            messagebox.showerror("加载错误", str(e))

def main():
    root = tk.Tk()
    
    # 设置现代化主题
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use('clam')
        style.configure("TButton", padding=6)
        style.configure("Accent.TButton", background="#3498db", foreground="white")
        style.map("Accent.TButton", 
                 background=[('active', '#2980b9')],
                 foreground=[('active', 'white')])
    
    app = ResistorNetworkCalculator(root)
    root.mainloop()

if __name__ == "__main__":
    main()