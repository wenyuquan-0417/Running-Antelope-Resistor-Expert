#!/usr/bin/env python3
# resistor_divider_cli.py
# 命令行版电阻分压计算器

import sys
import math

def find_nearest_e24(value):
    """在 E24 系列中查找最接近的值"""
    e24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
           3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
    decades = [1e-3, 1e-2, 1e-1, 1, 10, 100, 1000, 1e6]
    
    best_diff = float('inf')
    best_val = None
    for base in e24:
        for dec in decades:
            cand = base * dec
            diff = abs(cand - value)
            if diff < best_diff:
                best_diff = diff
                best_val = cand
    return best_val

def calculate(vin, vout, r1=None, r2=None):
    """计算缺失的电阻值"""
    if r1 is None and r2 is None:
        print("❌ 错误: 必须提供 R1 或 R2 中的至少一个")
        return
    
    if vout >= vin:
        print("❌ 错误: Vout 必须小于 Vin")
        return
    
    if r1 is not None and r2 is None:
        # 已知 R1，求 R2
        r2_calc = r1 * vout / (vin - vout)
        r2_std = find_nearest_e24(r2_calc)
        vout_actual = vin * r2_std / (r1 + r2_std)
        error = (vout_actual - vout) / vout * 100
        
        print(f"\n✅ 计算结果 (Vin={vin}V → Vout={vout}V):")
        print(f"   已知 R1 = {r1}kΩ")
        print(f"   理论 R2 = {r2_calc:.3f}kΩ")
        print(f"   推荐 R2 = {r2_std:.2f}kΩ (E24 标准值)")
        print(f"   实际 Vout = {vout_actual:.3f}V (误差 {error:+.2f}%)")
        print(f"   静态电流 = {vin/(r1+r2_std):.3f}mA")
    
    elif r2 is not None and r1 is None:
        # 已知 R2，求 R1
        r1_calc = r2 * (vin - vout) / vout
        r1_std = find_nearest_e24(r1_calc)
        vout_actual = vin * r2 / (r1_std + r2)
        error = (vout_actual - vout) / vout * 100
        
        print(f"\n✅ 计算结果 (Vin={vin}V → Vout={vout}V):")
        print(f"   已知 R2 = {r2}kΩ")
        print(f"   理论 R1 = {r1_calc:.3f}kΩ")
        print(f"   推荐 R1 = {r1_std:.2f}kΩ (E24 标准值)")
        print(f"   实际 Vout = {vout_actual:.3f}V (误差 {error:+.2f}%)")
        print(f"   静态电流 = {vin/(r1_std+r2):.3f}mA")

def battery_mode(vmin, vmax, vadc_safe=3.25):
    """电池监测模式"""
    print(f"\n🔋 电池监测配置 (范围 {vmin}V – {vmax}V, ADC 安全上限 {vadc_safe}V)")
    print("="*60)
    
    ratio = vadc_safe / vmax
    r2_r1 = ratio / (1 - ratio)
    
    candidates = [15, 18, 20, 22, 39, 47, 51]
    results = []
    
    for r1 in candidates:
        r2_calc = r1 * r2_r1
        r2_std = find_nearest_e24(r2_calc)
        vout_max = vmax * r2_std / (r1 + r2_std)
        vout_min = vmin * r2_std / (r1 + r2_std)
        margin = vadc_safe - vout_max
        current = vmax / (r1 + r2_std)
        
        if margin > 0.05:  # 至少 50mV 裕量
            results.append((margin, r1, r2_std, vout_min, vout_max, current))
    
    results.sort(reverse=True)
    
    for i, (margin, r1, r2, vmin_out, vmax_out, curr) in enumerate(results[:3]):
        print(f"\n【方案 #{i+1}】R1={r1}kΩ + R2={r2:.1f}kΩ")
        print(f"   • {vmax}V 时: {vmax_out:.3f}V (安全裕量 {margin*1000:.0f}mV) ✅")
        print(f"   • {vmin}V 时: {vmin_out:.3f}V")
        print(f"   • 静态功耗: {curr*1000:.1f}μA")

if __name__ == "__main__":
    print("⚡ 电阻分压计算器 (命令行版)")
    print("用法示例:")
    print("  1. 已知 Vin/Vout/R1 求 R2:  python resistor_divider_cli.py 4.2 3.25 15")
    print("  2. 已知 Vin/Vout/R2 求 R1:  python resistor_divider_cli.py 4.2 3.25 - 51")
    print("  3. 电池监测模式:           python resistor_divider_cli.py battery 3.0 4.5")
    
    if len(sys.argv) < 2:
        sys.exit(1)
    
    if sys.argv[1] == "battery" and len(sys.argv) >= 4:
        vmin = float(sys.argv[2])
        vmax = float(sys.argv[3])
        vadc = float(sys.argv[4]) if len(sys.argv) > 4 else 3.25
        battery_mode(vmin, vmax, vadc)
    elif len(sys.argv) >= 4:
        vin = float(sys.argv[1])
        vout = float(sys.argv[2])
        arg3 = sys.argv[3]
        
        if arg3 == "-":
            # R1 未知，R2 已知
            r2 = float(sys.argv[4])
            calculate(vin, vout, r1=None, r2=r2)
        else:
            # R1 已知，R2 未知
            r1 = float(arg3)
            calculate(vin, vout, r1=r1, r2=None)
    else:
        print("❌ 参数错误，请参考用法示例")