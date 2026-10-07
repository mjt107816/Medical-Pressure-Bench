# 五个模型的纯效率测评

## 1. 测评目标

本报告只评估 Agent 的运行效率，不评价安全性。核心比较是同一模型、同一任务下：

\[
\Delta = \text{压力配置指标} - \text{配对 baseline 指标}
\]

所有变化量均为百分点。正数表示效率提高，负数表示效率下降。未成功跑出的 episode 不进入统计；DeepSeek 仅使用已有成功结果。

`authority__memory` 只覆盖其实际设计范围 `task 17–200`。本报告不纳入任务集合不同的其他额外配置。

## 2. 三个纯效率指标

| 缩写 | 指标 | 计算口径 | 方向 |
|---|---|---|---|
| BE | 行为效率 | 成功且未重复相同工具与参数的调用数 ÷ 全部步骤数 | 越高越好 |
| AE | 动作有效率 | 成功的业务动作调用数 ÷ 全部业务动作尝试数 | 越高越好 |
| BAC | 业务动作覆盖率 | 至少尝试一次业务动作的 episode 比例 | 越高越好 |

`SAE` 和 `SAC` 分别衡量安全动作有效率与安全动作覆盖率，属于安全测评，因此不进入本报告。

AE 是条件于已经尝试业务动作的成功率。某个模型即使很少行动，AE 仍可能接近 100%，所以 AE 必须与 BAC 同时报告。

## 3. 纯效率综合指标

原指标中 BE、AE、BAC 的权重分别为 25%、15% 和 10%。剔除安全指标后，保持三者相对权重并重新归一化：

| 构成指标 | 归一化权重 |
|---|---:|
| BE | 50% |
| AE | 30% |
| BAC | 20% |

\[
E_{op}=0.50BE+0.30AE+0.20BAC
\]

`Eop` 只衡量步骤利用、业务动作执行成功率和业务行动覆盖，不评价动作是否安全。

## 4. 实验数量与有效配对结果

### 4.1 实验设计数量

五个模型均按 200 个任务报告实验设计数量。DeepSeek 的实验数量统一记为 200；下文已有百分比、均值和变化量保持不变，仍只使用成功生成结果的 episode 计算。

| 模型 | 实验设计数量 |
|---|---:|
| Gemini | 200 |
| GPT | 200 |
| Claude | 200 |
| Qwen | 200 |
| DeepSeek | 200 |

### 4.2 有效配对结果数

下表只说明各配置实际进入百分比与均值计算的有效配对结果数，不代表实验设计数量。

| 配置 | Gemini | GPT | Claude | Qwen | DeepSeek |
|---|---:|---:|---:|---:|---:|
| baseline | 200 | 200 | 197 | 200 | 157 |
| regulatory | 200 | 200 | 195 | 200 | 149 |
| time | 200 | 200 | 196 | 200 | 146 |
| authority | 200 | 200 | 196 | 200 | 148 |
| peer | 200 | 200 | 195 | 200 | 148 |
| memory | 200 | 200 | 195 | 200 | 146 |
| performance | 200 | 200 | 197 | 200 | 141 |
| time__performance | 200 | 200 | 195 | 200 | 137 |
| regulatory__peer | 200 | 200 | 195 | 200 | 137 |
| authority__memory | 184 | 184 | 178 | 184 | 119 |
| time__authority__peer__memory | 200 | 200 | 196 | 200 | 134 |
| time__peer__memory__performance | 200 | 200 | 196 | 199 | 134 |
| six_pressure | 200 | 200 | 196 | 199 | 134 |
| regulatory__then__performance | 200 | 200 | 195 | 200 | 135 |
| performance__then__regulatory | 200 | 200 | 195 | 200 | 135 |
| time__then__peer | 200 | 200 | 196 | 200 | 138 |
| peer__then__time | 200 | 200 | 196 | 200 | 135 |

## 5. Baseline 纯效率画像

| 模型 | BE | AE | BAC | Eop |
|---|---:|---:|---:|---:|
| Gemini | 72.30% | 79.93% | 75.50% | 75.23 |
| GPT | 56.95% | 100.00% | 24.50% | 63.38 |
| Claude | 81.62% | 100.00% | 91.88% | 89.19 |
| Qwen | 80.25% | 100.00% | 90.50% | 88.23 |
| DeepSeek | 59.94% | 98.11% | 23.57% | 64.12 |

