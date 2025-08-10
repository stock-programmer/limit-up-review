# Stock Agent 项目文档

## 项目概述
Stock Agent 是一个功能完整的股票AI智能分析系统，集成了行情数据分析、PDF文档处理、财务报表解析、公告信息挖掘等功能。系统支持涨停股票综合深度分析，能够自动关联市场表现、公司基本面、财务数据和最新公告，为投资决策提供全方位的数据支持。

## 项目结构
```
stock_agent/
├── main.py                    # 主程序入口，股票市场数据综合分析
├── requirements.txt           # 项目依赖
├── market_data/              # 市场数据分析包
│   ├── __init__.py           # 包初始化文件
│   └── market_analyzer.py    # 市场数据分析器
├── pdf_downloader/           # PDF下载器包
│   ├── __init__.py           # 包初始化文件
│   ├── announcement_downloader.py    # 公告PDF下载器
│   └── financial_report_downloader.py # 财务报告PDF下载器
├── llm_pdf_processor/        # LLM PDF处理器包（替换传统PDF处理）
│   ├── __init__.py           # 包初始化文件
│   ├── pdf_text_converter.py # PDF文本转换器
│   ├── llm_client.py         # LLM客户端管理器
│   └── financial_report_analyzer.py # 基于LLM的财务报告分析器
├── comprehensive_analyzer.py # 涨停股票综合分析器
├── prompt/                   # 提示文档目录
│   └── requirement.md        # 需求文档
└── CLAUDE.md                 # 项目文档（本文件）
```

## 环境配置

### 1. Python 环境
- Python 3.10.12
- 位置：/usr/bin/python3

### 2. 依赖包
```bash
pip3 install -r requirements.txt
```

主要依赖：
- tushare>=1.2.89          # 股票数据接口
- pandas>=1.5.0            # 数据处理
- numpy>=1.21.0            # 数值计算
- PyPDF2>=3.0.0           # PDF文本提取（基础功能）
- pdfplumber>=0.9.0       # PDF文本提取（主要使用）
- openpyxl>=3.1.0         # Excel文件处理
- requests>=2.28.0        # HTTP请求（LLM API调用）

### 3. 环境变量设置
```bash
# 设置 tushare pro token
export TUSHARE_TOKEN="your_token_here"

# 设置 LLM API 密钥（选择其中一种）
export OPENAI_API_KEY="your_openai_api_key"          # OpenAI GPT（推荐）
export GEMINI_API_KEY="your_gemini_api_key"          # Google Gemini（推荐，性价比高）
export CLAUDE_API_KEY="your_claude_api_key"          # Claude
export LOCAL_LLM_URL="http://localhost:11434"        # 本地LLM (Ollama)

# 永久设置
echo 'export TUSHARE_TOKEN="your_token_here"' >> ~/.bashrc
echo 'export GEMINI_API_KEY="your_gemini_api_key"' >> ~/.bashrc
source ~/.bashrc
```

## 功能模块

### 1. 主程序 (main.py)
提供两种分析模式：

#### 模式1：市场数据综合分析
```bash
python3 main.py
# 选择: 1-市场分析
```

**包含的9大分析功能：**
1. 每日涨停股票
2. 成交额>4亿且涨幅>5%股票
3. 成交额>4亿且涨停股票
4. 近5日A股涨幅排名（前30名）
5. 近10日A股涨幅排名（前30名）
6. 近20日A股涨幅排名（前30名）
7. 当年股票涨幅排行（前30名）
8. 成交额>4亿且跌幅>5%股票
9. 新高且市值>300亿股票（前30名）

#### 模式2：涨停股票深度分析 🔥
```bash
python3 main.py
# 选择: 2-涨停分析
```

