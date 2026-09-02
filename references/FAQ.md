# 求职工作区助手 - 常见问题（FAQ）

## 目录

1. [简历生成相关](#简历生成相关)
2. [职位匹配相关](#职位匹配相关)
3. [岗位抓取相关](#岗位抓取相关)
4. [配置和数据相关](#配置和数据相关)
5. [工作流引擎相关](#工作流引擎相关)
6. [质量门禁相关](#质量门禁相关)
7. [常见错误和解决方案](#常见错误和解决方案)

---

## 简历生成相关

### Q1：如何生成简历？

**A**：修改 `resume_data.json` 中的内容后，运行：
```bash
python job_search.py resume
```
脚本会自动生成4套模板的HTML+PDF简历，保存在 `cv/` 目录下。

### Q2：如何修改简历内容？

**A**：直接编辑 `resume_data.json` 文件，修改后重新运行 `python job_search.py resume` 即可。简历数据源使用中文键名，便于直接修改。

### Q3：简历生成后只有HTML，没有PDF怎么办？

**A**：PDF转换需要Edge浏览器。如自动转换失败，可手动用Edge打开HTML文件，按Ctrl+P，勾选"背景图形"，保存为PDF。

### Q4：如何添加头像？

**A**：将头像图片命名为 `avatar.jpg`，放在 `cv/` 目录下。生成简历时会自动引用头像。

### Q5：简历内容太多，溢出到第二页怎么办？

**A**：精简简历内容，或调整 `resume_data.json` 中的描述长度。应届毕业生建议控制在一页。

### Q6：可以只生成某一套模板吗？

**A**：当前 `job_search.py resume` 会生成全部4套模板。如需只生成某一套，可直接调用对应的渲染脚本，或修改 `generate_selected.py` 中的模板列表。

### Q7：Word版本的简历如何生成？

**A**：Word版本按需生成。如需Word版本，使用专门的Word渲染脚本：
```bash
python -c "import sys; sys.path.insert(0, '.'); from render_cv_word import render_cv_word; render_cv_word('resume_data.json', 'cv/简历.docx')"
```

---

## 职位匹配相关

### Q8：如何评估某个岗位的匹配度？

**A**：将JD保存为文本文件，运行：
```bash
python job_search.py rank --jd job_description.txt
```
或直接传入JD文本：
```bash
python job_search.py rank --text "JD文本内容"
```

### Q9：匹配度评分是如何计算的？

**A**：从4个维度匹配评分：
- **技术匹配**（35%权重）：JD要求的技能，用户有哪些匹配，哪些缺失
- **经验匹配**（30%权重）：实习经历、项目经历、岗位经验要求
- **行为匹配**（15%权重）：软技能、出差接受度、学习能力等
- **硬约束**（20%权重）：学历、城市、经验年限等硬性条件

### Q10：匹配度多少分建议投递？

**A**：
- 80分以上：强烈推荐投递
- 65-79分：推荐投递
- 50-64分：可以尝试，需突出相关经历
- 50分以下：不太建议，优先考虑更匹配的岗位

匹配度仅供参考，实际投递请结合个人判断。

### Q11：如何提高匹配度？

**A**：
1. 在简历中突出与JD相关的经历和技能
2. 使用JD中的关键词描述自己的经历
3. 补充JD要求但自己具备的技能
4. 针对岗位定制简历内容

---

## 岗位抓取相关

### Q12：如何抓取招聘平台的岗位？

**A**：v0.2.0 起使用 **Edge 扩展被动采集**（主路径）：在你本人 Edge 装一个原生解压扩展，你正常搜索/翻页时扩展被动累积岗位、导出 JSON，AI 解析匹配出报告。旧的 Browser Use/CDP 自动化已归档（触发风控、页面跳动、无法登录BOSS）。详见 `references/sop/SOP-006_岗位抓取SOP.md`。

基本流程：
1. 在你本人 Edge 加载扩展并登录目标平台
2. 你手动设置关键词和筛选条件、搜索翻页，扩展被动累积
3. BOSS 可点"补全JD"慢速取详情；智联列表自带完整JD
4. 点"导出JSON"发给 AI
5. AI 解析匹配，出独立报告（不入库）或并入岗位库

### Q13：支持哪些招聘平台？

**A**：当前已用 Edge 扩展被动采集打通：
- BOSS直聘（明文薪资，可选慢速补全完整JD）
- 智联招聘（列表响应已内嵌完整JD，无需补详情）

待支持：前程无忧/51job（反爬弱，优先做）、猎聘（需注册、反爬较强）、实习僧。

### Q14：抓取会被封号吗？如何控制风险？

**A**：扩展方案本身几乎不触发风控（只被动镜像页面正常收到的响应，不主动抓取）：
- 列表/智联JD：纯被动，正常翻页即可
- BOSS补全JD：6-11秒随机间隔、每10个长休息、可随时停止、标签保持前台、用户在线时进行
- 一旦弹验证页立即停止、当天不再操作；不自动投递/打招呼
- 旧 Browser Use/CDP 因暴露自动化特征已弃用

详细策略请参考 `references/sop/SOP-006_岗位抓取SOP.md`。

### Q15：可以自动投递简历吗？

**A**：不可以，也不建议。本Skill只生成材料和抓取岗位信息，不代替用户实际投递。投递和打招呼由用户手动操作，因为：
1. 投递简历可能一个公司只有一次机会，必须慎重
2. 全部自动打招呼可能回复不过来
3. 自动投递可能触发平台风控

### Q16：抓取的岗位信息保存在哪里？

**A**：两种去向：①独立报告（测试用，不写库，由 `boss_api/make_standalone_report.py` 生成 HTML）；②正式并入 `jobs.json` 岗位库（标准化JSON，走 job_pipeline import→rank→report）。

### Q17：如何查看岗位推荐报告？

**A**：运行：
```bash
python job_search.py jobs report
```
报告会生成在 `applications/岗位推荐报告.html`，用浏览器打开即可查看。

---

## 配置和数据相关

### Q18：如何修改配置？

**A**：直接编辑 `config.yaml` 文件。配置文件包含10个section：
- general：通用配置
- paths：路径配置
- scraper：抓取配置（反爬策略）
- platforms：平台配置（智联、BOSS直聘）
- matching：匹配配置（权重、阈值）
- report：报告配置
- resume：简历配置（启用的模板）
- interview：面试配置
- validation：验证配置
- version：版本信息

修改后运行 `python job_search.py config validate` 验证配置是否正确。

### Q19：如何查看当前配置？

**A**：运行：
```bash
python job_search.py config show
```
会显示配置摘要，包括已启用平台、匹配权重、已启用简历模板等。

### Q20：数据验证是做什么的？

**A**：数据验证确保数据格式和业务逻辑正确，防止问题传递到下一步。运行：
```bash
python job_search.py validate
```
会验证：简历数据、岗位库、申请记录。

### Q21：JSON Schema是做什么的？

**A**：JSON Schema定义了数据的标准格式，包括字段名、类型、是否必填、枚举值等。当前有4个Schema：
- `schemas/job.json`：岗位数据Schema（32字段）
- `schemas/resume.json`：简历数据Schema
- `schemas/match_result.json`：匹配度结果Schema
- `schemas/application.json`：申请记录Schema

数据验证工具会根据Schema检查数据是否符合标准。

---

## 工作流引擎相关

### Q22：什么是统一工作流引擎？

**A**：统一工作流引擎是 `job_search.py` 主脚本，整合了所有功能，提供12个统一命令。推荐使用统一入口而非单独脚本，确保操作一致性。

### Q23：工作流引擎有哪些命令？

**A**：12个命令：
1. `setup`：初始化个人资料
2. `resume`：生成简历
3. `rank`：职位匹配评估
4. `apply`：生成定制简历
5. `interview`：面试准备
6. `outcome`：申请归档管理
7. `check`：简历格式检查
8. `jobs`：岗位库管理
9. `config`：配置管理
10. `validate`：数据验证
11. `quality`：质量门禁检查
12. `help`：显示帮助

### Q24：如何查看命令的帮助信息？

**A**：运行：
```bash
python job_search.py --help          # 查看所有命令
python job_search.py rank --help     # 查看某个命令的帮助
```

---

## 质量门禁相关

### Q25：什么是质量门禁？

**A**：质量门禁是自动验证和错误处理机制，确保每个步骤完成后自动检查，问题不传递到下一步。运行：
```bash
python job_search.py quality check
```
会检查4个模块：简历数据、岗位库、申请记录、配置文件。

### Q26：质量门禁检查哪些内容？

**A**：
1. **简历数据验证**：Schema验证 + 业务逻辑验证 + 内容完整性检查
2. **岗位数据验证**：Schema验证 + 批量验证 + 重复检测 + 链接有效性
3. **报告验证**：HTML结构验证 + 链接有效性检查 + 内容完整性检查
4. **配置验证**：必要section检查 + 匹配权重总和验证 + 平台配置完整性检查

### Q27：质量检查发现问题怎么办？

**A**：根据检查结果修复问题：
- 数据问题 → 修复数据
- 配置问题 → 修复配置
- 报告问题 → 重新生成报告

修复后重新运行 `python job_search.py quality check`，确保所有问题已解决。

---

## 常见错误和解决方案

### Q28：运行脚本提示"ModuleNotFoundError: No module named 'xxx'"

**A**：缺少依赖模块。安装所需模块：
```bash
pip install xxx
```
常见依赖：PyYAML（配置文件）、python-docx（Word生成）。

### Q29：运行脚本提示"FileNotFoundError: [Errno 2] No such file or directory"

**A**：缺少必要的文件。检查：
- `resume_data.json` 是否存在
- `config.yaml` 是否存在
- `cv/avatar.jpg` 是否存在（如需要头像）
- 工作区目录是否正确

### Q30：PDF转换失败，提示找不到Edge浏览器

**A**：确保Edge浏览器已安装，并将Edge添加到系统PATH。或手动用Edge打开HTML文件，按Ctrl+P保存为PDF。

### Q31：岗位抓取时遇到验证码

**A**：立即停止抓取，请求用户接管浏览器完成验证。用户完成验证后，重新观察页面状态，继续抓取。

### Q32：岗位抓取时页面加载超时

**A**：
1. 刷新页面
2. 等待更长时间
3. 如多次失败，停止抓取，检查网络连接
4. 记录失败的岗位，后续补充

### Q33：BOSS直聘薪资显示乱码

**A**：BOSS直聘使用特殊字体防爬，薪资可能显示乱码。解决方法：
1. 访问岗位详情页，从详情页提取薪资
2. 如详情页也乱码，记录为"薪资面议"
3. 不要尝试破解字体，避免触发风控

### Q34：报告中的公司链接无法访问

**A**：公司详情页需要公司ID，无法直接生成。已修复为使用搜索链接：
- 智联招聘：`https://sou.zhaopin.com/?jl=765&kw={公司名}`
- BOSS直聘：`https://www.zhipin.com/web/geek/jobs?query={公司名}`

如仍有问题，运行 `python job_search.py quality report` 检查报告质量。

### Q35：如何查看Git提交历史？

**A**：在工作区目录运行：
```bash
git log --oneline
```
当前有8次提交，完整记录了规范化整改的过程。

### Q36：如何回滚到之前的版本？

**A**：使用Git回滚：
```bash
git log --oneline          # 查看提交历史
git reset --hard <commit_id>  # 回滚到指定提交
```
注意：回滚会丢失当前修改，请谨慎操作。

---

## 更多资源

- **项目节点文档**：`PROJECT_NODE.md`（全流程记录+变更日志）
- **整改计划**：`REFACTOR_PLAN.md`（8阶段规范化整改计划）
- **SOP文档**：`references/sop/`（10个标准操作流程）
- **面试题库**：`interview-prep/`（测绘工程71题+经历深挖41题）
- **参考文档**：`references/`（候选人资料模板、简历生成规则、质量检查清单等）
