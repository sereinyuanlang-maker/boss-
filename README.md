# Boss直聘自动投简历工具

一个基于Python的Boss直聘平台自动投简历工具，支持自动登录、智能职位筛选、批量投递、状态记录等功能，并采用多种反爬策略模拟人类操作行为。

## 功能特性

- **自动登录**: 支持账号密码登录，可保存登录状态避免重复登录
- **智能筛选**: 根据关键词、城市、薪资、经验、学历等多维度筛选职位
- **批量投递**: 自动批量发送求职意向，支持自定义打招呼语
- **状态记录**: 完整记录投递状态，生成Excel报告
- **反爬防护**: 模拟人类操作行为，随机延迟、滚动、鼠标移动等
- **灵活配置**: 通过YAML配置文件或环境变量自定义所有参数

## 项目结构

```
.
├── src/
│   ├── __init__.py
│   ├── main.py              # 主程序入口
│   ├── config_manager.py    # 配置管理
│   ├── browser_manager.py   # 浏览器管理
│   ├── login_manager.py     # 登录管理
│   ├── job_filter.py        # 职位筛选
│   ├── resume_manager.py    # 简历管理
│   ├── delivery_engine.py   # 投递引擎
│   ├── anti_detection.py    # 反爬防护
│   └── logger.py            # 日志配置
├── config.yaml              # 主配置文件
├── requirements.txt         # 依赖清单
├── .env.example             # 环境变量示例
└── README.md                # 使用文档
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 配置账号信息

**方式一：配置文件**

编辑 `config.yaml`:
```yaml
account:
  username: "你的手机号"
  password: "你的密码"
```

**方式二：环境变量**

```bash
cp .env.example .env
# 编辑 .env 文件填写账号信息
```

### 2. 配置职位筛选条件

编辑 `config.yaml` 中的 `filters` 部分:
```yaml
filters:
  keywords:
    - "Python"
    - "后端开发"
  cities:
    - "北京"
    - "上海"
  salary_min: 15
  salary_max: 50
```

### 3. 运行工具

```bash
# 完整流程：登录 -> 搜索 -> 投递
python -m src.main

# 仅登录
python -m src.main -m login

# 仅搜索职位
python -m src.main -m search -p 5

# 仅投递（需先搜索）
python -m src.main -m deliver -l 20

# 更新在线简历
python -m src.main -m resume

# 查看投递统计
python -m src.main -m stats

# 无头模式运行
python -m src.main --headless
```

## 配置说明

### 账号配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `account.username` | 手机号 | "" |
| `account.password` | 密码 | "" |
| `account.captcha_mode` | 验证码处理模式 | manual |

### 浏览器配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `browser.type` | 浏览器类型 | chrome |
| `browser.headless` | 无头模式 | false |
| `browser.width` | 窗口宽度 | 1920 |
| `browser.height` | 窗口高度 | 1080 |
| `browser.use_undetected` | 使用反检测驱动 | true |

### 投递配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `delivery.daily_limit` | 每日投递上限 | 50 |
| `delivery.interval_min` | 最小投递间隔(秒) | 5 |
| `delivery.interval_max` | 最大投递间隔(秒) | 15 |
| `delivery.use_custom_greeting` | 使用自定义打招呼语 | true |
| `delivery.custom_greeting` | 自定义打招呼语 | "" |
| `delivery.active_hours` | 投递时间段 | 09:00-18:00 |

### 筛选配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `filters.keywords` | 搜索关键词列表 | [] |
| `filters.cities` | 目标城市列表 | [] |
| `filters.salary_min` | 最低薪资(K) | 15 |
| `filters.salary_max` | 最高薪资(K) | 50 |
| `filters.experience_min` | 最低经验(年) | 1 |
| `filters.experience_max` | 最高经验(年) | 5 |
| `filters.education` | 学历要求 | 本科 |
| `filters.exclude_keywords` | 排除关键词 | [] |

## 反爬策略

本工具采用以下反爬策略：

1. **undetected-chromedriver**: 使用反检测Chrome驱动
2. **随机延迟**: 操作间随机延迟，模拟人类反应时间
3. **人类化操作**: 模拟真实打字速度、鼠标移动轨迹
4. **随机滚动**: 页面随机滚动，模拟浏览行为
5. **视口变化**: 随机改变窗口大小
6. **脚本注入**: 移除webdriver标志，模拟真实浏览器环境

## 注意事项

1. **合法使用**: 请遵守Boss直聘平台的使用条款
2. **频率控制**: 建议设置合理的投递间隔和每日上限
3. **验证码处理**: 目前支持手动输入验证码
4. **登录状态**: 首次登录后会保存cookies，下次自动使用

## 常见问题

### Q: 登录失败怎么办？
A: 检查账号密码是否正确，确认是否需要验证码，尝试手动登录一次后再使用工具。

### Q: 被平台限制访问？
A: 增加投递间隔时间，减少每日投递数量，避免短时间内大量操作。

### Q: 找不到职位元素？
A: Boss直聘页面结构可能更新，需要检查CSS选择器是否需要调整。

## 技术栈

- Python 3.8+
- Selenium WebDriver
- undetected-chromedriver
- BeautifulSoup4
- Pandas
- Loguru
- Pydantic

## 许可证

MIT License

## 免责声明

本工具仅供学习研究使用，使用者需自行承担使用风险。请遵守相关平台的使用条款和法律法规。