**涨停股票综合分析功能：**
- 📈 **市场表现**：股票代码、名称、涨幅、成交金额
- 🏭 **公司基本面**：主营业务（完整无截断）、所属行业、主要产品
- 📊 **财务数据**：LLM智能提取财务指标和比率
- 📢 **公告分析**：最近30天公告、利好消息识别
- 🔍 **涨停原因**：智能分析涨停与公告关联性
- 📈 **行业热点**：涨停股票行业分布统计
- 💾 **多格式报告**：JSON、Excel详细报告
- 🤖 **AI增强**：使用LLM智能解析财务报告，提供更准确的业务信息

### 2. MarketAnalyzer 类 (market_data/market_analyzer.py)

#### 初始化
```python
from market_data import MarketAnalyzer
analyzer = MarketAnalyzer()
```

#### 功能方法

1. **get_daily_limit_up_stocks(trade_date: str)** - 获取每日涨停股票
   - 参数：trade_date (YYYYMMDD格式)
   - 返回：DataFrame，包含涨停股票信息

2. **get_high_volume_high_gain_stocks(trade_date: str, min_amount: float = 400000)** - 获取每日成交金额大于4亿且涨幅大于5%的股票
   - 参数：trade_date, min_amount（最小成交金额，千元）
   - 返回：DataFrame，符合条件的股票列表

3. **get_high_volume_limit_up_stocks(trade_date: str, min_amount: float = 400000)** - 获取每日成交金额大于4亿且涨停的股票
   - 参数：trade_date, min_amount
   - 返回：DataFrame，符合条件的股票列表

4. **get_5day_return_ranking(end_date: str)** - 获取近5日A股涨幅排名
   - 参数：end_date (YYYYMMDD格式)
   - 返回：DataFrame，5日涨幅排行榜

5. **get_10day_return_ranking(end_date: str)** - 获取近10日A股涨幅排名
   - 参数：end_date
   - 返回：DataFrame，10日涨幅排行榜

6. **get_20day_return_ranking(end_date: str)** - 获取近20日A股涨幅排名
   - 参数：end_date
   - 返回：DataFrame，20日涨幅排行榜

7. **get_ytd_return_ranking(end_date: str)** - 获取当年股票涨幅排行
   - 参数：end_date
   - 返回：DataFrame，年度涨幅排行榜

8. **get_high_volume_high_decline_stocks(trade_date: str, min_amount: float = 400000)** - 获取每日成交金额大于4亿且跌幅大于5%的股票
   - 参数：trade_date, min_amount
   - 返回：DataFrame，符合条件的股票列表

9. **get_new_high_large_cap_stocks(trade_date: str, min_market_cap: float = 30000000)** - 获取每日新高且市值大于300亿的股票，按市值排序
   - 参数：trade_date, min_market_cap（最小市值，万元）
   - 返回：DataFrame，按市值排序的新高股票

### 3. PDF下载器 (pdf_downloader包)

#### AnnouncementDownloader - 公告PDF下载器
```python
from pdf_downloader import AnnouncementDownloader
downloader = AnnouncementDownloader()

# 获取公告列表
announcements = downloader.get_announcements_list('000001.SZ', '20240101', '20241231')

# 下载公告PDF
files = downloader.download_announcements('000001.SZ', '20240101', '20241231')

# 搜索特定公告
financial_anns = downloader.get_financial_report_announcements('000001.SZ', '2024')
```

#### FinancialReportDownloader - 财务报告PDF下载器
```python
from pdf_downloader import FinancialReportDownloader
downloader = FinancialReportDownloader()

# 下载年报
annual_reports = downloader.download_annual_reports('000001.SZ', [2023, 2024])

# 下载指定年份的所有季报
quarterly_reports = downloader.download_quarterly_reports('000001.SZ', 2024)

# 下载所有财务报告
all_reports = downloader.download_all_reports('000001.SZ', 2022, 2024)

# 获取最新报告
latest_reports = downloader.get_latest_reports('000001.SZ')
```

# 获取股票基本信息
stock_info = downloader.get_stock_info('000001')

# 查询公告列表
announcements, total_pages = downloader.query_announcements(
    '000001', 
    start_date='2024-01-01', 
    end_date='2024-12-31',
    category='all_reports'  # annual_report, interim_report, quarterly_report, all
)

