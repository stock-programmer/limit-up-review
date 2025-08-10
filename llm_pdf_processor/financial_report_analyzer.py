"""
基于LLM的财务报告分析器
使用大语言模型分析财务报告PDF，提取结构化信息
"""

import json
import os
from typing import Dict, Any, Optional
from .pdf_text_converter import PDFTextConverter
from .llm_client import LLMClient


class FinancialReportAnalyzer:
    """基于LLM的财务报告分析器"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        初始化分析器
        
        Args:
            llm_client (Optional[LLMClient]): LLM客户端，如果为None则创建默认客户端
        """
        self.pdf_converter = PDFTextConverter()
        self.llm_client = llm_client or LLMClient()
        
        # 分析提示词模板
        self.analysis_prompt = self._get_analysis_prompt()
    
    def _get_analysis_prompt(self) -> str:
        """获取财务报告分析提示词"""
        return """
你是一个专业的财务分析师，请仔细分析以下财务报告内容，并按照以下结构化格式输出分析结果。请确保输出的是有效的JSON格式。

请重点关注并提取以下信息：

**第二节 公司简介和主要财务指标**
1. 公司信息
2. 主要会计数据和财务指标

**第三节 管理层讨论与分析**
1. 报告期内公司所处行业情况
2. 报告期内公司从事的主要业务
3. 核心竞争力分析
4. 主营业务分析
5. 公司未来发展的展望

请严格按照以下JSON格式输出分析结果：

```json
{
  "公司基本信息": {
    "公司名称": "提取的公司全名",
    "股票代码": "股票代码",
    "所属行业": "所属行业",
    "主营业务": "详细的主营业务描述",
    "主要产品及用途": "主要产品和用途说明",
    "主要经营模式": "经营模式描述"
  },
  "主要财务指标": {
    "营业收入": "营业收入数值（单位：元）",
    "营业收入_亿元": "营业收入（单位：亿元）",
    "归属于上市公司股东的净利润": "净利润数值（单位：元）",
    "归属于上市公司股东的净利润_亿元": "净利润（单位：亿元）",
    "归属于上市公司股东的扣除非经常性损益的净利润": "扣非净利润数值（单位：元）",
    "归属于上市公司股东的扣除非经常性损益的净利润_亿元": "扣非净利润（单位：亿元）",
    "经营活动产生的现金流量净额": "经营现金流数值（单位：元）",
    "基本每股收益": "每股收益数值（单位：元/股）",
    "资产总额": "资产总额数值（单位：元）",
    "归属于上市公司股东的净资产": "净资产数值（单位：元）"
  },
  "管理层讨论与分析": {
    "所处行业情况": "报告期内公司所处行业的详细描述",
    "主要业务情况": "报告期内公司从事的主要业务详细说明",
    "核心竞争力": "公司核心竞争力分析",
    "主营业务分析": "主营业务的详细分析",
    "未来发展展望": "公司未来发展的展望和规划"
  }
}
```

注意事项：
1. 如果某个字段无法从报告中提取到确切信息，请填写"信息未找到"
2. 财务数据请保持原始单位，同时提供亿元单位的换算值
3. 描述性文字请尽可能详细完整，保留重要信息
4. 确保输出的是有效的JSON格式，可以被Python的json.loads()正确解析
5. 不要添加任何JSON格式之外的文本

现在请分析以下财务报告内容：
"""
    
    def analyze_financial_report(self, pdf_path: str) -> Dict[str, Any]:
        """
        分析财务报告PDF文件
        
        Args:
            pdf_path (str): PDF文件路径
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            print(f"开始分析财务报告: {os.path.basename(pdf_path)}")
            
            # 初始化结果
            result = {
                'pdf_path': pdf_path,
                'success': False,
                'error': None,
                'raw_llm_response': '',
                'parsed_data': {}
            }
            
            # 检查LLM客户端是否配置
            if not self.llm_client.is_configured():
                result['error'] = "未配置LLM客户端，请设置API密钥"
                return result
            
            # 尝试直接分析PDF（如果LLM支持）
            print("尝试直接分析PDF文件...")
            llm_response = self.llm_client.analyze_pdf_directly(pdf_path, self.analysis_prompt)
            
            # 如果直接分析失败，使用文本提取方式
            if not llm_response.strip():
                print("直接分析PDF失败，转换为文本后分析...")
                
                # 提取目标章节
                sections = self.pdf_converter.extract_target_sections(pdf_path)
                
                if not any(sections.values()):
                    # 如果没有提取到目标章节，提取全文
                    print("未找到目标章节，提取全文进行分析...")
                    full_text = self.pdf_converter.extract_text_from_pdf(pdf_path)
                    analysis_text = full_text[:50000]  # 限制长度避免超出token限制
                else:
                    # 合并目标章节
                    analysis_text = "\n\n".join([
                        f"=== {section_name} ===\n{content}" 
                        for section_name, content in sections.items() 
                        if content.strip()
                    ])
                
                # 使用LLM分析文本
                llm_response = self.llm_client.analyze_text(analysis_text, self.analysis_prompt)
            
            result['raw_llm_response'] = llm_response
            
            if llm_response.strip():
                # 解析LLM响应
                parsed_data = self._parse_llm_response(llm_response)
                if parsed_data:
                    result['parsed_data'] = parsed_data
                    result['success'] = True
                    print("财务报告分析完成")
                else:
                    result['error'] = "LLM响应解析失败"
            else:
                result['error'] = "LLM未返回有效响应"
            
            return result
            
        except Exception as e:
            print(f"分析财务报告失败: {e}")
            return {
                'pdf_path': pdf_path,
                'success': False,
                'error': str(e),
                'raw_llm_response': '',
                'parsed_data': {}
            }
    
    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        解析LLM响应
        
        Args:
            response (str): LLM原始响应
            
        Returns:
            Optional[Dict[str, Any]]: 解析后的数据
        """
        try:
            # 尝试直接解析JSON
            if response.strip().startswith('{') and response.strip().endswith('}'):
                return json.loads(response)
            
            # 查找JSON代码块
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            
            # 查找JSON对象
            json_match = re.search(r'(\{.*\})', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            
            print("未找到有效的JSON格式响应")
            return None
            
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            return None
        except Exception as e:
            print(f"解析LLM响应失败: {e}")
            return None
    
    def extract_business_info(self, analysis_result: Dict[str, Any]) -> Dict[str, str]:
        """
        从分析结果中提取主营业务信息
        
        Args:
            analysis_result (Dict[str, Any]): 分析结果
            
        Returns:
            Dict[str, str]: 主营业务信息
        """
        business_info = {}
        
        try:
            if analysis_result['success'] and analysis_result['parsed_data']:
                data = analysis_result['parsed_data']
                
                # 提取公司基本信息
                company_info = data.get('公司基本信息', {})
                business_info['main_business'] = company_info.get('主营业务', '')
                business_info['industry'] = company_info.get('所属行业', '')
                business_info['main_products'] = company_info.get('主要产品及用途', '')
                business_info['business_model'] = company_info.get('主要经营模式', '')
                
                # 补充管理层讨论分析的信息
                analysis_info = data.get('管理层讨论与分析', {})
                if not business_info['main_business'] and analysis_info.get('主要业务情况'):
                    business_info['main_business'] = analysis_info['主要业务情况']
                
                # 清理空值
                business_info = {k: v for k, v in business_info.items() if v and v != '信息未找到'}
        
        except Exception as e:
            print(f"提取主营业务信息失败: {e}")
        
        return business_info
    
    def extract_financial_data(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        从分析结果中提取财务数据
        
        Args:
            analysis_result (Dict[str, Any]): 分析结果
            
        Returns:
            Dict[str, Any]: 财务数据
        """
        financial_data = {'key_indicators': {}, 'financial_ratios': {}}
        
        try:
            if analysis_result['success'] and analysis_result['parsed_data']:
                data = analysis_result['parsed_data']
                financial_indicators = data.get('主要财务指标', {})
                
                # 提取关键指标
                key_indicators = {}
                
                # 营业收入
                if financial_indicators.get('营业收入'):
                    try:
                        revenue_str = str(financial_indicators['营业收入']).replace(',', '').replace('元', '')
                        key_indicators['revenue'] = float(revenue_str)
                    except:
                        pass
                
                # 净利润
                if financial_indicators.get('归属于上市公司股东的净利润'):
                    try:
                        profit_str = str(financial_indicators['归属于上市公司股东的净利润']).replace(',', '').replace('元', '')
                        key_indicators['net_profit'] = float(profit_str)
                    except:
                        pass
                
                # 资产总额
                if financial_indicators.get('资产总额'):
                    try:
                        assets_str = str(financial_indicators['资产总额']).replace(',', '').replace('元', '')
                        key_indicators['total_assets'] = float(assets_str)
                    except:
                        pass
                
                # 净资产
                if financial_indicators.get('归属于上市公司股东的净资产'):
                    try:
                        equity_str = str(financial_indicators['归属于上市公司股东的净资产']).replace(',', '').replace('元', '')
                        key_indicators['total_equity'] = float(equity_str)
                    except:
                        pass
                
                financial_data['key_indicators'] = key_indicators
                
                # 计算财务比率
                if key_indicators:
                    ratios = {}
                    
                    # ROE
                    if 'net_profit' in key_indicators and 'total_equity' in key_indicators:
                        if key_indicators['total_equity'] != 0:
                            ratios['roe'] = key_indicators['net_profit'] / key_indicators['total_equity']
                    
                    # ROA
                    if 'net_profit' in key_indicators and 'total_assets' in key_indicators:
                        if key_indicators['total_assets'] != 0:
                            ratios['roa'] = key_indicators['net_profit'] / key_indicators['total_assets']
                    
                    financial_data['financial_ratios'] = ratios
        
        except Exception as e:
            print(f"提取财务数据失败: {e}")
        
        return financial_data
    
    def get_analysis_summary(self, analysis_result: Dict[str, Any]) -> Dict[str, str]:
        """
        获取分析摘要
        
        Args:
            analysis_result (Dict[str, Any]): 分析结果
            
        Returns:
            Dict[str, str]: 分析摘要
        """
        summary = {}
        
        try:
            if analysis_result['success'] and analysis_result['parsed_data']:
                data = analysis_result['parsed_data']
                
                # 公司基本信息
                company_info = data.get('公司基本信息', {})
                summary['company_name'] = company_info.get('公司名称', '')
                summary['stock_code'] = company_info.get('股票代码', '')
                summary['industry'] = company_info.get('所属行业', '')
                
                # 核心竞争力
                analysis_info = data.get('管理层讨论与分析', {})
                summary['core_competitiveness'] = analysis_info.get('核心竞争力', '')
                summary['future_outlook'] = analysis_info.get('未来发展展望', '')
        
        except Exception as e:
            print(f"获取分析摘要失败: {e}")
        
        return summary