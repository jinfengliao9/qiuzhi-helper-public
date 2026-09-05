---
name: job-search-assistant
description: "中文求职工作区助手，覆盖简历定制生成、个人资料结构化管理、职位匹配评估、面试准备、申请结果归档全流程。当用户提到秋招、春招、找工作、简历、求职信、面试准备、职位评估、求职规划、投递记录、Boss直聘/拉勾/智联/猎聘等招聘相关话题时触发；当用户上传简历、职位描述(JD)、求职材料，或要求优化简历、生成定制简历、准备面试时触发。"
---

# 求职工作区助手（Job Search Assistant）

## 概述

本 Skill 将求职过程管理为一个有状态、有反馈闭环的工作区，而非一次性的简历生成。核心流程：个人资料初始化（setup）→ 职位匹配评估（rank）→ 定制简历生成（apply）→ 面试准备（interview）→ 结果归档（outcome）→ 网申全流程（campus：信息底座/雷达找岗/机筛检查/OQ动态生成/半自动填表/进度看板），结果反哺资料，越用越精准。

**第一阶段已实现**：setup（资料初始化）+ apply（简历生成，4种HTML模板+Edge转PDF+Word按需生成）。
**第二阶段已实现**：rank（职位匹配评估）+ interview（面试准备）+ outcome（申请归档）+ check_resume（简历格式自动检查）。
**第三阶段已实现（v0.4.0 起四平台：Edge 扩展被动采集）**：在用户本人 Edge 浏览器安装原生扩展（MAIN world，hook 页面自身 fetch/XHR），支持 BOSS直聘/智联招聘/前程无忧三平台，用户正常搜索/翻页时被动累积岗位、一键导出 JSON，AI 侧解析、5维度匹配、出独立报告或入库。已打通 **BOSS直聘 + 智联招聘** 双平台：BOSS 列表明文薪资、可选慢速补全完整 JD；智联列表响应已内嵌完整 JD，无需补详情。旧的 Browser Use（CDP）自动化方案因触发风控/页面跳动/登录死路，**已归档，不再作为主路径**（详见流程六）。
**第四阶段已实现（v0.5.0 网申模块）**：campus 命令组统一入口，覆盖 ①信息底座（application_profile.json，13块中文key，含身份证/家人，敏感信息只存本地不入Git）②网申雷达【辅助参考】（国聘公开API+牛客校招日程，自动采集+合并HTML报告；主力推荐塔塔网申等专业聚合平台，数据量更大更新更及时）③机筛质量检查（apply_check.py，15维度，含国企机筛关键词/身份证校验/附件材料，统一主题HTML报告）④OQ开放性问题动态生成（AI动态生成+本地知识库记忆，任何问题都能基于信息底座生成个性化答案，越用越聪明，oq_kb.py知识库管理）⑤Edge轻量点填扩展（fill_extension，侧边面板一键填充，只填不提交）⑥进度看板（apply_track.py，8状态机/截止提醒/状态时间线/OQ存档/HTML看板）。统一报告主题 report_theme.py（四套报告统一视觉标准）。
**规范化整改已完成（阶段0-6）**：
- **统一工作流引擎**：`job_search.py` 主脚本，整合所有功能，提供13个统一命令（setup/resume/rank/apply/interview/outcome/check/jobs/config/validate/quality/campus/help），其中 campus 命令组含5个子命令（check/radar/oq/profile/track）
- **数据标准化**：4个JSON Schema（job/resume/match_result/application）+ 轻量级验证工具
- **配置外置**：`config.yaml` 统一配置文件（10个section）+ 配置加载工具
- **统一报告主题**：`report_theme.py` 唯一视觉标准（20+纯函数组件），四套报告（岗位采集/岗位库/网申雷达/机筛检查）全部统一主题；旧 templates/report_style.css 已废弃
- **推荐外部工具【重要】**：网申信息聚合优先使用专业平台——①塔塔网申（tatawangshen.com，累计108万+职位，每日实时更新，129家央企分类，内推码/投递榜/即将截止提醒，配套浏览器插件一键填网申）②校招鸭（xiaozhaoya.com，全网校招信息汇总，多维度筛选）③小罗盘校招网。本skill的网申雷达仅作为辅助参考，主力找岗位用上述专业平台，找到后把JD发给本skill做匹配评估+定制简历+OQ生成+面试准备
- **质量门禁**：`utils/quality_gate.py` 自动验证和错误处理（4类验证门禁）
- **SOP文档**：`references/sop/` 11个标准操作流程文档（含SOP-011网申模块SOP）
- **Git版本管理**：8次提交，完整的变更历史
**第二轮轻量产品化已完成（v0.6.0）**：
- **新增 prepare 一键命令**：`python job_search.py prepare --url <岗位URL>`，自动串联5个步骤（抓取JD→匹配评估→生成简历→生成OQ→生成面试题），支持 `--only`（只做指定步骤）和 `--skip`（跳过指定步骤）灵活选择，解决"每次都要临时写脚本"的核心痛点
- **新增 job_fetcher.py 岗位URL抓取模块**：支持从URL/JD文本/JD文件解析岗位信息，自动识别平台（国聘/智联/BOSS/51job/猎聘），提取15+字段（公司/岗位/薪资/地点/学历/经验/截止时间等），缓存到 applications/00_岗位缓存/ 供后续步骤复用
- **完善 resume 命令**：增加 `--company`（自动创建公司子文件夹）、`--output`（指定输出目录）、`--data`（指定简历数据文件）参数
- **完善 interview 命令**：增加 `--jd`（JD文本）、`--jd-file`（JD文件路径）参数，基于JD关键词增强专业技术题
- **新增 path_config.py 统一路径配置**：所有命令输出路径统一管理，8个分类目录（00_岗位缓存/01_岗位匹配报告/02_简历/03_面试题库/04_岗位采集报告/05_网申模块/99_归档），确保输出不混乱
- **统一输出路径**：resume输出到 applications/02_简历/{公司}_简历/，interview输出到 applications/03_面试题库/，prepare自动分类存放

