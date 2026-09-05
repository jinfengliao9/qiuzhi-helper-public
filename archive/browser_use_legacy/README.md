# Browser Use 时代遗留脚本归档

本目录存放 v0.2.0 之前、基于 **Browser Use / CDP 自动化抓取** 的遗留脚本。
自 v0.2.0 起，岗位采集主路径已切换为 **Edge 扩展被动采集**（见 `boss_api/`），
Browser Use 方案因触发 BOSS 风控（页面跳动、无法在内置浏览器登录）已弃用。

## 本目录文件

| 文件 | 原用途 | 状态 |
|------|--------|------|
| `multi_keyword_search.py` | Browser Use 多关键词搜索（导航+抓取代码生成+合并解析） | 已归档，不再使用 |
| `scraper_config.py` | Browser Use 抓取参数配置（平台/数量/间隔/滚动次数） | 已归档，不再使用 |

## 仍保留在工作区根目录的"旧时代但活跃复用"文件

以下文件虽然诞生于 Browser Use 时代，但其中的核心类/函数被现行流水线
（`job_pipeline.py` 的 import/rank/report、`filter_jobs.py` 的本地筛选）活跃引用，
**因此不归档、不删除**，仅在此明确其复用边界：

| 文件 | 活跃复用部分 | 已废弃部分 |
|------|-------------|-----------|
| `job_collector.py` | `JobCollector` 类——jobs.json 的数据访问层（增删改查/批量导入/匹配分更新/统计），被 job_pipeline、filter_jobs 依赖 | 文件内若含 Browser Use 抓取方法，均已不再调用 |
| `jd_parser.py` | `parse_job_detail()`、`extract_basic_info()`——从详情文本拆分职责/要求、提取基本信息，被 job_pipeline import 流程用于 scraped_jobs.json 格式 | 与 Browser Use 抓取流程绑定的调用路径已不再是主路径（新扩展采集由 parse_joblist_api / parse_zhaopin_api 直接产出已拆分字段） |

## 恢复使用（如需）

若未来要参考 Browser Use 时代的实现思路，可直接阅读本目录文件；
如需临时运行，将文件移回工作区根目录即可（它们依赖根目录的 match_engine / report_generator 等）。

## 相关文档

- `SKILL.md` 流程六「已归档/已证伪的方案」
- `references/sop/SOP-006_岗位抓取SOP.md`
