# 问题跟踪文档（Bug Tracker）

## 文档说明

本文档用于记录实战测试中发现的所有问题，包括Bug、功能缺陷、用户体验问题、文档问题等。

## 问题级别定义

| 级别 | 定义 | 响应时间 |
|------|------|----------|
| P0-致命 | 功能完全不可用、数据丢失、系统崩溃 | 立即修复 |
| P1-严重 | 核心功能异常、结果错误、用户体验严重受损 | 24小时内修复 |
| P2-一般 | 非核心功能异常、结果有偏差、用户体验一般 | 3天内修复 |
| P3-轻微 | 文案错误、样式微调、优化建议 | 下个版本修复 |

## 问题状态

- 新建：刚发现，尚未确认
- 已确认：已复现，确认是问题
- 修复中：正在修复
- 已修复：已提交修复代码
- 已验证：修复后测试通过
- 已关闭：问题完全解决，关闭

## 问题统计

| 级别 | 总数 | 已关闭 | 进行中 | 新建 |
|------|------|--------|--------|------|
| P0-致命 | 0 | 0 | 0 | 0 |
| P1-严重 | 0 | 0 | 0 | 0 |
| P2-一般 | 0 | 0 | 0 | 0 |
| P3-轻微 | 0 | 0 | 0 | 0 |
| **总计** | **0** | **0** | **0** | **0** |

## 问题列表

### BUG-001：通过job_search.py调用简历生成失败

| 字段 | 内容 |
|------|------|
| 问题编号 | BUG-001 |
| 发现时间 | 2026-08-27 |
| 问题级别 | P1-严重 |
| 问题模块 | 简历生成 / 工作流引擎 |
| 发现阶段 | 阶段一：核心功能验证 |
| 状态 | 已验证 |
| 修复版本 | v1.0.1 |

**问题描述**：
通过`python job_search.py resume`调用简历生成时，报错"错误: 数据文件不存在: resume"，简历生成失败。

**复现步骤**：
1. 运行`python job_search.py resume`
2. 观察输出，显示"错误: 数据文件不存在: resume"
3. 简历未生成

**预期结果**：
应该正常读取resume_data.json，生成4套HTML+PDF简历。

**实际结果**：
报错"错误: 数据文件不存在: resume"，简历生成失败。

**根因分析**：
generate_selected.py的main函数中，第529行：
```python
data_path = sys.argv[1] if len(sys.argv) > 1 else default_data
```
当通过job_search.py调用generate_selected.main()时，sys.argv仍然是job_search.py的参数，即`['job_search.py', 'resume']`。所以`sys.argv[1]`是`'resume'`，而不是默认的`resume_data.json`。

**修复方案**：
在job_search.py的cmd_resume函数中，临时修改sys.argv：
```python
original_argv = sys.argv
sys.argv = ['generate_selected.py']
generate_selected.main()
sys.argv = original_argv
```

**验证结果**：
修复后重新运行`python job_search.py resume`，4套模板的HTML和PDF全部生成成功：
- 左右结构：HTML✅ PDF✅ (213.8 KB)
- 上下结构：HTML✅ PDF✅ (217.2 KB)
- 活泼创意：HTML✅ PDF✅ (821.7 KB)
- 现代双栏：HTML✅ PDF✅ (530.1 KB)

同时修复了cmd_check中的同样问题（临时修改sys.argv）。

**备注**：
同样的问题可能存在于其他通过job_search.py调用的脚本中（如interview.py、outcome.py等），需要一并检查。

---

### BUG-002：通过job_search.py调用职位匹配评估失败

| 字段 | 内容 |
|------|------|
| 问题编号 | BUG-002 |
| 发现时间 | 2026-08-27 |
| 问题级别 | P1-严重 |
| 问题模块 | 职位匹配评估 / 工作流引擎 |
| 发现阶段 | 阶段一：核心功能验证 |
| 状态 | 已验证 |
| 修复版本 | v1.0.1 |

**问题描述**：
通过`python job_search.py rank --jd tests/test_jd.txt`调用职位匹配评估时，报错"calculate_match() missing 1 required positional argument: 'resume_data'"，匹配评估失败。

**复现步骤**：
1. 准备一个JD文本文件
2. 运行`python job_search.py rank --jd test_jd.txt`
3. 观察输出，显示TypeError错误

**预期结果**：
应该正常解析JD，与简历数据进行匹配，生成匹配度报告。

**实际结果**：
报错"calculate_match() missing 1 required positional argument: 'resume_data'"，匹配评估失败。

**根因分析**：
job_search.py的cmd_rank函数错误地调用了match_engine.py的calculate_match函数，但该函数需要两个参数（jd_info字典和resume_data），而cmd_rank只传了一个jd_text参数。而且match_engine.py和rank.py是两套独立的实现，接口不兼容。

**修复方案**：
在cmd_rank函数中，改为调用rank.py的main函数（rank.py有自己完整的parse_jd和匹配逻辑），并临时修改sys.argv传递JD文件路径。

**验证结果**：
修复后重新运行`python job_search.py rank --jd tests/test_jd.txt`，匹配评估成功：
- 综合匹配度：75分
- 技术匹配：41分
- 经验匹配：100分
- 行为匹配：76分
- 硬约束：100分
- 投递建议：推荐投递
- 匹配度报告已生成

注意：测试JD的公司名和岗位名没有解析出来（格式不匹配），这是rank.py的解析规则问题，属于P2级别小问题，后续优化。

**备注**：
需要检查cmd_apply函数是否也有同样的问题（因为它调用了cmd_rank）。

---

## 问题记录模板

```
### BUG-XXX：[问题标题]

| 字段 | 内容 |
|------|------|
| 问题编号 | BUG-XXX |
| 发现时间 | YYYY-MM-DD |
| 问题级别 | P0/P1/P2/P3 |
| 问题模块 | 简历生成/匹配评估/岗位抓取/... |
| 发现阶段 | 阶段一/阶段二/阶段三/阶段四 |
| 状态 | 新建/已确认/修复中/已修复/已验证/已关闭 |
| 修复版本 | vX.X.X |

**问题描述**：
详细描述问题现象

**复现步骤**：
1. ...
2. ...
3. ...

**预期结果**：
应该是什么样的

**实际结果**：
实际是什么样的

**环境信息**：
- 操作系统：
- Python版本：
- 浏览器版本：

**附件**：
- 截图：
- 日志：
- 错误信息：

**修复方案**：
（修复后填写）

**验证结果**：
（验证后填写）

**备注**：
其他需要说明的信息
```

---

**文档版本**：v1.0
**创建时间**：2026-08-26
**最后更新**：2026-08-26