**后续阶段规划**：完善文档（阶段7）、测试优化（阶段8）、多平台扩展（前程无忧/猎聘/实习僧，待用户注册账号）、薪资查询、多 agent 审核、求职信生成。

## 工作区目录结构

所有求职相关文件统一存放在用户工作目录下的 `job-search-workspace/` 文件夹中：

```
job-search-workspace/
├── job_search.py          ← 统一工作流引擎主脚本（12个命令，推荐使用）
├── config.yaml            ← 统一配置文件（10个section）
├── resume_data.json       ← 简历数据源（中文键名，用户直接修改）
├── jobs.json              ← 当前岗位库（已标准化，116个岗位）
├── PROJECT_NODE.md        ← 项目节点文档（全流程记录+变更日志）
├── FILE_MAP.md            ← 文件地图（唯一权威文件索引，找文件/删文件前先看这个）
├── REFACTOR_PLAN.md       ← 规范化整改计划（8阶段）
├── generate_selected.py   ← 一键生成4个模板HTML+PDF
├── rank.py                ← 职位匹配评估（单岗位评估）
├── interview.py           ← 面试准备
├── outcome.py             ← 申请归档
├── check_resume.py        ← 简历格式自动检查
├── apply_check.py         ← 【v0.5.0】网申机筛质量检查（15维度，含国企关键词/身份证校验）
├── apply_track.py         ← 【v0.5.0】网申进度看板（8状态机/截止提醒/时间线/OQ存档）
├── oq_answers/            ← OQ答案知识库（按公司分目录，AI动态生成的答案自动存档，支持搜索复用）
├── report_theme.py        ← 【v0.5.0】统一报告主题（唯一视觉标准，20+函数组件）
├── oq_generator.py        ← 【v0.5.0】OQ固定题库预生成（高频题基础，保留）
├── oq_kb.py               ← 【v0.5.1】OQ知识库管理器（list/search/show/add/export/stats，AI动态生成答案的本地记忆）
├── radar_guopin.py        ← 【v0.5.0】国聘网岗位采集（公开API，辅助参考）
├── radar_nowcoder.py      ← 【v0.5.0】牛客校招日程采集（辅助参考）
├── radar_merged_report.py ← 【v0.5.0】网申雷达合并报告生成
├── gen_fill_extension.py  ← 【v0.5.0】Edge点填扩展生成器
├── fill_extension/        ← 【v0.5.0】Edge轻量点填扩展（加载到Edge，只填不提交）
├── application_profile.json ← 【v0.5.0】网申信息底座（13块中文key，敏感信息不入Git）
├── match_engine.py        ← 优化版匹配引擎（5维度精细化评分）
├── report_generator.py    ← 统一报告生成器（标准化数据+统一样式）
├── job_pipeline.py        ← 岗位处理流水线（导入→匹配→报告）
├── jd_parser.py           ← JD详情解析（旧时代文件，活跃复用：详情文本拆分职责/要求）
├── job_fetcher.py         ← 【v0.6.0】岗位URL抓取模块（URL/JD文本解析，15+字段提取，缓存复用）
├── prepare_pipeline.py    ← 【v0.6.0】岗位一键处理流水线（5步骤串联，--only/--skip灵活选择）
├── path_config.py         ← 【v0.6.0】统一路径配置（8个分类目录，所有命令输出路径统一管理）
├── filter_jobs.py         ← 本地筛选模块（9维度筛选）
├── job_collector.py       ← 岗位库管理（旧时代文件，活跃复用：JobCollector DAL，被job_pipeline/filter_jobs依赖）
├── boss_api/               ← 【v0.2.0 主路径】Edge扩展被动采集 + 解析 + 独立报告
│   ├── boss_collector_extension/  ← Edge 原生 MV3 扩展（装到用户 Edge）
│   │   ├── manifest.json   ← 匹配 zhipin.com + zhaopin.com + 51job.com + liepin.com，MAIN world
│   │   └── content.js       ← 被动 hook fetch/XHR、去重累积、补全JD、导出JSON
│   ├── parse_joblist_api.py← BOSS 导出JSON → 标准岗位（明文薪资/补JD/公司主页）
│   ├── parse_zhaopin_api.py← 智联 导出JSON → 标准岗位（列表内嵌完整JD）
│   ├── parse_51job_api.py  ← 前程无忧 导出JSON → 标准岗位（列表直接返回完整JD，自动拆分职责/要求）
│   ├── parse_liepin_api.py  ← 猎聘 导出JSON → 标准岗位（列表无完整JD，含HR信息/刷新时间/公司规模）
│   ├── make_standalone_report.py ← 采集JSON → 匹配 → 独立HTML报告（支持多文件合并）
│   ├── boss岗位采集器.user.js    ← 油猴脚本（备选，本机MV3篡改猴注入不生效，保留）
│   ├── boss_bookmarklet_source.js / build_bookmarklet.py / install_bookmarklet.html ← 书签方案（备选）
│   └── README_采集器使用说明.md  ← 扩展安装与使用说明
├── schemas/               ← JSON Schema（数据标准化）
│   ├── job.json           ← 岗位数据Schema（32字段）
│   ├── resume.json        ← 简历数据Schema
│   ├── match_result.json  ← 匹配度结果Schema
│   └── application.json   ← 申请记录Schema
├── utils/                 ← 工具模块
│   ├── __init__.py
│   ├── config.py          ← 配置加载工具（带缓存/验证）
│   ├── validator.py       ← 轻量级数据验证工具（不依赖外部库）
│   ├── data_normalizer.py ← 数据标准化工具（清理/解析/去重）
│   └── quality_gate.py    ← 质量门禁模块（自动验证+错误处理）
├── templates/             ← 模板文件
│   └── report_style.css   ← 统一报告样式（颜色主题/统计栏/岗位卡片）
├── references/            ← 参考文档
│   └── sop/               ← 标准操作流程（SOP）
│       ├── README.md      ← SOP索引（10个SOP目录+快速命令）
│       ├── SOP-001_简历生成SOP.md
│       ├── SOP-002_职位匹配评估SOP.md
│       ├── SOP-006_岗位抓取SOP.md
│       ├── SOP-011_网申模块SOP.md
│       └── SOP-003至010_综合SOP.md
├── profile/               ← 个人资料（setup 阶段）
│   ├── candidate.md
│   └── preferences.md
├── cv/                    ← 生成的简历（HTML+PDF+Word）
│   ├── avatar.jpg
│   └── <姓名>_<岗位>_<模板>.html/pdf
├── applications/          ← 申请归档+岗位推荐报告
│   ├── applications.json  ← 投递记录表
│   ├── rank_<公司>_<岗位>.html  ← 单岗位匹配度报告
│   ├── 岗位推荐报告.html   ← 多平台联合岗位推荐报告
│   └── 投递统计报告.html
├── interview-prep/        ← 面试准备
│   ├── 测绘工程面试题库.md（71题）
│   ├── 经历深挖面试题库.md（41题）
│   └── interview_<公司>_<岗位>.html
└── archive/               ← 归档文件（临时脚本/数据）
    ├── scripts/           ← 30个临时脚本
    └── data/              ← 41个临时数据文件
```