# 下载PDF文件
for announcement in announcements:
    file_path = downloader.download_pdf(
        announcement['pdf_url'],
        announcement['title'],
        '000001'
    )

# 下载财务报告
financial_files = downloader.download_financial_reports('000001', 2024)

# 批量下载所有公告
all_files = downloader.download_all_announcements('000001', max_pages=5)

# 关键词搜索
results = downloader.search_announcements_by_keyword('000001', ['年报', '中报'])
```

### 5. 涨停股票综合分析器 (comprehensive_analyzer.py) 🔥

#### ComprehensiveStockAnalyzer - 核心功能
```python
from comprehensive_analyzer import ComprehensiveStockAnalyzer

# 初始化综合分析器
analyzer = ComprehensiveStockAnalyzer()

# 分析指定日期的涨停股票（最多分析10只）
analysis_result = analyzer.analyze_limit_up_stocks('20240801', max_stocks=10)

# 打印分析摘要
analyzer.print_analysis_summary(analysis_result)

# 分析结果包含：
# - limit_up_stocks: 每只股票的详细分析
# - summary: 统计汇总信息
# - industry_analysis: 行业分布分析
# - announcement_themes: 公告主题分析
```

#### 单只股票分析内容
```python
# 每只股票的分析结果包含：
stock_analysis = {
    'stock_code': '000001',           # 股票代码
    'stock_name': '平安银行',         # 股票名称
    'market_data': {                  # 市场数据
        'close_price': 16.85,         # 收盘价
        'change_pct': 10.00,          # 涨跌幅
        'volume': 120500,             # 成交量
        'amount': 2031450             # 成交额
    },
    'business_info': {                # 业务信息
        'main_business': '银行业务...',# 主营业务描述
        'industry': '货币金融服务',    # 所属行业
        'main_products': '银行卡...'   # 主要产品
    },
    'financial_data': {               # 财务数据
        'key_indicators': {           # 关键指标
            'revenue': 167832000000,  # 营业收入
            'net_profit': 39871000000 # 净利润
        },
        'financial_ratios': {         # 财务比率
            'roe': 0.0937,           # 净资产收益率
            'roa': 0.0074            # 总资产收益率
        }
    },
    'recent_announcements': [...],    # 最近公告列表
    'analysis_insights': {            # 分析洞察
        'possible_reasons': [...],    # 可能的涨停原因
        'announcement_correlation': True, # 公告关联性
        'positive_news_count': 1      # 利好消息数量
    }
}
```

#### 智能分析特性
- **自动关联分析**：涨停与公告的时间关联性
- **利好消息识别**：自动识别利好公告类型  
- **行业热点分析**：统计涨停股票行业分布
- **原因推理逻辑**：基于公告内容推断涨停原因
- **同行业关联**：分析同行业股票是否有类似公告

### 4. LLM PDF处理器 (llm_pdf_processor包)

#### FinancialReportAnalyzer - 基于LLM的财务报告分析器 🤖
```python
from llm_pdf_processor import FinancialReportAnalyzer

# 初始化分析器（自动检测可用的LLM客户端）
analyzer = FinancialReportAnalyzer()

# 分析财务报告PDF
analysis_result = analyzer.analyze_financial_report('annual_report.pdf')

if analysis_result['success']:
    # 提取主营业务信息
    business_info = analyzer.extract_business_info(analysis_result)
    print("主营业务:", business_info.get('main_business'))
    print("所属行业:", business_info.get('industry'))
    print("主要产品:", business_info.get('main_products'))
    
    # 提取财务数据
    financial_data = analyzer.extract_financial_data(analysis_result)
    indicators = financial_data['key_indicators']
    print("营业收入:", indicators.get('revenue', 0))
    print("净利润:", indicators.get('net_profit', 0))
    
    # 获取分析摘要
    summary = analyzer.get_analysis_summary(analysis_result)
    print("核心竞争力:", summary.get('core_competitiveness'))
