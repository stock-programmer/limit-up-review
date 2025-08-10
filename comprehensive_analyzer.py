#!/usr/bin/env python3
"""
涨停股票综合分析器
整合行情数据、财报分析、公告信息的一站式分析工具
"""

import os
import pandas as pd
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time

from market_data import MarketAnalyzer
from pdf_downloader import CninfoDownloader
from llm_pdf_processor import FinancialReportAnalyzer


class ComprehensiveStockAnalyzer:
    """涨停股票综合分析器"""
    
    def __init__(self, output_dir: str = "analysis_output"):
        """
        初始化综合分析器
        
        Args:
            output_dir (str): 分析结果输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化各个分析器
        self.market_analyzer = MarketAnalyzer()
        self.pdf_downloader = CninfoDownloader()
        self.financial_analyzer = FinancialReportAnalyzer()
        
        # 利好消息关键词
        self.positive_keywords = [
            '中标', '签约', '合作', '收购', '增资', '扩产', '新品', '专利',
            '政策支持', '补贴', '奖励', '业绩预增', '分红', '股权激励',
            '重组', '资产注入', '战略合作', '技术突破'
        ]
    
    def analyze_limit_up_stocks(self, trade_date: str, max_stocks: int = 20) -> Dict[str, Any]:
        """
        分析指定日期的涨停股票
        
        Args:
            trade_date (str): 交易日期 YYYYMMDD
            max_stocks (int): 最大分析股票数量
            
        Returns:
            Dict[str, Any]: 综合分析结果
        """
        print(f"=== 开始分析 {trade_date} 涨停股票 ===")
        
        analysis_result = {
            'trade_date': trade_date,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'limit_up_stocks': [],
            'summary': {},
            'industry_analysis': {},
            'announcement_themes': []
        }
        
        try:
            # 1. 获取涨停股票列表
            print("\n1. 获取涨停股票列表...")
            limit_up_data = self.market_analyzer.get_daily_limit_up_stocks(trade_date)
            
            if limit_up_data.empty:
                print(f"{trade_date} 无涨停股票")
                return analysis_result
            
            print(f"找到 {len(limit_up_data)} 只涨停股票")
            
            # 限制分析数量
            stocks_to_analyze = limit_up_data.head(max_stocks)
            
            # 2. 逐只股票进行详细分析
            for idx, (_, stock_row) in enumerate(stocks_to_analyze.iterrows(), 1):
                stock_code = stock_row['股票代码'].replace('.SZ', '').replace('.SH', '')
                stock_name = stock_row['股票名称']
                
                print(f"\n=== 分析第 {idx}/{len(stocks_to_analyze)} 只股票: {stock_code} {stock_name} ===")
                
                stock_analysis = self._analyze_single_stock(
                    stock_code, stock_name, stock_row, trade_date
                )
                
                analysis_result['limit_up_stocks'].append(stock_analysis)
                
                # 添加延迟避免请求过频
                time.sleep(2)
            
            # 3. 生成汇总分析
            analysis_result['summary'] = self._generate_summary(analysis_result['limit_up_stocks'])
            analysis_result['industry_analysis'] = self._analyze_industries(analysis_result['limit_up_stocks'])
            analysis_result['announcement_themes'] = self._analyze_announcement_themes(analysis_result['limit_up_stocks'])
            
            # 4. 保存分析结果
            self._save_analysis_result(analysis_result)
            
            print(f"\n=== 分析完成，共分析 {len(analysis_result['limit_up_stocks'])} 只股票 ===")
            return analysis_result
            
        except Exception as e:
            print(f"综合分析失败: {e}")
            analysis_result['error'] = str(e)
            return analysis_result
    
    def _analyze_single_stock(self, stock_code: str, stock_name: str, 
                            stock_row: pd.Series, trade_date: str) -> Dict[str, Any]:
        """
        分析单只股票的详细信息
        
        Args:
            stock_code (str): 股票代码
            stock_name (str): 股票名称  
            stock_row (pd.Series): 股票行情数据
            trade_date (str): 交易日期
            
        Returns:
            Dict[str, Any]: 单只股票分析结果
        """
        stock_analysis = {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'market_data': {
                'close_price': stock_row.get('收盘价', 0),
                'change_pct': stock_row.get('涨跌幅(%)', 0),
                'volume': stock_row.get('成交量(手)', 0),
                'amount': stock_row.get('成交额(千元)', 0)
            },
            'business_info': {},
            'financial_data': {},
            'recent_announcements': [],
            'analysis_insights': {}
        }
        
        try:
            # 1. 获取财报信息
            print(f"  获取 {stock_code} 财报信息...")
            financial_info = self._get_financial_info(stock_code)
            stock_analysis['business_info'] = financial_info.get('business_info', {})
            stock_analysis['financial_data'] = financial_info.get('financial_data', {})
            
            # 2. 获取最近公告
            print(f"  获取 {stock_code} 最近公告...")
            recent_announcements = self._get_recent_announcements(stock_code, trade_date)
            stock_analysis['recent_announcements'] = recent_announcements
            
            # 3. 分析涨停原因
            print(f"  分析 {stock_code} 涨停原因...")
            insights = self._analyze_limit_up_reasons(
                stock_analysis['recent_announcements'],
                stock_analysis['business_info'],
                trade_date
            )
            stock_analysis['analysis_insights'] = insights
            
            return stock_analysis
            
        except Exception as e:
            print(f"分析股票 {stock_code} 失败: {e}")
            stock_analysis['error'] = str(e)
            return stock_analysis
    
    def _get_financial_info(self, stock_code: str) -> Dict[str, Any]:
        """
        获取股票财务信息（使用LLM分析）
        
        Args:
            stock_code (str): 股票代码
            
        Returns:
            Dict[str, Any]: 财务信息
        """
        financial_info = {
            'business_info': {},
            'financial_data': {}
        }
        
        try:
            # 下载最新财务报告
            current_year = datetime.now().year
            financial_files = self.pdf_downloader.download_financial_reports(
                stock_code, current_year, ['annual_report', 'interim_report']
            )
            
            if not financial_files:
                # 如果当年没有，尝试上一年
                financial_files = self.pdf_downloader.download_financial_reports(
                    stock_code, current_year - 1, ['annual_report']
                )
            
            if financial_files:
                # 使用LLM分析最新的财务报告
                latest_report = financial_files[0]
                print(f"  使用LLM分析财务报告: {os.path.basename(latest_report)}")
                
                # 使用LLM分析财务报告
                analysis_result = self.financial_analyzer.analyze_financial_report(latest_report)
                
                if analysis_result['success']:
                    # 提取主营业务信息
                    business_info = self.financial_analyzer.extract_business_info(analysis_result)
                    financial_info['business_info'] = business_info
                    
                    # 提取财务数据
                    financial_data = self.financial_analyzer.extract_financial_data(analysis_result)
                    financial_info['financial_data'] = financial_data
                    
                    print(f"  LLM分析完成: 提取到 {len(business_info)} 项业务信息，{len(financial_data.get('key_indicators', {}))} 项财务指标")
                else:
                    print(f"  LLM分析失败: {analysis_result.get('error', '未知错误')}")
                    # 降级到简单方法（如果需要的话）
                    financial_info['business_info'] = self._fallback_business_extraction(latest_report)
            
            return financial_info
            
        except Exception as e:
            print(f"获取 {stock_code} 财务信息失败: {e}")
            return financial_info
    
    def _fallback_business_extraction(self, pdf_path: str) -> Dict[str, str]:
        """
        降级方法：简单提取主营业务信息
        
        Args:
            pdf_path (str): PDF文件路径
            
        Returns:
            Dict[str, str]: 主营业务信息
        """
        business_info = {}
        
        try:
            # 使用简单的PDF文本提取
            from llm_pdf_processor import PDFTextConverter
            converter = PDFTextConverter()
            text_content = converter.extract_text_from_pdf(pdf_path)
            
            # 简单的业务信息提取
            if '是一家' in text_content and '专注于' in text_content:
                match = re.search(r'([^。]*是一家[^。]*专注于[^。]*[。])', text_content)
                if match:
                    business_info['main_business'] = match.group(1).strip()
            
            # 简单的行业提取
            industry_match = re.search(r'所属行业[：:]\s*([^\n。]{1,50})', text_content)
            if industry_match:
                business_info['industry'] = industry_match.group(1).strip()
            
            return business_info
            
        except Exception as e:
            print(f"降级业务信息提取失败: {e}")
            return {}
    
    def _get_recent_announcements(self, stock_code: str, trade_date: str, days: int = 30) -> List[Dict]:
        """
        获取最近的公告信息
        
        Args:
            stock_code (str): 股票代码
            trade_date (str): 交易日期
            days (int): 查询天数
            
        Returns:
            List[Dict]: 公告列表
        """
        try:
            # 计算查询日期范围
            end_date = datetime.strptime(trade_date, '%Y%m%d')
            start_date = end_date - timedelta(days=days)
            
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            # 查询公告
            announcements, _ = self.pdf_downloader.query_announcements(
                stock_code, start_date_str, end_date_str, page_size=10
            )
            
            # 处理公告数据
            processed_announcements = []
            for ann in announcements[:5]:  # 只取最近5条
                processed_ann = {
                    'title': ann.get('title', ''),
                    'date': ann.get('announcementTime', ''),
                    'type': self._classify_announcement_type(ann.get('title', '')),
                    'is_positive': self._is_positive_announcement(ann.get('title', ''))
                }
                processed_announcements.append(processed_ann)
            
            return processed_announcements
            
        except Exception as e:
            print(f"获取 {stock_code} 公告失败: {e}")
            return []
    
    def _classify_announcement_type(self, title: str) -> str:
        """
        分类公告类型
        
        Args:
            title (str): 公告标题
            
        Returns:
            str: 公告类型
        """
        if any(keyword in title for keyword in ['年报', '季报', '中报', '财务']):
            return '财务报告'
        elif any(keyword in title for keyword in ['董事会', '股东大会', '决议']):
            return '治理公告'
        elif any(keyword in title for keyword in ['中标', '合同', '签约']):
            return '业务公告'
        elif any(keyword in title for keyword in ['投资', '收购', '增资', '重组']):
            return '投资公告'
        elif any(keyword in title for keyword in ['业绩', '预告', '修正']):
            return '业绩公告'
        else:
            return '其他公告'
    
    def _is_positive_announcement(self, title: str) -> bool:
        """
        判断是否为利好公告
        
        Args:
            title (str): 公告标题
            
        Returns:
            bool: 是否利好
        """
        return any(keyword in title for keyword in self.positive_keywords)
    
    def _analyze_limit_up_reasons(self, announcements: List[Dict], 
                                business_info: Dict, trade_date: str) -> Dict[str, Any]:
        """
        分析涨停原因
        
        Args:
            announcements (List[Dict]): 公告列表
            business_info (Dict): 主营业务信息
            trade_date (str): 交易日期
            
        Returns:
            Dict[str, Any]: 分析见解
        """
        insights = {
            'possible_reasons': [],
            'announcement_correlation': False,
            'positive_news_count': 0,
            'recent_events': []
        }
        
        try:
            # 统计利好公告数量
            positive_count = sum(1 for ann in announcements if ann['is_positive'])
            insights['positive_news_count'] = positive_count
            
            # 分析公告与涨停的关联性
            recent_positive = [ann for ann in announcements[:3] if ann['is_positive']]
            if recent_positive:
                insights['announcement_correlation'] = True
                insights['possible_reasons'].append('近期有利好公告发布')
                
                for ann in recent_positive:
                    insights['recent_events'].append({
                        'event': ann['title'],
                        'date': ann['date'],
                        'type': ann['type']
                    })
            
            # 根据公告类型分析可能原因
            announcement_types = [ann['type'] for ann in announcements]
            
            if '业务公告' in announcement_types:
                insights['possible_reasons'].append('业务拓展或重大合同')
            
            if '投资公告' in announcement_types:
                insights['possible_reasons'].append('投资并购活动')
            
            if '业绩公告' in announcement_types:
                insights['possible_reasons'].append('业绩超预期')
            
            # 如果没有明显利好，可能是题材炒作
            if positive_count == 0:
                insights['possible_reasons'].append('可能为题材炒作或跟风上涨')
            
            return insights
            
        except Exception as e:
            print(f"分析涨停原因失败: {e}")
            return insights
    
    def _generate_summary(self, stock_analyses: List[Dict]) -> Dict[str, Any]:
        """
        生成汇总分析
        
        Args:
            stock_analyses (List[Dict]): 股票分析结果列表
            
        Returns:
            Dict[str, Any]: 汇总信息
        """
        summary = {
            'total_stocks': len(stock_analyses),
            'avg_change_pct': 0,
            'total_amount': 0,
            'with_positive_news': 0,
            'business_correlation': 0
        }
        
        try:
            if not stock_analyses:
                return summary
            
            # 计算统计数据
            total_change = sum(s['market_data'].get('change_pct', 0) for s in stock_analyses)
            total_amount = sum(s['market_data'].get('amount', 0) for s in stock_analyses)
            positive_news_count = sum(1 for s in stock_analyses 
                                    if s['analysis_insights'].get('positive_news_count', 0) > 0)
            
            summary['avg_change_pct'] = round(total_change / len(stock_analyses), 2)
            summary['total_amount'] = total_amount
            summary['with_positive_news'] = positive_news_count
            summary['business_correlation'] = round(positive_news_count / len(stock_analyses) * 100, 1)
            
            return summary
            
        except Exception as e:
            print(f"生成汇总失败: {e}")
            return summary
    
    def _analyze_industries(self, stock_analyses: List[Dict]) -> Dict[str, int]:
        """
        分析涨停股票的行业分布
        
        Args:
            stock_analyses (List[Dict]): 股票分析结果列表
            
        Returns:
            Dict[str, int]: 行业分布统计
        """
        industry_count = {}
        
        try:
            for analysis in stock_analyses:
                industry = analysis['business_info'].get('industry', '未知行业')
                industry_count[industry] = industry_count.get(industry, 0) + 1
            
            # 按数量排序
            sorted_industries = dict(sorted(industry_count.items(), 
                                          key=lambda x: x[1], reverse=True))
            
            return sorted_industries
            
        except Exception as e:
            print(f"行业分析失败: {e}")
            return {}
    
    def _analyze_announcement_themes(self, stock_analyses: List[Dict]) -> List[Dict]:
        """
        分析公告主题
        
        Args:
            stock_analyses (List[Dict]): 股票分析结果列表
            
        Returns:
            List[Dict]: 主题分析结果
        """
        themes = {}
        
        try:
            for analysis in stock_analyses:
                for event in analysis['analysis_insights'].get('recent_events', []):
                    event_type = event['type']
                    themes[event_type] = themes.get(event_type, 0) + 1
            
            # 转换为列表格式
            theme_list = [{'theme': k, 'count': v} for k, v in themes.items()]
            theme_list.sort(key=lambda x: x['count'], reverse=True)
            
            return theme_list
            
        except Exception as e:
            print(f"主题分析失败: {e}")
            return []
    
    def _save_analysis_result(self, analysis_result: Dict[str, Any]):
        """
        保存分析结果
        
        Args:
            analysis_result (Dict[str, Any]): 分析结果
        """
        try:
            trade_date = analysis_result['trade_date']
            
            # 保存为JSON格式
            import json
            json_file = os.path.join(self.output_dir, f"limit_up_analysis_{trade_date}.json")
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            
            # 生成Excel报告
            self._generate_excel_report(analysis_result)
            
            print(f"分析结果已保存到: {json_file}")
            
        except Exception as e:
            print(f"保存分析结果失败: {e}")
    
    def _generate_excel_report(self, analysis_result: Dict[str, Any]):
        """
        生成Excel分析报告
        
        Args:
            analysis_result (Dict[str, Any]): 分析结果
        """
        try:
            trade_date = analysis_result['trade_date']
            excel_file = os.path.join(self.output_dir, f"limit_up_report_{trade_date}.xlsx")
            
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                # 股票详情页
                stock_details = []
                for stock in analysis_result['limit_up_stocks']:
                    detail = {
                        '股票代码': stock['stock_code'],
                        '股票名称': stock['stock_name'],
                        '收盘价': stock['market_data'].get('close_price', 0),
                        '涨跌幅(%)': stock['market_data'].get('change_pct', 0),
                        '成交额(千元)': stock['market_data'].get('amount', 0),
                        '主营业务': stock['business_info'].get('main_business', '')[:100],
                        '所属行业': stock['business_info'].get('industry', ''),
                        '利好公告数': stock['analysis_insights'].get('positive_news_count', 0),
                        '可能原因': '; '.join(stock['analysis_insights'].get('possible_reasons', []))
                    }
                    stock_details.append(detail)
                
                df_details = pd.DataFrame(stock_details)
                df_details.to_excel(writer, sheet_name='股票详情', index=False)
                
                # 汇总统计页
                summary_data = []
                summary = analysis_result['summary']
                summary_data.append(['涨停股票总数', summary.get('total_stocks', 0)])
                summary_data.append(['平均涨幅(%)', summary.get('avg_change_pct', 0)])
                summary_data.append(['总成交额(千元)', summary.get('total_amount', 0)])
                summary_data.append(['有利好消息股票数', summary.get('with_positive_news', 0)])
                summary_data.append(['利好关联度(%)', summary.get('business_correlation', 0)])
                
                df_summary = pd.DataFrame(summary_data, columns=['指标', '数值'])
                df_summary.to_excel(writer, sheet_name='汇总统计', index=False)
                
                # 行业分布页
                industry_data = list(analysis_result['industry_analysis'].items())
                if industry_data:
                    df_industry = pd.DataFrame(industry_data, columns=['行业', '股票数量'])
                    df_industry.to_excel(writer, sheet_name='行业分布', index=False)
            
            print(f"Excel报告已生成: {excel_file}")
            
        except Exception as e:
            print(f"生成Excel报告失败: {e}")
    
    def print_analysis_summary(self, analysis_result: Dict[str, Any]):
        """
        打印分析摘要
        
        Args:
            analysis_result (Dict[str, Any]): 分析结果
        """
        print(f"\n{'='*80}")
        print(f"  {analysis_result['trade_date']} 涨停股票综合分析报告")
        print(f"{'='*80}")
        
        summary = analysis_result['summary']
        print(f"📊 基本统计:")
        print(f"   涨停股票总数: {summary.get('total_stocks', 0)} 只")
        print(f"   平均涨幅: {summary.get('avg_change_pct', 0)}%")
        print(f"   总成交额: {summary.get('total_amount', 0):,.0f} 千元")
        print(f"   有利好消息: {summary.get('with_positive_news', 0)} 只 ({summary.get('business_correlation', 0)}%)")
        
        # 行业分布
        print(f"\n🏭 行业分布:")
        industry_analysis = analysis_result['industry_analysis']
        for industry, count in list(industry_analysis.items())[:5]:
            print(f"   {industry}: {count} 只")
        
        # 主要股票详情
        print(f"\n📈 主要涨停股票:")
        for i, stock in enumerate(analysis_result['limit_up_stocks'][:5], 1):
            print(f"   {i}. {stock['stock_code']} {stock['stock_name']}")
            print(f"      涨幅: {stock['market_data'].get('change_pct', 0)}% | "
                  f"成交额: {stock['market_data'].get('amount', 0):,.0f}千元")
            
            business = stock['business_info'].get('main_business', '信息获取中...')
            if len(business) > 60:
                business = business[:60] + "..."
            print(f"      主营: {business}")
            
            reasons = stock['analysis_insights'].get('possible_reasons', [])
            if reasons:
                print(f"      原因: {'; '.join(reasons[:2])}")
            print()
        
        print(f"{'='*80}")


def main():
    """主函数 - 示例用法"""
    analyzer = ComprehensiveStockAnalyzer()
    
    # 分析指定日期的涨停股票
    trade_date = "20241220"  # 示例日期，您可以修改
    result = analyzer.analyze_limit_up_stocks(trade_date, max_stocks=5)
    
    # 打印分析摘要
    analyzer.print_analysis_summary(result)

if __name__ == "__main__":
    main()