首次使用时，如果工作区目录不存在，自动创建。

## 统一工作流引擎（推荐使用）

所有功能已整合到统一主脚本 `job_search.py`，提供12个命令，推荐使用统一入口而非单独脚本。

### 命令列表

| 命令 | 功能 | 说明 |
|------|------|------|
| `setup` | 初始化个人资料 | 生成candidate.md和preferences.md |
| `resume` | 生成简历 | 4套模板的HTML+PDF简历 |
| `rank` | 职位匹配评估 | 对JD进行匹配度评估 |
| `apply` | 生成定制简历 | 先匹配评估，再生成定制简历 |
| `interview` | 面试准备 | 定制自我介绍和面试问题 |
| `outcome` | 申请归档管理 | add/update/list/stats |
| `check` | 简历格式检查 | 8维度简历检查 |
| `jobs` | 岗位库管理 | list/report/filter（针对已入库 jobs.json） |
| `collect` | 扩展采集JSON→独立报告 | `collect <导出.json...> [-o 输出.html]`，多文件自动合并，**不写岗位库** |
| `config` | 配置管理 | show/validate/path |
| `validate` | 数据验证 | 验证简历、岗位库、申请记录 |
| `quality` | 质量门禁检查 | check/resume/jobs/report |
| `help` | 显示帮助 | 所有命令和使用方法 |

### 使用示例

```bash
# 生成简历
python job_search.py resume

# 职位匹配评估
python job_search.py rank --jd job_description.txt

# 面试准备
python job_search.py interview --company "公司名" --position "岗位名"

# 添加申请记录
python job_search.py outcome add --company "公司名" --position "岗位名"

# 生成岗位推荐报告（基于已入库岗位）
python job_search.py jobs report

# 扩展采集JSON出独立报告（不入库，可传多个文件自动合并）
python job_search.py collect 导出1.json 导出2.json -o applications/采集报告.html

# 显示配置
python job_search.py config show

# 数据验证
python job_search.py validate

# 质量门禁检查
python job_search.py quality check
```

### 质量门禁

执行关键操作前，建议先运行质量检查，确保数据质量：
```bash
python job_search.py quality check
```

质量门禁会检查：简历数据、岗位库、申请记录、配置文件。

### 标准操作流程（SOP）

详细的操作步骤请参考 `references/sop/` 目录下的SOP文档：
- SOP-001：简历生成SOP
- SOP-002：职位匹配评估SOP
- SOP-006：岗位抓取SOP（含反爬策略）
- SOP-003至010：综合SOP（定制简历/面试/归档/报告/验证/质量/配置）

## 流程一：个人资料初始化（setup）

### 触发场景
- 用户说"帮我初始化求职资料"、" setup 一下"、"帮我整理个人资料"
- 用户首次使用本 Skill，且没有 profile 文件
- 用户说"更新我的资料"、"新增一段实习经历"

### 执行步骤

1. **检查工作区状态**
   - 检查 `job-search-workspace/profile/candidate.md` 和 `preferences.md` 是否存在
   - 如果已存在，询问用户是"更新现有资料"还是"重新初始化"
   - 如果不存在，进入初始化流程

2. **收集候选人信息**
   - 参考 `references/candidate-profile-template.md` 的结构，引导用户提供信息
   - 信息收集可以分轮进行，不用一次问完
   - 用户提供的信息可以是大白话、零散的，由 AI 整理成结构化格式
   - 如果用户上传了现有简历/PDF/Word，直接提取信息，只向用户确认和补充缺失部分

3. **收集求职偏好**
   - 目标岗位、目标行业、目标城市
   - 薪资期望范围
   - 硬约束（比如"不接受加班"、"只考虑国企"、"不考虑外包"等，这些在职位评估时直接 veto）
   - 特别想去的公司类型或特别不想去的类型

4. **生成 profile 文件**
   - 将整理好的信息写入 `job-search-workspace/profile/candidate.md`
   - 将求职偏好写入 `job-search-workspace/profile/preferences.md`
   - 格式参考 `references/candidate-profile-template.md`
   - 生成后向用户展示，确认是否准确，有问题随时修改

5. **重要原则**
   - **绝不编造**：用户没说过的经历、技能、成果，绝对不能自行添加
   - **可以优化表述**：用户提供的零散事实，可以用更专业的语言重新组织，但事实本身不能改变
   - **量化优先**：如果用户提到了数字（处理了多少数据、效率提升多少、项目规模），保留并突出

## 流程二：定制简历生成（apply）

