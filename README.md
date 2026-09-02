# 求职助手 (Job Search Assistant)

一个覆盖求职全流程的本地工作区工具：简历生成 → 岗位采集 → 匹配评估 → 面试准备 → 申请归档 → 网申全流程。

## 功能特性

### 简历生成
- 4 套 HTML 简历模板（现代双栏 / 经典单栏 / 上下结构 / 活泼创意）
- JSON 数据源驱动，修改 `resume_data.json` 后一键生成
- 支持 HTML → PDF（浏览器打印）、按需生成 Word

### 四平台岗位采集
- Edge 浏览器扩展被动采集（BOSS直聘 / 智联 / 前程无忧 / 猎聘）
- 用户正常搜索翻页时自动累积岗位，一键导出 JSON
- 5 维度匹配评分（技术/经验/相关性/硬性条件/偏好）
- 统一主题 HTML 报告，支持筛选、JD 折叠、公司搜索

### 网申模块（campus 命令组）
- **信息底座**：`application_profile.json` 统一管理 13 类网申信息
- **网申雷达**：国聘网 + 牛客校招日程自动采集，合并报告
- **机筛检查**：15 维度质量检查（含国企关键词、身份证校验、附件材料）
- **OQ 生成**：8 类 28 题开放性问题个性化答案
- **进度看板**：8 状态机跟踪、截止提醒、状态时间线、HTML 看板
- **Edge 点填扩展**：网申页面侧边面板一键填充，只填不提交

### 其他
- 面试题库（通用 + 经历深挖）
- 申请归档与统计
- 简历格式自动检查
- 116 个单元测试

## 快速开始

### 1. 安装依赖
```bash
pip install pyyaml
```

### 2. 配置个人信息
编辑 `resume_data.json`，替换为你自己的简历信息（当前为示例数据"张三"）。

如需使用网申模块，创建 `application_profile.json`（参考 SOP-011）。

### 3. 生成简历
```bash
python generate_selected.py
```

### 4. 岗位采集
1. 在 Edge 中加载 `boss_api/boss_collector_extension/` 扩展
2. 正常在 BOSS/智联/51job/猎聘搜索岗位
3. 点击扩展面板"导出 JSON"
4. 生成报告：
```bash
python boss_api/make_standalone_report.py 采集文件.json -o 报告.html
```

### 5. 网申全流程
```bash
python job_search.py campus profile          # 查看信息底座
python job_search.py campus check            # 机筛质量检查
python job_search.py campus radar            # 网申雷达采集
python job_search.py campus oq gen           # 生成OQ答案
python job_search.py campus track add ...    # 添加进度记录
python job_search.py campus track report     # 进度看板报告
```

## 目录结构

```
├── job_search.py              # 统一工作流引擎（13命令）
├── resume_data.json           # 简历数据源（替换为你的信息）
├── config.yaml                # 统一配置
├── apply_check.py             # 网申机筛检查（15维度）
├── apply_track.py             # 网申进度看板
├── report_theme.py            # 统一报告主题
├── oq_generator.py            # OQ答案生成
├── radar_guopin.py            # 国聘网采集
├── radar_nowcoder.py          # 牛客校招采集
├── match_engine.py            # 5维度匹配引擎
├── check_resume.py            # 简历格式检查
├── boss_api/                  # 四平台采集扩展+解析器
├── fill_extension/            # Edge网申点填扩展
├── templates/                 # 简历模板
├── references/sop/            # 标准操作流程（11个SOP）
├── tests/                     # 单元测试（116个）
└── schemas/                   # JSON Schema
```

## 统一命令

```bash
python job_search.py <command>

setup      资料初始化
resume     简历生成
rank       职位匹配评估
apply      定制简历
interview  面试准备
outcome    申请归档
check      简历格式检查
jobs       岗位库管理
config     配置管理
validate   数据验证
quality    质量门禁
campus     网申模块（check/radar/oq/profile/track）
help       帮助
```

## 安全说明

- `application_profile.json`（含身份证/家人信息）和 `apply_tracking.json`（投递记录）已入 `.gitignore`，不会被提交
- 简历数据 `resume_data.json` 请替换为你自己的信息后再使用
- Edge 点填扩展只填不提交，所有提交动作必须人工完成
- 岗位采集扩展仅被动监听页面请求，不发送任何数据到第三方

## 许可证

MIT License