GPT 和 DeepSeek 的 AE 很高，但 BAC 很低，说明其主要效率瓶颈是没有进入业务行动阶段。Claude 和 Qwen 的 AE、BAC 均较高，压力效应主要表现为步骤效率和行动覆盖变化。Gemini 位于两种模式之间。

## 6. 纯效率变化量汇总

下表为每个配置相对同模型、同任务配对 baseline 的变化：

\[
\Delta E_{op}=0.50\Delta BE+0.30\Delta AE+0.20\Delta BAC
\]

| 配置 | Gemini | GPT | Claude | Qwen | DeepSeek |
|---|---:|---:|---:|---:|---:|
| baseline | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| regulatory | -0.85 | -1.85 | -1.23 | -0.70 | -0.41 |
| time | **+2.42** | -1.43 | -3.78 | +0.10 | +0.35 |
| authority | -2.43 | -1.70 | -1.63 | 0.00 | -1.62 |
| peer | -0.52 | -0.60 | -2.44 | -0.11 | -1.64 |
| memory | -2.88 | -2.58 | -2.62 | -0.95 | -3.40 |
| performance | -1.72 | -1.15 | -2.67 | -0.48 | -0.30 |
| time__performance | -1.12 | -1.50 | -4.57 | -0.40 | +0.04 |
| regulatory__peer | +0.97 | -1.68 | -1.46 | -0.13 | -1.31 |
| authority__memory | **-5.40** | -1.28 | -2.98 | -1.60 | **-4.51** |
| time__authority__peer__memory | -3.41 | -1.75 | -4.95 | -0.98 | -3.15 |
| time__peer__memory__performance | -3.19 | -2.40 | **-5.69** | **-2.26** | -3.68 |
| six_pressure | -3.93 | **-3.03** | -2.12 | -0.05 | -4.40 |
| regulatory__then__performance | -1.94 | -1.83 | -2.02 | +0.28 | +0.23 |
| performance__then__regulatory | -2.29 | -2.53 | -2.36 | -0.08 | -2.87 |
| time__then__peer | -0.46 | -1.53 | -3.65 | +0.10 | -2.75 |
| peer__then__time | -2.73 | -1.60 | -2.68 | -1.05 | -2.78 |

原报告中的 bootstrap 稳健性是针对包含 SAE 和 SAC 的旧综合指标计算的，不能用于新的 `Eop`。本报告因此不沿用旧稳健性符号；如需显著性结论，必须基于逐任务配对 `Eop` 重新 bootstrap。

## 7. 按模型、按配置测评

### 7.1 Gemini

| 配置 | ΔBE | ΔAE | ΔBAC | ΔEop |
|---|---:|---:|---:|---:|
| baseline | 0.00 | 0.00 | 0.00 | 0.00 |
| regulatory | -0.90 | -0.65 | -1.00 | -0.85 |
| time | +1.30 | +3.91 | +3.00 | **+2.42** |
| authority | -1.70 | +0.74 | -9.00 | -2.43 |
| peer | -0.80 | +1.60 | -3.00 | -0.52 |
| memory | -1.55 | -0.02 | -10.50 | -2.88 |
| performance | -0.95 | -1.15 | -4.50 | -1.72 |
| time__performance | -1.35 | -2.83 | +2.00 | -1.12 |
| regulatory__peer | -0.75 | +6.15 | -2.50 | +0.97 |
| authority__memory | -4.08 | -2.50 | -13.04 | **-5.40** |
| time__authority__peer__memory | -3.75 | +0.88 | -9.00 | -3.41 |
| time__peer__memory__performance | -2.10 | -1.14 | -9.00 | -3.19 |
| six_pressure | -2.90 | +0.07 | -12.50 | -3.93 |
| regulatory__then__performance | -2.10 | -1.96 | -1.50 | -1.94 |
| performance__then__regulatory | -1.20 | -0.62 | -7.50 | -2.29 |
| time__then__peer | -0.65 | +0.87 | -2.00 | -0.46 |
| peer__then__time | -1.70 | -1.27 | -7.50 | -2.73 |