### 触发场景
- 用户说"帮我给这个岗位生成简历"、"帮我投这个公司"、"根据这个 JD 改简历"
- 用户提供了职位描述（JD）或职位链接，并要求生成/优化简历
- 用户说"帮我优化简历"且提供了目标岗位方向

### 前置检查
- 检查 `job-search-workspace/profile/candidate.md` 是否存在
- 如果不存在，先执行 setup 流程，或让用户提供基本信息
- 如果存在，读取候选人资料

### 执行步骤

#### 第 1 步：提取职位信息
- 如果用户提供了职位链接，尝试读取页面内容提取 JD
- 如果用户粘贴了 JD 文本，直接解析
- 提取关键字段：公司名称、岗位名称、工作地点、岗位要求（硬技能/软技能/经验）、岗位职责、薪资范围（如有）
- 将提取的职位信息临时保存，用于后续匹配和生成

#### 第 2 步：职位匹配评估（轻量版，完整 rank 在第二阶段）
- 参考 `references/job-evaluation-framework.md` 的评估维度
- 从四个维度快速评估匹配度：
  - **技术匹配**：岗位要求的技能/工具/语言，候选人有哪些直接匹配，哪些是相邻经验，哪些完全没有
  - **经验匹配**：岗位要求的工作年限、行业经验、项目经验，候选人是否满足
  - **行为匹配**：岗位描述中暗示的工作风格（比如"能承受压力"、"需要跨部门协作"），与候选人偏好是否冲突
  - **硬约束检查**：地点、薪资、行业等是否与 `preferences.md` 中的硬约束冲突，冲突则直接 veto
- 向用户输出匹配度评估报告，包括：
  - 匹配的亮点（哪些经历和技能正好对口）
  - 存在的 gap（岗位要求但候选人没有的）
  - 建议：是否建议投递，简历中应该重点突出什么
- **停下来询问用户**：是否继续生成简历？用户确认后再进入下一步

#### 第 3 步：生成简历内容
- 参考 `references/cv-generation-rules.md` 的生成规则
- 核心原则：
  - **一页优先**：应届毕业生或经验少于 5 年，简历控制在一页；经验丰富可放宽到两页
  - **岗位定制**：根据 JD 的关键词和要求，调整经历的描述顺序和侧重点，与岗位最相关的经历放最前面、写最详细
  - **STAR 法则**：每段经历用 Situation（背景）- Task（任务）- Action（行动）- Result（结果）结构描述
  - **量化成果**：尽可能用数字说话（处理了多少数据、覆盖多少用户、提升多少效率、节省多少时间）
  - **关键词匹配**：JD 中出现的核心技能词，如果候选人确实具备，在简历中自然地体现（不要生硬堆砌）
  - **绝不编造**：没有的经历、技能、成果绝对不能写
- 简历模块顺序（根据岗位和候选人情况灵活调整）：
  1. 个人信息（姓名、电话、邮箱、城市、求职意向）
  2. 教育背景（学校、专业、学历、时间、GPA/相关课程，如适用）
  3. 实习/工作经历（公司、岗位、时间、STAR 描述）
  4. 项目经历（项目名、角色、时间、背景、你的工作、成果）
  5. 技能清单（编程语言、软件工具、专业技能，按熟练程度排序）
  6. 其他（获奖、证书、论文等，如适用）

#### 第 4 步：自审与修订（reviewer 角色）
- 生成简历初稿后，切换到"招聘经理视角"进行自审：
  - 这份简历 30 秒内能抓住重点吗？
  - 有没有和岗位无关的内容占了篇幅？
  - 经历描述是不是只说了"做了什么"，没说"做成了什么"？
  - 有没有语法错误、错别字、时间线矛盾？
  - 关键词覆盖够不够？
  - 排版会不会有问题（内容太多导致溢出、太少导致空洞）？
- 根据自审结果修订简历，直到通过质量检查清单

#### 第 5 步：质量检查
- 参考 `references/quality-checklist.md` 逐项检查：
  - 页数是否符合要求
  - 个人信息是否完整（电话、邮箱可正常识别）
  - 时间线是否连贯无矛盾
  - 是否有错别字、语法错误
  - 经历描述是否遵循 STAR 法则
  - 是否有量化成果
  - 是否包含岗位关键词
  - 是否有编造内容（严格禁止）
- 检查不通过的项，返回修订

#### 第 6 步：渲染输出 HTML 简历
- 将最终简历内容整理成结构化 JSON 数据（字段说明见脚本头部注释）
- 确保头像图片 `avatar.jpg` 存在于 cv 目录下（首次使用时提醒用户提供证件照）
- 调用 `scripts/render_cv_html.py` 脚本，渲染生成现代风格 HTML 简历
- 输出路径：`job-search-workspace/cv/<公司>_<岗位>.html`
- 文件名中的公司和岗位名如果包含特殊字符，做安全处理
- 生成后向用户报告：
  - 简历保存路径
  - 匹配度评估摘要
  - 简历的核心亮点
  - 提醒用户用浏览器打开 HTML 文件，按 Ctrl+P 打印为 PDF（勾选"背景图形"选项以保留颜色和渐变）
  - 有需要调整的地方（颜色、布局、内容）随时说

### 重要原则
- **用户确认机制**：匹配评估后必须停下来等用户确认，不能直接生成简历
- **不自动投递**：本 Skill 只生成材料，不代替用户实际投递
- **隐私保护**：个人资料文件包含敏感信息，提醒用户妥善保管，不要公开分享工作区目录

## 流程三：职位匹配评估（rank）

### 触发场景
- 用户提供了职位描述（JD）或职位链接，要求评估匹配度
- 用户说"这个岗位我能投吗"、"帮我看看这个岗位匹配不匹配"
- 用户在投递前想了解自己的优势和差距

### 执行步骤

1. **获取 JD 文本**
   - 用户粘贴 JD 文本：直接使用
   - 用户提供职位链接：尝试读取页面内容提取 JD
   - 用户口头描述岗位：整理成结构化 JD

