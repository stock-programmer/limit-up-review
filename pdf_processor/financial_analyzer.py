"""
财务PDF分析器
专门用于分析财务报告PDF文件
提供财务数据提取、指标计算等功能
"""

import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import re
import numpy as np
from .text_extractor import PDFTextExtractor
from .table_extractor import PDFTableExtractor


class FinancialPDFAnalyzer:
    """财务PDF分析器"""
    
    def __init__(self):
        """初始化财务分析器"""
        self.text_extractor = PDFTextExtractor()
        self.table_extractor = PDFTableExtractor()
        
        # 财务指标关键词映射
        self.financial_indicators = {
            # 资产负债表项目
            'total_assets': ['资产总计', '总资产', '资产合计'],
            'total_liabilities': ['负债合计', '负债总计', '总负债'],
            'total_equity': ['所有者权益合计', '股东权益合计', '净资产'],
            'current_assets': ['流动资产合计', '流动资产'],
            'current_liabilities': ['流动负债合计', '流动负债'],
            
            # 利润表项目
            'revenue': ['营业收入', '主营业务收入', '总收入'],
            'operating_profit': ['营业利润', '经营利润'],
            'net_profit': ['净利润', '归属于母公司股东的净利润'],
            'gross_profit': ['毛利润', '营业毛利'],
            'operating_cost': ['营业成本', '主营业务成本'],
            
            # 现金流量表项目
            'operating_cash_flow': ['经营活动产生的现金流量净额', '经营性现金流'],
            'investing_cash_flow': ['投资活动产生的现金流量净额', '投资性现金流'],
            'financing_cash_flow': ['筹资活动产生的现金流量净额', '筹资性现金流'],
        }
    
    def analyze_financial_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        分析财务PDF文件
        
        Args:
            pdf_path (str): 财务PDF文件路径
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        result = {
            'pdf_path': pdf_path,
            'text_content': '',
            'financial_tables': {},
            'key_indicators': {},
            'financial_ratios': {},
            'summary': {}
        }
        
        try:
            print(f"开始分析财务PDF: {pdf_path}")
            
            # 1. 提取文本内容
            result['text_content'] = self.text_extractor.extract_text(pdf_path)
            
            # 2. 提取财务表格
            result['financial_tables'] = self.table_extractor.extract_financial_tables(pdf_path)
            
            # 3. 提取关键财务指标
            result['key_indicators'] = self.extract_key_indicators(result['financial_tables'])
            
            # 4. 计算财务比率
            result['financial_ratios'] = self.calculate_financial_ratios(result['key_indicators'])
            
            # 5. 生成分析摘要
            result['summary'] = self.generate_analysis_summary(result)
            
            print("财务PDF分析完成")
            return result
            
        except Exception as e:
            print(f"分析财务PDF失败: {e}")
            result['error'] = str(e)
            return result
    
    def extract_key_indicators(self, financial_tables: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """
        从财务表格中提取关键指标
        
        Args:
            financial_tables (Dict[str, pd.DataFrame]): 财务表格数据
            
        Returns:
            Dict[str, float]: 关键指标数据
        """
        indicators = {}
        
        try:
            for table_type, table in financial_tables.items():
                if table.empty:
                    continue
                
                # 将表格转换为文本用于搜索
                table_text = table.to_string()
                
                # 搜索每个财务指标
                for indicator_name, keywords in self.financial_indicators.items():
                    value = self._find_indicator_value(table, keywords)
                    if value is not None:
                        indicators[indicator_name] = value
            
            return indicators
            
        except Exception as e:
            print(f"提取关键指标失败: {e}")
            return {}
    
    def _find_indicator_value(self, table: pd.DataFrame, keywords: List[str]) -> Optional[float]:
        """
        在表格中查找指标数值
        
        Args:
            table (pd.DataFrame): 表格数据
            keywords (List[str]): 搜索关键词
            
        Returns:
            Optional[float]: 找到的数值
        """
        try:
            for _, row in table.iterrows():
                row_text = ' '.join([str(cell) for cell in row if pd.notna(cell)])
                
                # 检查是否包含关键词
                if any(keyword in row_text for keyword in keywords):
                    # 查找数值
                    for cell in row:
                        if pd.notna(cell) and isinstance(cell, (int, float)):
                            return float(cell)
                        elif pd.notna(cell) and isinstance(cell, str):
                            # 尝试提取数值
                            numbers = re.findall(r'-?\d+(?:,\d{3})*(?:\.\d+)?', str(cell).replace(',', ''))
                            if numbers:
                                try:
                                    return float(numbers[-1])  # 取最后一个数字
                                except ValueError:
                                    continue
            
            return None
            
        except Exception as e:
            print(f"查找指标数值失败: {e}")
            return None
    
    def calculate_financial_ratios(self, indicators: Dict[str, float]) -> Dict[str, float]:
        """
        计算财务比率
        
        Args:
            indicators (Dict[str, float]): 财务指标数据
            
        Returns:
            Dict[str, float]: 财务比率
        """
        ratios = {}
        
        try:
            # 流动比率 = 流动资产 / 流动负债
            if 'current_assets' in indicators and 'current_liabilities' in indicators:
                if indicators['current_liabilities'] != 0:
                    ratios['current_ratio'] = indicators['current_assets'] / indicators['current_liabilities']
            
            # 资产负债率 = 总负债 / 总资产
            if 'total_liabilities' in indicators and 'total_assets' in indicators:
                if indicators['total_assets'] != 0:
                    ratios['debt_ratio'] = indicators['total_liabilities'] / indicators['total_assets']
            
            # 净资产收益率 = 净利润 / 净资产
            if 'net_profit' in indicators and 'total_equity' in indicators:
                if indicators['total_equity'] != 0:
                    ratios['roe'] = indicators['net_profit'] / indicators['total_equity']
            
            # 总资产收益率 = 净利润 / 总资产
            if 'net_profit' in indicators and 'total_assets' in indicators:
                if indicators['total_assets'] != 0:
                    ratios['roa'] = indicators['net_profit'] / indicators['total_assets']
            
            # 毛利率 = (营业收入 - 营业成本) / 营业收入
            if 'revenue' in indicators and 'operating_cost' in indicators:
                if indicators['revenue'] != 0:
                    gross_profit = indicators['revenue'] - indicators['operating_cost']
                    ratios['gross_margin'] = gross_profit / indicators['revenue']
            
            # 净利率 = 净利润 / 营业收入
            if 'net_profit' in indicators and 'revenue' in indicators:
                if indicators['revenue'] != 0:
                    ratios['net_margin'] = indicators['net_profit'] / indicators['revenue']
            
            return ratios
            
        except Exception as e:
            print(f"计算财务比率失败: {e}")
            return {}
    
    def extract_company_info(self, text_content: str) -> Dict[str, str]:
        """
        从文本中提取公司基本信息
        
        Args:
            text_content (str): PDF文本内容
            
        Returns:
            Dict[str, str]: 公司信息
        """
        company_info = {}
        
        try:
            # 公司名称
            name_pattern = r'公司名称[：:]\s*([^\n\r]+)'
            name_match = re.search(name_pattern, text_content)
            if name_match:
                company_info['company_name'] = name_match.group(1).strip()
            
            # 股票代码
            code_pattern = r'股票代码[：:]\s*(\d+)'
            code_match = re.search(code_pattern, text_content)
            if code_match:
                company_info['stock_code'] = code_match.group(1)
            
            # 报告期间
            period_pattern = r'(\d{4})年度|(\d{4})年第[一二三四1234]季度|(\d{4})年半年度'
            period_match = re.search(period_pattern, text_content)
            if period_match:
                company_info['report_period'] = period_match.group(0)
            
            # 报告类型
            if '年度报告' in text_content or '年报' in text_content:
                company_info['report_type'] = '年报'
            elif '半年度报告' in text_content or '中报' in text_content:
                company_info['report_type'] = '中报'
            elif '第一季度报告' in text_content or '一季报' in text_content:
                company_info['report_type'] = '一季报'
            elif '第三季度报告' in text_content or '三季报' in text_content:
                company_info['report_type'] = '三季报'
            
            return company_info
            
        except Exception as e:
            print(f"提取公司信息失败: {e}")
            return {}
    
    def generate_analysis_summary(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成分析摘要
        
        Args:
            analysis_result (Dict[str, Any]): 分析结果
            
        Returns:
            Dict[str, Any]: 分析摘要
        """
        summary = {}
        
        try:
            # 提取公司信息
            company_info = self.extract_company_info(analysis_result['text_content'])
            summary['company_info'] = company_info
            
            # 表格统计
            tables = analysis_result['financial_tables']
            summary['tables_count'] = len(tables)
            summary['tables_found'] = list(tables.keys())
            
            # 指标统计
            indicators = analysis_result['key_indicators']
            summary['indicators_count'] = len(indicators)
            summary['indicators_found'] = list(indicators.keys())
            
            # 比率统计
            ratios = analysis_result['financial_ratios']
            summary['ratios_count'] = len(ratios)
            summary['ratios_calculated'] = list(ratios.keys())
            
            # 关键财务数据摘要
            if indicators:
                summary['key_figures'] = {
                    'revenue': indicators.get('revenue'),
                    'net_profit': indicators.get('net_profit'),
                    'total_assets': indicators.get('total_assets'),
                    'total_equity': indicators.get('total_equity')
                }
            
            # 关键比率摘要
            if ratios:
                summary['key_ratios'] = {
                    'current_ratio': ratios.get('current_ratio'),
                    'debt_ratio': ratios.get('debt_ratio'),
                    'roe': ratios.get('roe'),
                    'net_margin': ratios.get('net_margin')
                }
            
            return summary
            
        except Exception as e:
            print(f"生成分析摘要失败: {e}")
            return {'error': str(e)}
    
    def compare_financial_reports(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        比较多个财务报告
        
        Args:
            analysis_results (List[Dict[str, Any]]): 多个分析结果
            
        Returns:
            Dict[str, Any]: 比较结果
        """
        comparison = {}
        
        try:
            if len(analysis_results) < 2:
                return {'error': '需要至少2个财务报告进行比较'}
            
            # 提取各期间的关键指标
            periods_data = []
            for result in analysis_results:
                period_info = {
                    'period': result['summary'].get('company_info', {}).get('report_period', 'Unknown'),
                    'indicators': result['key_indicators'],
                    'ratios': result['financial_ratios']
                }
                periods_data.append(period_info)
            
            # 计算指标变化
            comparison['periods'] = periods_data
            comparison['changes'] = self._calculate_changes(periods_data)
            comparison['trends'] = self._analyze_trends(periods_data)
            
            return comparison
            
        except Exception as e:
            print(f"比较财务报告失败: {e}")
            return {'error': str(e)}
    
    def _calculate_changes(self, periods_data: List[Dict]) -> Dict[str, float]:
        """计算期间变化"""
        changes = {}
        
        if len(periods_data) >= 2:
            current = periods_data[-1]['indicators']
            previous = periods_data[-2]['indicators']
            
            for indicator in current:
                if indicator in previous and previous[indicator] != 0:
                    change_rate = (current[indicator] - previous[indicator]) / previous[indicator]
                    changes[f"{indicator}_change"] = change_rate
        
        return changes
    
    def _analyze_trends(self, periods_data: List[Dict]) -> Dict[str, str]:
        """分析趋势"""
        trends = {}
        
        # 简单趋势分析
        for indicator in ['revenue', 'net_profit', 'total_assets']:
            values = [period['indicators'].get(indicator) for period in periods_data 
                     if period['indicators'].get(indicator) is not None]
            
            if len(values) >= 2:
                if values[-1] > values[0]:
                    trends[indicator] = 'increasing'
                elif values[-1] < values[0]:
                    trends[indicator] = 'decreasing'
                else:
                    trends[indicator] = 'stable'
        
        return trends