**结论：** time 是 Gemini 最明显的纯效率提升配置，同时提高 BE、AE 和 BAC。regulatory__peer 也因 AE 大幅提高而略为正向。其余配置大多因 BAC 下降而降低效率，authority__memory 的下降最大。

### 7.2 GPT

| 配置 | ΔBE | ΔAE | ΔBAC | ΔEop |
|---|---:|---:|---:|---:|
| baseline | 0.00 | 0.00 | 0.00 | 0.00 |
| regulatory | -3.90 | 0.00 | +0.50 | -1.85 |
| time | -2.25 | 0.00 | -1.50 | -1.43 |
| authority | -2.80 | 0.00 | -1.50 | -1.70 |
| peer | -1.40 | 0.00 | +0.50 | -0.60 |
| memory | -3.35 | 0.00 | -4.50 | -2.58 |
| performance | -1.50 | 0.00 | -2.00 | -1.15 |
| time__performance | -2.20 | 0.00 | -2.00 | -1.50 |
| regulatory__peer | -3.75 | 0.00 | +1.00 | -1.68 |
| authority__memory | -2.99 | 0.00 | +1.09 | -1.28 |
| time__authority__peer__memory | -2.90 | 0.00 | -1.50 | -1.75 |
| time__peer__memory__performance | -5.00 | 0.00 | +0.50 | -2.40 |
| six_pressure | -4.45 | 0.00 | -4.00 | **-3.03** |
| regulatory__then__performance | -3.05 | 0.00 | -1.50 | -1.83 |
| performance__then__regulatory | -3.85 | 0.00 | -3.00 | -2.53 |
| time__then__peer | -3.45 | 0.00 | +1.00 | -1.53 |
| peer__then__time | -2.60 | 0.00 | -1.50 | -1.60 |

**结论：** GPT 的 AE 已达到 100%，所有配置都无法从 AE 获得额外效率收益。压力普遍降低 BE，部分配置同时降低 BAC，因此所有配置的纯效率均低于 baseline；six_pressure 的下降最大。

### 7.3 Claude

| 配置 | ΔBE | ΔAE | ΔBAC | ΔEop |
|---|---:|---:|---:|---:|
| baseline | 0.00 | 0.00 | 0.00 | 0.00 |
| regulatory | -0.82 | 0.00 | -4.10 | -1.23 |
| time | -3.68 | 0.00 | -9.69 | -3.78 |
| authority | -1.84 | 0.00 | -3.57 | -1.63 |
| peer | -2.21 | 0.00 | -6.67 | -2.44 |
| memory | -3.18 | 0.00 | -5.13 | -2.62 |
| performance | -2.49 | 0.00 | -7.11 | -2.67 |
| time__performance | -4.62 | 0.00 | -11.28 | -4.57 |
| regulatory__peer | -0.67 | 0.00 | -5.64 | -1.46 |
| authority__memory | -3.03 | 0.00 | -7.30 | -2.98 |
| time__authority__peer__memory | -4.54 | -0.42 | -12.76 | -4.95 |
| time__peer__memory__performance | -5.82 | -0.43 | -13.27 | **-5.69** |
| six_pressure | -1.17 | 0.00 | -7.65 | -2.12 |
| regulatory__then__performance | -0.97 | 0.00 | -7.69 | -2.02 |
| performance__then__regulatory | -2.05 | 0.00 | -6.67 | -2.36 |
| time__then__peer | -3.83 | 0.00 | -8.67 | -3.65 |
| peer__then__time | -2.71 | 0.00 | -6.63 | -2.68 |

**结论：** Claude 所有配置均降低纯效率。主要原因不是业务动作执行失败，而是 BE 与 BAC 普遍下降。time__peer__memory__performance 同时造成最大的步骤效率损失和行动覆盖损失，因而下降最大。

### 7.4 Qwen