2. **调用 rank.py 脚本**
   ```bash
   python rank.py --text "JD文本内容"
   # 或从文件读取
   python rank.py job_description.txt
   ```
   - 脚本自动解析 JD：公司、岗位、城市、薪资、经验要求、学历要求、技能要求、岗位职责
   - 与用户简历数据从4个维度匹配评分：
     - **技术匹配**（35%权重）：JD要求的技能，用户有哪些匹配，哪些缺失
     - **经验匹配**（30%权重）：实习经历、项目经历、岗位经验要求
     - **行为匹配**（15%权重）：软技能、出差接受度、学习能力等
     - **硬约束**（20%权重）：学历、城市、经验年限等硬性条件
   - 输出综合匹配度评分（0-100分）和投递建议

3. **向用户展示匹配度报告**
   - 报告为 HTML 格式，保存在 `applications/rank_<公司>_<岗位>.html`
   - 包含：综合匹配度环形图、4维度评分条、已匹配/缺失技能标签、硬约束检查结果、JD信息解析
   - 用 `present_files` 展示报告给用户

4. **给出投递建议**
   - 80分以上：强烈推荐投递
   - 65-79分：推荐投递
   - 50-64分：可以尝试，需突出相关经历
   - 50分以下：不太建议，优先考虑更匹配的岗位
   - 提醒用户：匹配度仅供参考，实际投递请结合个人判断

### 注意事项
- rank.py 的 JD 解析基于规则匹配，格式不规范的 JD 可能解析不完整，此时由 AI 手动补充解析
- 技能匹配基于关键词，用户技能列表中的名称需与 JD 中的名称尽量一致
- 匹配度评分是辅助参考，不能代替用户的主观判断

## 流程四：面试准备（interview）

### 触发场景
- 用户收到面试通知，要求准备面试
- 用户说"帮我准备XX公司XX岗位的面试"
- 用户想了解某类岗位的常见面试问题

### 执行步骤

1. **收集面试信息**
   - 公司名称、岗位名称
   - 面试形式（电话/视频/现场）、面试轮次
   - 已知的面试方向（如有）

2. **调用 interview.py 脚本**
   ```bash
   python interview.py --company "公司名" --position "岗位名"
   ```
   - 脚本自动分析岗位类型（GIS工程师/地籍测绘/工程测量/遥感航测/通用测绘）
   - 生成定制版自我介绍（3分钟，结合用户简历和目标岗位）
   - 生成针对性面试问题（约25道），分5类：
     - **专业知识题**：根据岗位类型生成对应的专业问题
     - **软件操作题**：ArcGIS/CASS/ENVI/Python等
     - **仪器操作题**：RTK/全站仪/水准仪/无人机等
     - **项目经验题**：STAR法则相关问题
     - **行为面试题**：职业规划、团队协作、学习能力等
   - 提供反问环节建议和面试注意事项

3. **展示面试准备报告**
   - 报告为 HTML 格式，保存在 `interview-prep/interview_<公司>_<岗位>.html`
   - 同时参考 `interview-prep/测绘工程面试题库.md`（38道详细题+回答思路）
   - 用 `present_files` 展示报告给用户

4. **模拟面试（可选）**
   - 如果用户需要，可以进行模拟面试：AI扮演面试官，逐题提问，用户回答后AI给出点评和改进建议
   - 重点练习自我介绍、项目经历描述、专业知识问答

### 注意事项
- 面试问题库是通用的，实际面试问题因公司而异，建议用户结合公司背景和岗位JD进一步准备
- 面试准备报告生成后，建议用户提前演练自我介绍，确保3分钟内流畅说完
- 测绘行业面试看重踏实肯干和吃苦精神，行为面试中要突出这一点

## 流程五：申请结果归档（outcome）

### 触发场景
- 用户投递了新的公司/岗位，要求记录
- 用户收到笔试/面试/offer/拒绝通知，要求更新状态
- 用户想查看投递记录或统计分析

### 执行步骤

1. **添加投递记录**
   ```bash
   python outcome.py add --company "公司名" --position "岗位名" --city "城市" --source "渠道" --cv "使用的简历模板" --salary "薪资" --status "已投递"
   ```
   - 必填：公司名、岗位名
   - 选填：城市、投递渠道、使用的简历模板、薪资、JD链接、备注、投递日期、状态
   - 默认状态：已投递，默认日期：当天
   - 自动生成唯一编号 ID

2. **更新投递状态**
   ```bash
   python outcome.py update --id <编号> --status <新状态> --note "备注"
   ```
   - 状态可选：待投递/已投递/笔试中/面试中/已offer/已拒绝/无回应
   - 自动记录状态变更历史（日期、状态、备注）

3. **查看投递记录**
   ```bash
   python outcome.py list              # 查看全部记录
   python outcome.py list --status "面试中"  # 按状态筛选
   ```
   - 按投递日期倒序排列
   - 显示：ID、公司、岗位、城市、日期、状态

4. **统计分析**
   ```bash
   python outcome.py stats     # 命令行统计
   python outcome.py report    # 生成HTML统计报告
   ```
   - 统计内容：总投递数、各状态分布、进行中数量、offer数量、拒绝数量、无回应数量
   - 关键指标：面试转化率、offer率
   - 按投递渠道、使用简历版本分类统计
   - HTML报告保存在 `applications/投递统计报告.html`

5. **反馈闭环（重要）**
   - 当用户收到拒绝通知时，询问拒绝原因（如有），记录到备注中
   - 定期回顾投递数据，分析：
     - 哪些渠道回复率高 → 增加该渠道投递
     - 哪些简历模板面试转化率高 → 优先使用该模板
     - 哪些类型岗位匹配度高 → 聚焦该方向
   - 将分析结果反馈给用户，优化后续投递策略