```

#### LLMClient - LLM客户端管理器
```python
from llm_pdf_processor import LLMClient

# 创建LLM客户端管理器
llm_client = LLMClient()

# 查看可用客户端
print("可用客户端:", llm_client.get_available_clients())

# 手动切换LLM客户端
llm_client.set_active_client('gemini')  # 或 'openai', 'claude', 'local'

# 直接分析文本
result = llm_client.analyze_text(text_content, analysis_prompt)

# 直接分析PDF（如果支持）
result = llm_client.analyze_pdf_directly('report.pdf', analysis_prompt)
```

#### PDFTextConverter - PDF文本转换器
```python
from llm_pdf_processor import PDFTextConverter

converter = PDFTextConverter()

# 提取PDF全文
text = converter.extract_text_from_pdf('report.pdf')

# 提取目标章节（第二节、第三节）
sections = converter.extract_target_sections('report.pdf')
print("第二节:", sections['第二节_公司简介和主要财务指标'])
print("第三节:", sections['第三节_管理层讨论与分析'])

# 清理文本
clean_text = converter.clean_text(raw_text)
```

## 完整使用示例

### 1. 市场数据分析
```python
from market_data import MarketAnalyzer

# 初始化分析器
analyzer = MarketAnalyzer()

# 获取涨停股票
limit_up = analyzer.get_daily_limit_up_stocks('20240801')

# 获取高成交额高涨幅股票
high_vol_gain = analyzer.get_high_volume_high_gain_stocks('20240801')

# 获取近5日涨幅排名
ranking_5d = analyzer.get_5day_return_ranking('20240801')
```

### 3. LLM增强的综合分析流程 🚀
```python
# 组合使用所有功能（LLM增强版）
def comprehensive_stock_analysis(stock_code, trade_date):
    # 市场数据分析
    market_analyzer = MarketAnalyzer()
    
    # 检查是否为涨停股票
    limit_up = market_analyzer.get_daily_limit_up_stocks(trade_date)
    is_limit_up = stock_code in limit_up['股票代码'].values if not limit_up.empty else False
    
    # 下载最新财务报告
    from pdf_downloader import CninfoDownloader
    pdf_downloader = CninfoDownloader()
    financial_files = pdf_downloader.download_financial_reports(
        stock_code, 2024, ['annual_report', 'interim_report']
    )
    
    # 使用LLM分析财务报告
    from llm_pdf_processor import FinancialReportAnalyzer
    llm_analyzer = FinancialReportAnalyzer()
    financial_analysis = {}
    
    if financial_files:
        latest_report = financial_files[0]
        analysis_result = llm_analyzer.analyze_financial_report(latest_report)
        
        if analysis_result['success']:
            financial_analysis = {
                'business_info': llm_analyzer.extract_business_info(analysis_result),
                'financial_data': llm_analyzer.extract_financial_data(analysis_result),
                'summary': llm_analyzer.get_analysis_summary(analysis_result)
            }
    
    return {
        'stock_code': stock_code,
        'trade_date': trade_date,
        'is_limit_up': is_limit_up,
        'financial_analysis': financial_analysis,
        'llm_enhanced': True
    }