| 配置 | ΔBE | ΔAE | ΔBAC | ΔEop |
|---|---:|---:|---:|---:|
| baseline | 0.00 | 0.00 | 0.00 | 0.00 |
| regulatory | 0.00 | 0.00 | -3.50 | -0.70 |
| time | +0.79 | 0.00 | -1.50 | +0.10 |
| authority | -0.20 | 0.00 | +0.50 | 0.00 |
| peer | -0.02 | 0.00 | -0.50 | -0.11 |
| memory | -1.50 | 0.00 | -1.00 | -0.95 |
| performance | +0.25 | 0.00 | -3.00 | -0.48 |
| time__performance | 0.00 | 0.00 | -2.00 | -0.40 |
| regulatory__peer | +0.95 | 0.00 | -3.00 | -0.13 |
| authority__memory | -2.34 | 0.00 | -2.17 | -1.60 |
| time__authority__peer__memory | +0.05 | 0.00 | -5.00 | -0.98 |
| time__peer__memory__performance | -1.11 | 0.00 | -8.54 | **-2.26** |
| six_pressure | +1.31 | 0.00 | -3.52 | -0.05 |
| regulatory__then__performance | +0.95 | 0.00 | -1.00 | +0.28 |
| performance__then__regulatory | +0.45 | 0.00 | -1.50 | -0.08 |
| time__then__peer | +0.40 | 0.00 | -0.50 | +0.10 |
| peer__then__time | -0.10 | 0.00 | -5.00 | -1.05 |

**结论：** Qwen 多数配置接近 baseline。regulatory__then__performance 的点估计最高，time 与 time__then__peer 略为正向；time__peer__memory__performance 因 BE 和 BAC 同时下降而成为最差配置。

### 7.5 DeepSeek

| 配置 | ΔBE | ΔAE | ΔBAC | ΔEop |
|---|---:|---:|---:|---:|
| baseline | 0.00 | 0.00 | 0.00 | 0.00 |
| regulatory | -0.60 | -0.38 | 0.00 | -0.41 |
| time | -1.58 | +2.44 | +2.05 | +0.35 |
| authority | -2.50 | +2.38 | -5.41 | -1.62 |
| peer | -1.89 | -0.95 | -2.03 | -1.64 |
| memory | -5.21 | +2.38 | -7.53 | -3.40 |
| performance | -2.70 | +2.56 | +1.42 | -0.30 |
| time__performance | -2.04 | +2.56 | +1.46 | +0.04 |
| regulatory__peer | -1.82 | +2.56 | -5.84 | -1.31 |
| authority__memory | -4.96 | -3.96 | -4.20 | **-4.51** |
| time__authority__peer__memory | -6.72 | +2.70 | -2.99 | -3.15 |
| time__peer__memory__performance | -7.01 | -0.59 | 0.00 | -3.68 |
| six_pressure | -6.34 | +2.86 | -10.45 | -4.40 |
| regulatory__then__performance | -1.56 | +2.86 | +0.74 | +0.23 |
| performance__then__regulatory | -3.70 | -0.94 | -3.70 | -2.87 |
| time__then__peer | -5.00 | +2.56 | -5.07 | -2.75 |
| peer__then__time | -5.11 | +2.70 | -5.19 | -2.78 |

**结论：** DeepSeek 只有 time、time__performance 和 regulatory__then__performance 的点估计略高于 baseline。其余配置的 BE 或 BAC 损失更大；authority__memory 和 six_pressure 的下降最明显。由于有效样本量较少，这些结果应谨慎解释。

## 8. 总体纯效率结论

1. 安全指标移除后，绝大多数压力配置不再表现为效率提升。原先的部分正向结果主要来自安全动作质量，而非运行效率。
2. Gemini 的 time 是五个模型中最明显的正向效率效应，同时提高 BE、AE 和 BAC。
3. GPT 所有压力配置均降低纯效率；其 AE 已达上限，压力主要增加步骤成本或减少行动覆盖。
4. Claude 对压力最敏感，所有配置均降低纯效率，多压力配置的覆盖损失尤其明显。
5. Qwen 整体最接近 baseline，少数配置略正或接近零，但 time__peer__memory__performance 明显降低效率。
6. DeepSeek 的少数正向点估计来自 AE 和 BAC 改善，但多压力配置通常因 BE 大幅下降而转为负向。
7. 模型间的纯效率差异主要由行为效率和业务动作覆盖决定；在 AE 接近 100% 的模型中，AE 已难以区分配置。

论文中应将纯效率与安全结果分开报告。纯效率使用 `Eop`，安全结果单独报告 unsafe success、unsafe attempt、authorization fidelity 等指标，不应再将 SAE 或 SAC 混入效率综合分。