### 注意事项
- 投递记录保存在 `applications/applications.json`，是纯文本JSON，用户可直接查看和编辑
- 状态更新要及时，确保统计数据准确
- 拒绝原因记录很重要，有助于后续优化简历和投递策略
- 定期（如每周）生成统计报告，回顾投递进展

## 流程六：岗位采集与推荐（Edge 扩展被动采集 · v0.2.0 起唯一主路径）

### 核心架构（务必先理解）

**不在 AI 侧用 Browser Use/CDP 自动操作浏览器，而是在用户本人 Edge 装一个原生解压扩展，由用户正常搜索/翻页，扩展被动镜像页面自身发出的列表/详情响应，累积去重后一键导出 JSON，再交给 AI 解析、匹配、出报告。**

- 扩展运行在页面 **MAIN world**，`document_start` 注入，hook 页面自身的 `fetch`/`XMLHttpRequest`，**只读取页面本来就会收到的响应，不主动发抓取请求、不自动翻页、不自动投递/打招呼**；
- 因此几乎不触发反自动化检测（对比：Browser Use 走 CDP，会被 BOSS 的 risk-detection 识别为 `navigator.webdriver` + `Runtime.Enable` 泄露，导致清空 token、反复跳验证页"页面跳动"，且无法在内置浏览器登录 BOSS——此路已证伪）；
- 筛选条件由用户在 Edge 页面上手动设置（方案A 抓取前筛选），AI 不代点；
- 采集状态**按标签页隔离**：BOSS 页和智联页各自计数、各自导出，需要合并时 AI 侧多文件合并。

### 触发场景
- 用户说"帮我找一下测绘工程师的岗位"、"抓一下 BOSS/智联 的岗位"、"我导出了岗位 JSON，帮我出报告"
- 用户在 Edge 用扩展采集后，把下载的 JSON 发给 AI，要求匹配评估/出独立报告/并入岗位库

### 支持的平台

| 平台 | 状态 | 列表是否带完整JD | 关键特性 |
|------|------|------------------|----------|
| BOSS直聘 | ✅ 已完成（扩展） | 否，需点"补全JD"慢速取详情 | 明文薪资 salaryDesc（绕过字体反爬）；详情 `/wapi/zpgeek/job/detail.json?securityId=`，6-11秒/个拟人间隔，可停止；公司主页 `zhipin.com/gongsi/{brandId}.html` |
| 智联招聘 | ✅ 已完成（扩展） | **是，列表内嵌完整JD** | 完整JD在 `jobDetailData.position.desc.description`（100%覆盖），无需补详情；岗位 `jobs.zhaopin.com/{number}.htm`，公司 `company.zhaopin.com/{companyNumber}.htm`（校招为 xiaoyuan.zhaopin.com/company/） |
| 前程无忧/51job | ✅ 已完成(v0.3.0) | 列表直接返回完整JD | 扩展v1.3.0+parse_51job_api.py，标签/福利/经纬度提取，自动拆分职责/要求 |
| 猎聘 | ✅ 已完成(v0.4.0) | 列表无JD，需补全 | 扩展v1.4.0+parse_liepin_api.py，SSR详情页schema.org提取JD，「补全猎聘JD」按钮，HR信息/刷新时间 |
| 实习僧 | 📋 待启动 | - | 待用户注册账号 |

### 执行步骤

#### 第 1 步：确认平台、关键词、筛选条件
- 问清平台（BOSS/智联）、关键词（"测绘/测量/GIS/遥感"，注意"测量"较宽泛）、城市/薪资/学历/经验等筛选；
- 指导用户在 **Edge** 打开对应平台搜索页，**由用户本人设置好筛选条件**（方案A）。

#### 第 2 步：用户在 Edge 采集（扩展被动累积）
- 确认扩展已加载（edge://extensions，文件夹 `boss_api/boss_collector_extension/`，MAIN world）；首次使用按 `boss_api/README_采集器使用说明.md` 指导"加载解压缩的扩展"；
- 用户搜索、滚动/翻页，右上角"🎯 双平台采集"面板实时显示 `BOSS n（JD x）` / `智联 n`，自动按岗位ID去重累积；
- **BOSS 补全JD（可选但推荐）**：列表抓完后点橙色"补全BOSS的JD"，扩展用页面自身 fetch 按 6-11 秒随机间隔、每10个额外休息15-25秒逐个取详情，可随时"停止补全"，已补的不重复；让该标签保持前台（后台会降速）；
- **智联无需补JD**：列表已内嵌完整描述。

#### 第 3 步：用户导出 JSON 发给 AI
- 点"导出JSON"，下载形如 `岗位采集_BOSSxx_智联xx_时间.json`（双平台信封：`zpData.jobList`=BOSS、`zhaopin_jobs`=智联）；
- 用户把文件（本地路径）发给 AI。

#### 第 4 步：AI 解析为标准岗位（不联网、只做数据映射）
- BOSS：`boss_api/parse_joblist_api.py`（或在脚本中 import `extract_jobs/dedupe`），提取明文薪资、技能、`__detail.jobInfo.postDescription` 清洗并拆分职责/要求、合并 showSkills、公司主页链接；
- 智联：`boss_api/parse_zhaopin_api.py` 的 `parse_zhaopin()`，按真实字段（name/salary60/workCity/jobDetailData.position.desc.description 等）映射；
- 解析后核对覆盖率（岗位名/公司/薪资/城市/JD/链接应接近100%）。

#### 第 5 步：匹配评估 + 出报告（两条路径，先问用户）
- **独立报告（默认，测试/不入库，优先走统一引擎）**：
  ```bash
  python job_search.py collect <导出1.json> [导出2.json ...] -o applications/xxx.html
  ```
  支持一次传多个 JSON（BOSS、智联分平台导出后自动跨文件合并去重），按 `resume_data.json` 5维度评分，输出独立 HTML，**不写 jobs.json**；相对路径会自动回退到工作区根目录、兼容带 BOM 的导出文件。（等价底层脚本 `boss_api/make_standalone_report.py`，向后保留）