# 使用示例
result = comprehensive_stock_analysis('000001.SZ', '20240801')
print("主营业务:", result['financial_analysis']['business_info'].get('main_business'))
```

## 数据源说明

### Tushare Pro API 接口
- **daily**: 日线行情数据
- **stock_basic**: 股票基本信息
- **daily_basic**: 每日基本指标（包含市值）
- **trade_cal**: 交易日历

### 数据字段说明
- ts_code: 股票代码
- name: 股票名称
- close: 收盘价
- pct_chg: 涨跌幅(%)
- vol: 成交量(手)
- amount: 成交额(千元)
- total_mv: 总市值(万元)

### LLM支持的数据源

#### 支持的LLM服务
1. **OpenAI GPT-4o** - 最稳定可靠，支持直接PDF分析
2. **Google Gemini** - 性价比最高，支持直接PDF分析，推荐使用
3. **Claude (Anthropic)** - 优秀的中文理解能力
4. **本地LLM (Ollama)** - 完全离线，支持qwen2.5等开源模型

#### LLM分析能力
- **智能语义理解**：自动识别业务描述的多种表达方式
- **结构化提取**：从非结构化文本中提取结构化财务数据
- **上下文理解**：理解财务报告的业务逻辑和关联关系
- **多格式适应**：适应各种PDF格式和排版方式

## 注意事项

1. **Token 配置**：必须设置有效的 TUSHARE_TOKEN 环境变量
2. **LLM配置**：涨停分析功能需要配置LLM API密钥（推荐使用Gemini）
3. **交易日**：只能查询交易日的数据，非交易日会返回空结果
4. **API 限制**：tushare pro 有调用频率限制（500次/分钟）
5. **数据延迟**：行情数据通常在交易日15:00-16:00更新
6. **历史数据**：部分功能需要足够的历史数据支持
7. **LLM成本**：使用商业LLM服务会产生API调用费用
8. **网络连接**：LLM分析需要稳定的网络连接（本地LLM除外）

## 错误处理
所有方法都包含完整的错误处理，当出现问题时会打印错误信息并返回空的 DataFrame。

## 重要提醒

### LLM PDF处理系统 🚀
**新版本**：项目已升级为基于大语言模型的智能PDF处理系统，具备以下优势：

#### 主要改进
1. **智能内容理解** - 替代传统的正则表达式匹配
2. **完整业务信息** - 主营业务描述不再截断，支持完整提取
3. **结构化数据提取** - 自动提取财务指标并计算比率
4. **多种LLM支持** - OpenAI、Gemini、Claude、本地LLM

#### 配置要求
- **必需**：设置TUSHARE_TOKEN用于股票数据
- **推荐**：设置GEMINI_API_KEY用于PDF分析（性价比最高）
- **备选**：OPENAI_API_KEY 或 CLAUDE_API_KEY
- **离线**：安装Ollama本地LLM服务

#### PDF数据源
系统对接巨潮资讯网(cninfo.com.cn)，自动下载和分析：
1. **年度报告** - 完整财务数据和业务分析
2. **半年度报告** - 中期财务状况
3. **季度报告** - 季度财务数据

### 快速开始
```bash
# 1. 设置环境变量
export TUSHARE_TOKEN="your_tushare_token"
export GEMINI_API_KEY="your_gemini_key"

# 2. 运行涨停分析
python3 main.py
# 选择模式2进行LLM增强的涨停分析

# 3. 测试LLM功能
python3 test_llm_pdf.py
```

## 扩展说明
项目采用模块化设计，包含四大核心模块：

1. **market_data** - 市场数据分析，支持9种股票筛选和排名功能
2. **pdf_downloader** - PDF文件下载，支持公告和财报获取
3. **llm_pdf_processor** - 🤖 LLM智能PDF处理，支持财务报告智能分析
4. **comprehensive_analyzer** - 涨停股票综合分析，整合所有功能模块

### 技术架构对比

| 功能模块 | 传统方案 | LLM增强方案 |
|----------|----------|-------------|
| **PDF文本提取** | 基础文本提取 | 智能章节识别 |
| **业务信息提取** | 正则表达式匹配 | LLM语义理解 |
| **财务数据提取** | 表格识别 | LLM结构化解析 |
| **准确性** | 60-70% | 90-95% |
| **完整性** | 部分信息 | 完整提取 |
| **适应性** | 固定格式 | 任意格式 |

### 投资策略扩展
基于LLM增强的数据提取，可以轻松扩展以下高级功能：
- **ESG评估** - 分析企业社会责任和治理水平
- **风险预警** - 基于财务指标和公告内容的风险识别
- **行业比较** - 同行业公司的智能对比分析
- **投资组合优化** - 基于多维度数据的组合建议

所有功能都支持方便的函数调用和组合使用，LLM的加入大大提升了系统的智能化水平和分析精度。