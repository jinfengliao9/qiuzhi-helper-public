# SOP-001：简历生成标准操作流程

## 目的

生成4套模板的HTML+PDF简历，确保简历格式统一、内容完整、样式美观。

## 前置条件

1. 工作区目录已初始化
2. `resume_data.json`简历数据源已存在且内容完整
3. `cv/avatar.jpg`头像文件已存在（如需要头像）
4. Edge浏览器已安装（用于HTML转PDF）

## 操作步骤

### 步骤1：验证简历数据

```bash
python job_search.py validate
```

- 检查简历数据是否通过Schema验证
- 检查基本信息是否完整（姓名、电话、邮箱）
- 检查是否有实习经历或项目经历
- 检查技能清单是否存在

### 步骤2：运行简历质量检查

```bash
python job_search.py quality resume
```

- 检查简历数据的业务逻辑
- 检查邮箱格式、电话格式
- 检查内容完整性

### 步骤3：生成简历

```bash
python job_search.py resume
```

- 脚本会自动生成4套模板的HTML简历
- 自动调用Edge浏览器将HTML转换为PDF
- 输出文件保存在`cv/`目录下

### 步骤4：验证生成结果

1. 检查`cv/`目录下是否生成了4套HTML文件
2. 检查是否生成了对应的PDF文件
3. 用浏览器打开HTML文件，检查：
   - 内容是否完整
   - 样式是否正确
   - 头像是否显示
   - 排版是否美观
   - 是否有溢出或截断

### 步骤5：按需生成Word版本（可选）

如需Word版本，使用专门的Word渲染脚本：
```bash
python -c "import sys; sys.path.insert(0, '.'); from render_cv_word import render_cv_word; render_cv_word('resume_data.json', 'cv/简历.docx')"
```

## 验证方法

1. **数据验证**：`python job_search.py validate` 全部通过
2. **质量检查**：`python job_search.py quality resume` 无错误
3. **文件检查**：4套HTML+PDF文件均已生成
4. **内容检查**：人工检查简历内容完整、格式正确

## 常见问题

### Q1：简历生成失败，提示找不到Edge浏览器

**A**：确保Edge浏览器已安装，并将Edge添加到系统PATH。或手动修改`generate_selected.py`中的Edge路径。

### Q2：PDF转换失败或样式丢失

**A**：用Edge浏览器手动打开HTML文件，按Ctrl+P，勾选"背景图形"，保存为PDF。

### Q3：头像不显示

**A**：检查`cv/avatar.jpg`文件是否存在，文件名是否正确，图片格式是否为JPG。

### Q4：简历内容溢出到第二页

**A**：精简简历内容，或调整`resume_data.json`中的描述长度。应届毕业生建议控制在一页。

### Q5：如何修改简历内容

**A**：直接编辑`resume_data.json`文件，修改后重新运行`python job_search.py resume`即可。

## 相关文档

- [SOP-003：定制简历生成SOP](SOP-003_定制简历生成SOP.md)
- [SOP-008：数据验证SOP](SOP-008_数据验证SOP.md)
- [SOP-009：质量检查SOP](SOP-009_质量检查SOP.md)