- **并入岗位库（正式积累）**：解析为标准岗位后走 `job_pipeline.py import → rank → report`（分步，不要用 `all`，会超时），写入 `jobs.json` 并出正式推荐报告；
- 报告卡片：查看岗位→岗位详情页、搜索公司→**公司主页**（report_generator 优先用岗位自带 company_link，缺失才站内搜索兜底）；带来源标签（蓝=智联、橙=BOSS）。

#### 第 6 步：用户人工决策投递
- AI **绝不自动投递/打招呼**；用户看报告与完整JD后，自行到对应平台手动操作，保证一个公司一次机会的慎重。

### 多关键词搜索
- 用户可在 Edge 分别搜"测绘""测量""GIS"等，每次翻页累积（同一标签会持续去重），或分多次导出，AI 侧合并；
- "测量"等宽泛词会混入药理测量/心理测量/测试岗，匹配引擎会用低分过滤，但建议优先精准词。

### 四平台采集流程速查

| 平台 | 搜索URL关键词 | 列表有JD？ | 补全JD方式 | 导出字段 |
|---|---|---|---|---|
| BOSS直聘 | `query=测绘` | ❌ 无 | 点「补全BOSS的JD」按钮（fetch详情API） | zpData.jobList（含__detail） |
| 智联招聘 | `kw=测绘` | ✅ 内嵌 | 不需要 | zhaopin_jobs（含完整JD） |
| 前程无忧 | `keyword=测绘` | ✅ 直接返回 | 不需要 | job51_jobs（含完整JD+经纬度） |
| 猎聘 | `key=测绘` | ❌ 无 | 点「补全猎聘JD」按钮（fetch详情页HTML，提取schema.org） | liepin_jobs（含__detail.description） |

**采集流程**：搜索岗位 → 翻页滚动（扩展被动累积） → 如需JD补全点对应按钮 → 点「导出JSON」 → 发给助手出报告。

**多平台混合**：多个平台的JSON可一次传入 `make_standalone_report.py`，自动跨平台去重合并。

### 扩展采集风控与注意事项
- **不主动发抓取请求**：列表/智联/51job JD完全被动；主动请求仅 BOSS"补全JD"和猎聘"补全JD"，均用拟人间隔(6-11秒/个)+可停止+用户在线时进行，若弹验证页立即停止、当天不再补；
- **不自动投递/打招呼**，只读取；
- 扩展代码改过后需在 edge://extensions 点"重新加载"，并 F5 刷新目标页面；
- 采集状态按标签页隔离，跨平台请分标签导出、报告侧合并；
- 本机结论：优先 Edge 原生解压扩展（MAIN world）；MV3 版篡改猴在本机 userscript 注入不生效，油猴/书签仅作备选保留。

### 已归档/已证伪的方案（不要再走回老路）
- **Browser Use / CDP 自动化抓取（旧主路径，已归档）**：CDP 特征（navigator.webdriver、Runtime.Enable）被 BOSS 检测，清空 bst token、反复跳 verify.html"页面跳动"，且无法在内置浏览器登录 BOSS；相关旧脚本（job_collector.py、multi_keyword_search.py、scraper_config.py、jd_parser.py 等）保留但不再作为采集主路径，仅复用其匹配/筛选/入库能力。
- **方案A全自动爬虫**：违规风险高，放弃。
- **方案B 直接调内部API（脱离真实浏览器）**：签名/TLS指纹门槛高、登录态难维持，放弃；被动镜像方案等价地拿到了内部API明文数据，且无需逆向。
- **方案D纯半自动复制JD**：效率提升有限，被扩展方案取代。
- **BOSS卡片视图直接提薪资**：自定义字体乱码，现由列表接口 salaryDesc 明文获得，已解决。
- **PowerShell ConvertFrom-Json 解析 UTF-8 中文**：乱码，JSON 一律用 Python 解析。

## 参考资源索引

| 文件 | 用途 | 何时读取 |
|---|---|---|
| `references/candidate-profile-template.md` | 候选人资料模板 | setup 阶段生成 profile 时 |
| `references/cv-generation-rules.md` | 简历生成规则 | apply 阶段生成简历内容时 |
| `references/quality-checklist.md` | 简历质量检查清单 | apply 阶段自审和最终检查时 |
| `references/job-evaluation-framework.md` | 职位匹配评估框架 | apply 阶段匹配评估时（轻量版） |
| `references/writing-style-guide.md` | 写作风格指南 | 生成简历和求职信表述时 |

## 脚本索引

### 统一工作流引擎（推荐使用）

| 脚本 | 用途 |
|---|---|
| `job_search.py` | 统一工作流引擎主脚本（整合所有功能，12个命令，推荐使用） |

### 工具模块（utils/）

| 模块 | 用途 |
|---|---|
| `utils/config.py` | 配置加载工具（带缓存/验证/便捷访问函数） |
| `utils/validator.py` | 轻量级数据验证工具（不依赖外部库，支持类型/枚举/格式/范围验证） |
| `utils/data_normalizer.py` | 数据标准化工具（清理文本/解析薪资/分离技能福利/生成ID/去重） |
| `utils/quality_gate.py` | 质量门禁模块（自动验证+错误处理，4类验证门禁） |

### Skill 内置脚本（scripts/）

| 脚本 | 用途 |
|---|---|
| `scripts/render_cv_html.py` | 多模板 HTML 简历渲染（modern/classic/minimal/geek/creative 5种风格） |
| `scripts/render_cv_word.py` | Word 简历渲染（双栏+头像+深蓝金配色） |
| `scripts/render_cv_latex.py` | LaTeX 简历渲染（已放弃，保留备用） |

### 工作区脚本（job-search-workspace/）

