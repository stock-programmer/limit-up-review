"""
PDF下载器包
用于获取股票公告和财报PDF文件
支持多种数据源：巨潮资讯网、tushare、交易所官网、第三方API等
"""

from .announcement_downloader import AnnouncementDownloader
from .financial_report_downloader import FinancialReportDownloader
from .cninfo_downloader import CninfoDownloader

__all__ = ['AnnouncementDownloader', 'FinancialReportDownloader', 'CninfoDownloader']