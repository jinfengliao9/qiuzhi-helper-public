# 标准操作流程（SOP）索引

本目录包含求职工作区Skill的所有标准操作流程文档。

## SOP列表

| 编号 | 文档 | 说明 |
|------|------|------|
| SOP-001 | [简历生成SOP.md](SOP-001_简历生成SOP.md) | 生成4套模板的HTML+PDF简历 |
| SOP-002 | [职位匹配评估SOP.md](SOP-002_职位匹配评估SOP.md) | 对JD进行匹配度评估 |
| SOP-003 | [综合SOP（SOP-003至010）](SOP-003至010_综合SOP.md) | 定制简历/面试准备/申请归档/报告生成/数据验证/质量检查/配置管理 |
| SOP-006 | [岗位抓取SOP.md](SOP-006_岗位抓取SOP.md) | Edge扩展被动采集BOSS+智联岗位（主路径，含补JD/合并/风控，Browser Use已归档） |

> **说明**：SOP-003至SOP-010已合并为综合SOP文档，包含7个操作流程的详细步骤。

## 使用说明

1. 每个SOP文档包含：目的、前置条件、操作步骤、验证方法、常见问题
2. 执行任务前，先阅读对应的SOP文档
3. 严格按照SOP步骤执行，确保操作一致性
4. 如发现SOP有问题或需要更新，及时修改并记录

## 快速命令参考

```bash
# 简历生成
python job_search.py resume

# 职位匹配评估
python job_search.py rank --jd job_description.txt

# 面试准备
python job_search.py interview --company "公司名" --position "岗位名"

# 申请归档
python job_search.py outcome add --company "公司名" --position "岗位名"
python job_search.py outcome list
python job_search.py outcome stats

# 岗位库管理
python job_search.py jobs list
python job_search.py jobs report

# 配置管理
python job_search.py config show
python job_search.py config validate

# 数据验证
python job_search.py validate

# 质量检查
python job_search.py quality check
```