| 脚本 | 用途 |
|---|---|
| `generate_selected.py` | 一键生成4个选中模板的 HTML+PDF（改动 JSON 后运行） |
| `rank.py` | 单岗位职位匹配评估（输入JD，输出4维度匹配评分和投递建议） |
| `interview.py` | 面试准备（输入公司和岗位，输出定制自我介绍+针对性面试问题） |
| `outcome.py` | 申请归档（添加投递记录、更新状态、查看列表、统计分析） |
| `check_resume.py` | 简历格式自动检查（8维度检查+JD关键词覆盖+页数估算，生成检查报告） |
| `job_pipeline.py` | 岗位处理流水线（import导入→rank匹配→report报告，分步运行） |
| `deploy_skill.py` | 部署同步脚本（把工作区SKILL.md同步到已安装skill目录，修改SKILL.md后必须运行） |
| `jd_parser.py` | JD详情解析（旧时代文件，活跃复用：parse_job_detail/extract_basic_info，被job_pipeline import依赖） |
| `match_engine.py` | 优化版匹配引擎（5维度精细化评分，技术/经验/行为/硬约束/偏好） |
| `filter_jobs.py` | 本地筛选模块（9维度筛选+交互式筛选+筛选报告生成） |
| `job_collector.py` | 岗位库管理（旧时代文件，活跃复用：JobCollector类是jobs.json数据访问层，被job_pipeline/filter_jobs依赖） |
| `archive/browser_use_legacy/` | 已归档Browser Use时代脚本：multi_keyword_search.py、scraper_config.py（v0.2.0起不再使用，详见该目录README） |

### Edge 扩展被动采集（boss_api/，v0.2.0 主路径）

| 脚本/文件 | 用途 |
|---|---|
| `boss_api/boss_collector_extension/` | Edge 原生 MV3 扩展（manifest+content.js），装到用户 Edge，被动采集 BOSS+智联 |
| `boss_api/parse_joblist_api.py` | BOSS 导出JSON→标准岗位（明文薪资、补全JD清洗拆分、gongsi公司主页） |
| `boss_api/parse_zhaopin_api.py` | 智联 导出JSON→标准岗位（列表内嵌完整JD，容错多字段路径） |
| `boss_api/parse_51job_api.py` | 前程无忧 导出JSON→标准岗位（列表直接返回完整JD，自动拆分职责/要求，标签/福利/经纬度提取） |
| `boss_api/parse_liepin_api.py` | 猎聘 导出JSON→标准岗位（列表无完整JD，含HR信息/刷新时间/公司规模/行业，从liepin_raw提取pc-search-job响应） |
| `boss_api/make_standalone_report.py` | 采集JSON→匹配→独立HTML报告，支持多文件跨平台合并，不写岗位库 |
| `boss_api/boss岗位采集器.user.js` | 油猴脚本（备选，本机MV3篡改猴注入不生效） |
| `boss_api/*bookmarklet*`、`install_bookmarklet.html` | 书签方案（备选，免安装） |
| `boss_api/README_采集器使用说明.md` | 扩展安装、使用、风控说明 |

## 资产索引

| 文件 | 用途 |
|---|---|
| `assets/cv-template.docx` | Word 简历模板（双栏+头像+深蓝金配色） |
| `config.yaml` | 统一配置文件（10个section：general/paths/scraper/platforms/matching/report/resume/interview/validation/version） |
| `templates/report_style.css` | 统一报告样式文件（颜色主题/统计栏/岗位卡片/维度评分/技能标签/操作按钮/响应式设计） |
| `schemas/job.json` | 岗位数据JSON Schema（32字段） |
| `schemas/resume.json` | 简历数据JSON Schema（中文键名） |
| `schemas/match_result.json` | 匹配度结果JSON Schema（4维度评分） |
| `schemas/application.json` | 申请记录JSON Schema |
| `references/sop/` | 标准操作流程文档目录（10个SOP） |
| `interview-prep/测绘工程面试题库.md` | 测绘工程专业面试题库（71道题+回答思路） |
| `interview-prep/经历深挖面试题库.md` | 经历深挖面试题库（41道针对具体经历的定制题+回答技巧） |

## 后续阶段规划

- **已完成**：第一阶段（setup+apply）、第二阶段（rank+interview+outcome+check_resume）、规范化整改阶段0-8、第三阶段岗位采集——v0.2.0 起以 **Edge 扩展被动采集**为唯一主路径，已打通 BOSS直聘（明文薪资+慢速补全JD）+ 智联招聘（列表内嵌完整JD），含5维度匹配、多关键词、方案A抓取前筛选、跨平台合并去重、独立报告/入库两条路径、公司主页直链
- **规范化整改已完成（阶段0-8）**：Git版本管理、数据标准化（4个JSON Schema）、配置外置（config.yaml）、统一报告模板（report_style.css）、工作流引擎（job_search.py，13个命令）、质量门禁（quality_gate.py）、SOP文档、65个自动化测试
- **轻量产品化已完成（5步全做完）**：①git版本管理基线 ②SKILL/SOP主路径切换为Edge扩展被动采集 ③解析器自动化测试（32个新测试，全量65个） ④统一引擎新增collect命令整合独立报告 ⑤归档Browser Use旧代码（multi_keyword_search/scraper_config移至archive/browser_use_legacy/，job_collector/jd_parser因活跃复用保留）
- **待启动（下一个平台）**：实习僧等（优先级低）；新平台只需在扩展manifest加匹配+写对应 parse_xxx 解析器，架构已支持动态扩展
- **待启动（优先级中）**：薪资查询（接入看准网/职友集等中国薪资数据源）、求职信生成（根据公司和岗位生成定制求职信）
- **待启动（优先级低）**：多 agent reviewer（派专门的审核子 agent 从HR/技术面试官/招聘经理视角审查简历）
- **持续优化**：匹配度精细化（提升区分度）、面试题库扩充、简历模板扩充、报告体验优化
- **已归档（不再使用）**：Browser Use/CDP 自动化抓取（触发风控、页面跳动、无法登录BOSS）
