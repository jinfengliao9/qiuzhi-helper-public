# SOP-011 网申模块标准操作流程

> 适用版本：v0.5.0（网申模块） | 最后更新：2026-09-02
> 前置条件：已完成简历生成（SOP-001）、岗位匹配（SOP-002）

## 一、模块概述

网申模块覆盖国企/大厂校招网申全流程：**信息底座 → 雷达找岗位 → 机筛检查 → OQ生成 → 半自动填表 → 进度跟踪**。所有功能通过 `python job_search.py campus` 统一入口调用。

## 二、信息底座维护（阶段0）

### 2.1 信息底座文件
- 路径：`job-search-workspace/application_profile.json`
- 13个顶级块：基本信息/教育背景/实习经历/项目经历/专业技能/技能证书/获奖经历/培训经历/家庭成员/紧急联系人/自我评价/兴趣特长/附件材料
- **敏感信息只存本地，已入 .gitignore，不进 GitHub**

### 2.2 维护方式
直接用文本编辑器修改 JSON 文件，或告知 AI 需要修改的内容，由 AI 用 Python 脚本更新。

### 2.3 查看摘要
```bash
python job_search.py campus profile
```

## 三、网申雷达（阶段2）

### 3.1 功能
自动从国聘网（公开API）+ 牛客校招日程采集网申信息，生成合并HTML报告。

### 3.2 命令
```bash
# 默认关键词"测绘"，2页
python job_search.py campus radar

# 自定义关键词和页数
python job_search.py campus radar --keyword "测绘" --pages 3
```

### 3.3 输出
- 国聘岗位JSON：`radar/guopin_关键词_N条_时间.json`
- 牛客公司JSON：`radar/nowcoder_N家_时间.json`
- 合并HTML报告：`radar/网申雷达综合报告_N岗位_N公司_时间.html`

### 3.4 数据源说明
- **国聘网**：国企主战场，走 gp-api JSON 接口，POST 请求，body 仅 `{page, page_size, keyword}`
- **牛客**：校招日程聚合，GET 请求，50家/页，含网申起止时间和官方入口
- **应届生网**：暂挂起（搜索页SPA+JS挑战反爬，需Browser Use攻克）

## 四、机筛质量检查（阶段3）

### 4.1 功能
15个维度检查网申信息完整度和质量，含国企机筛关键词核查、身份证校验、附件材料检查等。

### 4.2 命令
```bash
# 基础检查
python job_search.py campus check

# 含目标岗位ATS关键词覆盖检查
python job_search.py campus check --jd job_desc.txt

# 指定输出路径
python job_search.py campus check -o applications/我的检查报告.html
```

### 4.3 检查维度（15个）
1. 个人信息 2. 教育背景 3. 实习经历 4. 项目经历 5. 技能清单
6. 时间线 7. 错别字表述 8. 量化成果 9. 身份证校验 10. 联系方式
11. 国企机筛关键词 12. 家庭成员 13. 紧急联系人 14. 附件材料 15. 网申特有字段

### 4.4 输出
HTML报告：`applications/张三_网申机筛检查报告.html`，分"必须修改/建议优化/已达标"三类。

## 五、OQ开放性问题生成（阶段1）

### 5.1 功能
针对国企网申常见开放性问题，基于信息底座生成个性化答案。

### 5.2 命令
```bash
# 列出支持的OQ问题（8类28题）
python job_search.py campus oq list

# 生成全部OQ答案
python job_search.py campus oq gen
```

### 5.3 问题分类
1. 自我介绍类 2. 职业规划类 3. 为什么选择我们 4. 优缺点类
5. 团队合作类 6. 压力挑战类 7. 创新解决问题类 8. 国企特有类

## 六、进度看板（阶段5）

### 6.1 功能
跟踪每家公司网申全流程状态，含截止提醒、状态时间线、OQ存档。

### 6.2 命令
```bash
# 添加记录
python job_search.py campus track add --company "中国电信" --position "测绘工程师" --deadline "2026-10-15" --source "国聘" --url "https://..."

# 更新状态
python job_search.py campus track update --id 1 --status 面试中 --note "一面已完成"

# 查看列表
python job_search.py campus track list [--status 面试中]

# 查看详情（含时间线/OQ存档）
python job_search.py campus track show --id 1

# 统计分析
python job_search.py campus track stats

# 截止提醒（已过期/3天内/7天内）
python job_search.py campus track deadline

# HTML看板报告
python job_search.py campus track report
```

### 6.3 状态机（8种）
待投递 → 已投递 → 测评中 → 面试中 → offer / 已拒绝 / 待定 / 放弃

### 6.4 数据存储
`applications/apply_tracking.json`（测试数据不入库，正式使用时添加真实记录）

## 七、Edge轻量点填扩展（阶段4a）

### 7.1 功能
在网申页面侧边弹出面板，一键填充基本信息，只填不提交。

### 7.2 安装
1. 打开 Edge → 扩展 → 管理扩展
2. 开启"开发人员模式"
3. 点击"加载解压缩的扩展"
4. 选择 `job-search-workspace/fill_extension/` 目录

### 7.3 使用
1. 打开任意网申页面
2. 点击扩展图标，弹出填充面板
3. 点击"一键填充"按钮，自动填充表单
4. **人工核对后手动提交**（扩展绝不自动提交）

### 7.4 安全红线
- 只填不提交，所有提交动作必须人工完成
- 敏感信息（身份证/银行卡）不自动填充，需人工输入
- 验证码/下拉选择/附件上传需人工操作

## 八、完整网申流程示例

```bash
# 1. 查看信息底座摘要，确认信息完整
python job_search.py campus profile

# 2. 机筛检查，发现并修复问题
python job_search.py campus check

# 3. 网申雷达，寻找目标岗位
python job_search.py campus radar --keyword "测绘" --pages 2

# 4. 生成OQ答案备用
python job_search.py campus oq gen

# 5. 添加到进度看板
python job_search.py campus track add --company "中国电信" --position "测绘工程师" --deadline "2026-10-15"

# 6. 用Edge扩展半自动填表（在浏览器中操作）

# 7. 更新状态
python job_search.py campus track update --id 1 --status 已投递 --note "已提交网申"

# 8. 定期查看截止提醒和看板
python job_search.py campus track deadline
python job_search.py campus track report
```

## 九、注意事项

1. **敏感信息**：application_profile.json 含身份证/家人电话，已入 .gitignore，切勿手动添加到 git
2. **反爬风控**：网申雷达只抓公开数据，每日1次低频，不登录不交互
3. **测试数据**：apply_tracking.json 测试数据已清空，正式秋招时添加真实记录
4. **应届生网**：第三源暂挂起，需Browser Use攻克反爬后启用
5. **阶段4b智能全填**：长期规划，边投边打磨，适配北森/Moka等SaaS系统
