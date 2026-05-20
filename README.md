# Boss直聘自动投简历工具

基于 Python + Selenium 的 Boss直聘 自动化简历投递工具，支持职位筛选、反反爬机制、投递状态记录等功能。

## 功能特性

- **自动登录**: 支持手机号+短信验证码登录
- **智能筛选**: 根据关键词、薪资、城市、经验等条件筛选职位
- **自动投递**: 自动打开职位详情并发送简历
- **反反爬机制**: 
  - 随机请求间隔
  - 模拟真实用户行为（点击、滚动、鼠标移动）
  - 隐藏自动化特征
  - 滑块验证码自动识别
- **状态记录**: 自动记录投递状态，避免重复投递
- **配置化管理**: YAML配置文件自定义所有参数
- **详细日志**: 使用 loguru 记录完整操作日志
- **数据导出**: 支持导出投递记录为 Excel

## 项目结构

```
自动投简历/
├── src/
│   ├── __init__.py          # 包初始化
│   ├── config.py             # 配置管理模块
│   ├── logger.py             # 日志系统
│   ├── anti_detect.py        # 反反爬机制
│   ├── browser.py            # 浏览器管理
│   ├── filter.py             # 职位筛选器
│   ├── sender.py             # 简历投递器
│   └── recorder.py           # 状态记录器
├── main.py                   # 主程序入口
├── config.example.yaml       # 配置文件示例
├── .env.example              # 环境变量示例
├── requirements.txt          # Python依赖
├── README.md                 # 使用文档
├── logs/                     # 日志目录
├── data/                     # 数据存储目录
└── browser_data/             # 浏览器用户数据
```

## 环境要求

- Python 3.10+
- Google Chrome 浏览器
- macOS / Linux / Windows

## 安装步骤

### 1. 克隆项目

```bash
cd /Users/mac/Al/大al/自动投简历
```

### 2. 创建虚拟环境（推荐）

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制 `.env.example` 为 `.env`，填写您的Boss直聘账号：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
BOSS_USERNAME=您的手机号
BOSS_PASSWORD=您的密码
```

### 5. 配置投递参数

复制配置文件示例：

```bash
cp config.example.yaml config.yaml
```

编辑 `config.yaml`，根据您的需求修改搜索条件、简历信息等。

## 使用方法

### 基本使用

```bash
python main.py
```

### 指定配置文件

```bash
python main.py --config /path/to/your/config.yaml
```

### 查看版本

```bash
python main.py --version
```

## 配置说明

### 搜索配置 (search)

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| keywords | list | 职位关键词 | ["Python开发", "后端工程师"] |
| cities | list | 目标城市 | ["北京", "上海"] |
| salary_range | str | 薪资范围 | "15k-30k" |
| experience | str | 经验要求 | "3-5年" |
| degree | str | 学历要求 | "本科" |
| company_size | str | 公司规模 | "100-499人" |
| financing_stage | str | 融资阶段 | "B轮" |

### 简历配置 (resume)

| 参数 | 类型 | 说明 |
|------|------|------|
| name | str | 您的姓名（必填） |
| phone | str | 联系电话 |
| email | str | 电子邮箱 |
| greeting_template | str | 打招呼模板，支持占位符 |
| resume_pdf_path | str | 简历PDF路径 |

**打招呼模板占位符：**
- `{name}` - 您的姓名
- `{company}` - 公司名
- `{position}` - 职位名

### 策略配置 (strategy)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| max_applications_per_day | int | 50 | 每日最大投递数 |
| min_interval_seconds | int | 5 | 最小请求间隔 |
| max_interval_seconds | int | 15 | 最大请求间隔 |
| random_click | bool | true | 模拟随机点击 |
| scroll_randomly | bool | true | 随机滚动页面 |
| headless | bool | false | 无头模式 |
| retry_times | int | 3 | 失败重试次数 |

## 反反爬机制说明

本工具实现了多层反反爬策略：

1. **请求间隔控制**: 随机间隔 5-15 秒，模拟人工操作节奏
2. **行为模拟**: 
   - 随机页面滚动
   - 随机鼠标移动
   - 随机点击页面元素
   - 模拟人类打字速度
3. **特征隐藏**: 
   - 移除 `navigator.webdriver` 属性
   - 模拟 Chrome 运行时环境
   - 模拟插件列表
4. **验证码处理**: 自动识别并尝试通过滑块验证码

## 日志说明

日志文件存储在 `logs/` 目录下：
- `boss_auto_apply.log` - 主程序日志
- 按日期轮转，单文件最大 10MB
- 保留最近 30 天的日志

## 数据存储

投递记录存储在 `data/` 目录下：
- `applied_jobs.json` - 已投递职位记录（用于去重）
- `applications_YYYYMMDD.json` - 每日投递详情
- `applications_YYYYMMDD.xlsx` - Excel格式导出

## 注意事项

1. **合法合规**: 本工具仅供学习研究使用，请遵守 Boss直聘 的使用条款
2. **频率控制**: 建议合理设置投递频率，避免对平台造成压力
3. **账号安全**: 请妥善保管账号信息，不要将 `.env` 文件提交到代码仓库
4. **验证码处理**: 首次登录可能需要手动输入短信验证码
5. **浏览器兼容性**: 确保已安装 Google Chrome 浏览器

## 常见问题

### Q: 登录时提示需要验证码？
A: 工具会自动处理滑块验证码，如遇短信验证码请在控制台输入后按回车继续。

### Q: 投递失败怎么办？
A: 检查网络连接，查看日志文件 `logs/boss_auto_apply.log` 获取详细错误信息。

### Q: 如何防止被封号？
A: 
- 控制每日投递数量（建议不超过50）
- 增大请求间隔时间
- 避免频繁运行
- 使用正常的浏览器用户数据目录

### Q: 支持其他招聘平台吗？
A: 当前版本仅支持 Boss直聘，后续可考虑扩展其他平台。

## 技术栈

- **Python 3.10+**
- **Selenium** - 浏览器自动化
- **undetected-chromedriver** - 反检测Chrome驱动
- **Pydantic** - 配置数据验证
- **Loguru** - 日志记录
- **PyYAML** - YAML配置解析
- **Pandas** - 数据导出

## 免责声明

本工具仅供学习和技术研究使用。使用本工具产生的任何后果由使用者自行承担。请遵守相关平台的服务条款和法律法规，合理使用自动化工具。

## License

MIT License
