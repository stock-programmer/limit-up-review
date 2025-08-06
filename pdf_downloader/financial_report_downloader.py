"""
财务报告PDF下载器
专门用于下载上市公司财务报告PDF文件
包括年报、中报、季报等
"""

import os
import requests
import tushare as ts
import pandas as pd
from typing import List, Optional, Dict, Tuple
from datetime import datetime
import time


class FinancialReportDownloader:
    """财务报告PDF下载器"""
    
    def __init__(self, download_dir: str = "downloads/financial_reports"):
        """
        初始化下载器
        
        Args:
            download_dir (str): PDF文件下载目录
        """
        self.download_dir = download_dir
        self.token = os.getenv('TUSHARE_TOKEN')
        
        if not self.token:
            print("警告：未找到TUSHARE_TOKEN环境变量")
        else:
            ts.set_token(self.token)
            self.pro = ts.pro_api()
        
        # 创建下载目录
        os.makedirs(download_dir, exist_ok=True)
        
        # 请求会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 财报类型映射
        self.report_types = {
            'annual': {'name': '年报', 'period_suffix': '1231'},
            'interim': {'name': '中报', 'period_suffix': '0630'},
            'q3': {'name': '三季报', 'period_suffix': '0930'},
            'q1': {'name': '一季报', 'period_suffix': '0331'}
        }
    
    def get_financial_periods(self, ts_code: str, start_year: int = None, 
                            end_year: int = None) -> List[Dict]:
        """
        获取财务报告期间列表
        
        Args:
            ts_code (str): 股票代码
            start_year (int): 开始年份
            end_year (int): 结束年份
            
        Returns:
            List[Dict]: 财务报告期间信息列表
        """
        try:
            if not start_year:
                start_year = datetime.now().year - 3  # 默认最近3年
            if not end_year:
                end_year = datetime.now().year
            
            periods = []
            
            for year in range(start_year, end_year + 1):
                for report_type, info in self.report_types.items():
                    period = f"{year}{info['period_suffix']}"
                    periods.append({
                        'ts_code': ts_code,
                        'period': period,
                        'year': year,
                        'report_type': report_type,
                        'report_name': info['name'],
                        'period_str': f"{year}年{info['name']}"
                    })
            
            return periods
            
        except Exception as e:
            print(f"获取财务期间失败: {e}")
            return []
    
    def get_financial_data_url(self, ts_code: str, period: str, report_type: str) -> str:
        """
        获取财务报告PDF的下载URL
        
        Args:
            ts_code (str): 股票代码
            period (str): 报告期，如 20241231
            report_type (str): 报告类型
            
        Returns:
            str: PDF下载URL，实际项目中需要对接真实的数据源
        """
        # 这里返回模拟URL，实际使用时需要对接真实的数据源
        # 例如：巨潮资讯网、上交所、深交所等官方网站
        
        base_urls = {
            'cninfo': 'http://www.cninfo.com.cn',  # 巨潮资讯网
            'sse': 'http://www.sse.com.cn',        # 上交所
            'szse': 'http://www.szse.cn'           # 深交所
        }
        
        # 模拟URL生成逻辑
        year = period[:4]
        exchange = 'sz' if ts_code.endswith('.SZ') else 'sh'
        
        mock_url = f"http://example-financial-reports.com/{exchange}/{ts_code}_{period}_{report_type}.pdf"
        
        return mock_url
    
    def download_financial_report(self, ts_code: str, period: str, 
                                report_type: str) -> str:
        """
        下载单个财务报告PDF
        
        Args:
            ts_code (str): 股票代码
            period (str): 报告期
            report_type (str): 报告类型
            
        Returns:
            str: 下载的文件路径，失败返回空字符串
        """
        try:
            # 生成文件名
            report_name = self.report_types.get(report_type, {}).get('name', report_type)
            filename = f"{ts_code}_{period}_{report_name}.pdf"
            file_path = os.path.join(self.download_dir, filename)
            
            # 检查文件是否已存在
            if os.path.exists(file_path):
                print(f"文件已存在: {filename}")
                return file_path
            
            # 获取下载URL
            pdf_url = self.get_financial_data_url(ts_code, period, report_type)
            
            print(f"正在下载 {ts_code} {period} {report_name}...")
            
            # 下载文件
            response = self.session.get(pdf_url, timeout=30)
            
            # 检查响应状态
            if response.status_code == 404:
                print(f"报告不存在: {filename}")
                return ""
            
            response.raise_for_status()
            
            # 检查内容类型
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower() and len(response.content) < 1000:
                print(f"下载的文件可能不是PDF: {filename}")
                return ""
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            print(f"下载完成: {filename}")
            return file_path
            
        except requests.exceptions.RequestException as e:
            print(f"网络请求失败: {e}")
            return ""
        except Exception as e:
            print(f"下载财务报告失败: {e}")
            return ""
    
    def download_annual_reports(self, ts_code: str, years: List[int]) -> List[str]:
        """
        批量下载年报
        
        Args:
            ts_code (str): 股票代码
            years (List[int]): 年份列表
            
        Returns:
            List[str]: 下载成功的文件路径列表
        """
        downloaded_files = []
        
        for year in years:
            period = f"{year}1231"
            file_path = self.download_financial_report(ts_code, period, 'annual')
            if file_path:
                downloaded_files.append(file_path)
            time.sleep(1)  # 避免频繁请求
        
        return downloaded_files
    
    def download_quarterly_reports(self, ts_code: str, year: int) -> List[str]:
        """
        下载指定年份的所有季报
        
        Args:
            ts_code (str): 股票代码
            year (int): 年份
            
        Returns:
            List[str]: 下载成功的文件路径列表
        """
        downloaded_files = []
        
        quarters = ['q1', 'interim', 'q3', 'annual']  # 一季报、中报、三季报、年报
        
        for quarter in quarters:
            period = f"{year}{self.report_types[quarter]['period_suffix']}"
            file_path = self.download_financial_report(ts_code, period, quarter)
            if file_path:
                downloaded_files.append(file_path)
            time.sleep(1)
        
        return downloaded_files
    
    def download_all_reports(self, ts_code: str, start_year: int = None, 
                           end_year: int = None) -> Dict[str, List[str]]:
        """
        下载所有财务报告
        
        Args:
            ts_code (str): 股票代码
            start_year (int): 开始年份
            end_year (int): 结束年份
            
        Returns:
            Dict[str, List[str]]: 按报告类型分组的下载文件路径
        """
        if not start_year:
            start_year = datetime.now().year - 2
        if not end_year:
            end_year = datetime.now().year
        
        result = {
            'annual': [],    # 年报
            'interim': [],   # 中报
            'q3': [],        # 三季报
            'q1': []         # 一季报
        }
        
        print(f"开始下载 {ts_code} {start_year}-{end_year} 年度财务报告...")
        
        for year in range(start_year, end_year + 1):
            for report_type in result.keys():
                period = f"{year}{self.report_types[report_type]['period_suffix']}"
                file_path = self.download_financial_report(ts_code, period, report_type)
                if file_path:
                    result[report_type].append(file_path)
                time.sleep(1)
        
        # 统计下载结果
        total_downloaded = sum(len(files) for files in result.values())
        print(f"下载完成，共成功下载 {total_downloaded} 个财务报告文件")
        
        return result
    
    def get_latest_reports(self, ts_code: str) -> Dict[str, str]:
        """
        获取最新的各类财务报告
        
        Args:
            ts_code (str): 股票代码
            
        Returns:
            Dict[str, str]: 最新报告的文件路径
        """
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        result = {}
        
        # 根据当前日期判断应该有哪些最新报告
        if current_month >= 4:  # 4月后一季报应该发布
            result['q1'] = self.download_financial_report(ts_code, f"{current_year}0331", 'q1')
        
        if current_month >= 8:  # 8月后中报应该发布
            result['interim'] = self.download_financial_report(ts_code, f"{current_year}0630", 'interim')
        
        if current_month >= 10:  # 10月后三季报应该发布
            result['q3'] = self.download_financial_report(ts_code, f"{current_year}0930", 'q3')
        
        # 上一年的年报
        prev_year = current_year - 1
        result['annual'] = self.download_financial_report(ts_code, f"{prev_year}1231", 'annual')
        
        return {k: v for k, v in result.items() if v}  # 过滤空值