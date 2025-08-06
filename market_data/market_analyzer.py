"""
市场行情数据分析器
提供各种股票筛选和分析功能
"""

import tushare as ts
import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Optional, List


class MarketAnalyzer:
    """市场数据分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.token = os.getenv('TUSHARE_TOKEN')
        if not self.token:
            raise ValueError("未找到TUSHARE_TOKEN环境变量，请设置token")
        
        ts.set_token(self.token)
        self.pro = ts.pro_api()
        self._stock_basic = None
    
    def _get_stock_basic(self, force_refresh: bool = False) -> pd.DataFrame:
        """获取股票基本信息，带缓存"""
        if self._stock_basic is None or force_refresh:
            self._stock_basic = self.pro.stock_basic(exchange='', list_status='L')
        return self._stock_basic
    
    def get_daily_limit_up_stocks(self, trade_date: str) -> pd.DataFrame:
        """
        获取每日涨停股票
        
        Args:
            trade_date (str): 交易日期，格式为 YYYYMMDD
            
        Returns:
            pd.DataFrame: 涨停股票数据
        """
        try:
            # 获取当日行情数据
            daily_data = self.pro.daily(trade_date=trade_date)
            
            if daily_data is None or daily_data.empty:
                return pd.DataFrame()
            
            # 筛选涨停股票（涨幅大于等于9.5%）
            limit_up_stocks = daily_data[daily_data['pct_chg'] >= 9.5].copy()
            
            if limit_up_stocks.empty:
                return pd.DataFrame()
            
            # 合并股票名称
            stock_basic = self._get_stock_basic()
            result = limit_up_stocks.merge(
                stock_basic[['ts_code', 'name']], 
                on='ts_code', 
                how='left'
            )
            
            # 重新整理列
            result = result[['ts_code', 'name', 'close', 'pct_chg', 'vol', 'amount']].copy()
            result.columns = ['股票代码', '股票名称', '收盘价', '涨跌幅(%)', '成交量(手)', '成交额(千元)']
            
            return result.sort_values('涨跌幅(%)', ascending=False)
            
        except Exception as e:
            print(f"获取涨停股票数据失败: {e}")
            return pd.DataFrame()
    
    def get_high_volume_high_gain_stocks(self, trade_date: str, min_amount: float = 400000) -> pd.DataFrame:
        """
        获取每日成交金额大于指定值且涨幅大于5%的股票
        
        Args:
            trade_date (str): 交易日期，格式为 YYYYMMDD
            min_amount (float): 最小成交金额（千元），默认400000（4亿）
            
        Returns:
            pd.DataFrame: 符合条件的股票数据
        """
        try:
            daily_data = self.pro.daily(trade_date=trade_date)
            
            if daily_data is None or daily_data.empty:
                return pd.DataFrame()
            
            # 筛选条件：成交金额>4亿且涨幅>5%
            filtered_stocks = daily_data[
                (daily_data['amount'] > min_amount) & 
                (daily_data['pct_chg'] > 5.0)
            ].copy()
            
            if filtered_stocks.empty:
                return pd.DataFrame()
            
            # 合并股票名称
            stock_basic = self._get_stock_basic()
            result = filtered_stocks.merge(
                stock_basic[['ts_code', 'name']], 
                on='ts_code', 
                how='left'
            )
            
            result = result[['ts_code', 'name', 'close', 'pct_chg', 'vol', 'amount']].copy()
            result.columns = ['股票代码', '股票名称', '收盘价', '涨跌幅(%)', '成交量(手)', '成交额(千元)']
            
            return result.sort_values('涨跌幅(%)', ascending=False)
            
        except Exception as e:
            print(f"获取高成交额高涨幅股票数据失败: {e}")
            return pd.DataFrame()
    
    def get_high_volume_limit_up_stocks(self, trade_date: str, min_amount: float = 400000) -> pd.DataFrame:
        """
        获取每日成交金额大于指定值且涨停的股票
        
        Args:
            trade_date (str): 交易日期，格式为 YYYYMMDD
            min_amount (float): 最小成交金额（千元），默认400000（4亿）
            
        Returns:
            pd.DataFrame: 符合条件的股票数据
        """
        try:
            daily_data = self.pro.daily(trade_date=trade_date)
            
            if daily_data is None or daily_data.empty:
                return pd.DataFrame()
            
            # 筛选条件：成交金额>4亿且涨停（涨幅>=9.5%）
            filtered_stocks = daily_data[
                (daily_data['amount'] > min_amount) & 
                (daily_data['pct_chg'] >= 9.5)
            ].copy()
            
            if filtered_stocks.empty:
                return pd.DataFrame()
            
            # 合并股票名称
            stock_basic = self._get_stock_basic()
            result = filtered_stocks.merge(
                stock_basic[['ts_code', 'name']], 
                on='ts_code', 
                how='left'
            )
            
            result = result[['ts_code', 'name', 'close', 'pct_chg', 'vol', 'amount']].copy()
            result.columns = ['股票代码', '股票名称', '收盘价', '涨跌幅(%)', '成交量(手)', '成交额(千元)']
            
            return result.sort_values('涨跌幅(%)', ascending=False)
            
        except Exception as e:
            print(f"获取高成交额涨停股票数据失败: {e}")
            return pd.DataFrame()
    
    def _calculate_period_return(self, days: int, end_date: str) -> pd.DataFrame:
        """
        计算指定期间的股票涨幅排名
        
        Args:
            days (int): 统计天数
            end_date (str): 结束日期，格式为 YYYYMMDD
            
        Returns:
            pd.DataFrame: 期间涨幅排名数据
        """
        try:
            # 计算开始日期（交易日历）
            cal = self.pro.trade_cal(start_date=end_date, end_date=end_date)
            if cal.empty or cal.iloc[0]['is_open'] != 1:
                print(f"{end_date} 非交易日")
                return pd.DataFrame()
            
            # 获取交易日历，找到开始日期
            start_date_obj = datetime.strptime(end_date, '%Y%m%d') - timedelta(days=days*2)  # 预留足够天数
            start_date_str = start_date_obj.strftime('%Y%m%d')
            
            trade_cal = self.pro.trade_cal(start_date=start_date_str, end_date=end_date)
            trade_days = trade_cal[trade_cal['is_open'] == 1]['cal_date'].tolist()
            
            if len(trade_days) < days + 1:
                print(f"交易日不足{days + 1}天")
                return pd.DataFrame()
            
            start_trade_date = trade_days[-(days + 1)]  # 开始交易日
            end_trade_date = trade_days[-1]  # 结束交易日
            
            # 获取开始日期和结束日期的行情数据
            start_data = self.pro.daily(trade_date=start_trade_date)
            end_data = self.pro.daily(trade_date=end_trade_date)
            
            if start_data.empty or end_data.empty:
                return pd.DataFrame()
            
            # 计算期间涨幅
            merged_data = start_data.merge(
                end_data, 
                on='ts_code', 
                suffixes=('_start', '_end')
            )
            
            merged_data['period_return'] = (
                (merged_data['close_end'] - merged_data['close_start']) / 
                merged_data['close_start'] * 100
            )
            
            # 合并股票名称
            stock_basic = self._get_stock_basic()
            result = merged_data.merge(
                stock_basic[['ts_code', 'name']], 
                on='ts_code', 
                how='left'
            )
            
            result = result[['ts_code', 'name', 'close_start', 'close_end', 'period_return']].copy()
            result.columns = ['股票代码', '股票名称', f'{days}日前收盘价', '最新收盘价', f'{days}日涨幅(%)']
            
            return result.sort_values(f'{days}日涨幅(%)', ascending=False)
            
        except Exception as e:
            print(f"计算{days}日期间涨幅失败: {e}")
            return pd.DataFrame()
    
    def get_5day_return_ranking(self, end_date: str) -> pd.DataFrame:
        """获取近5日A股涨幅排名"""
        return self._calculate_period_return(5, end_date)
    
    def get_10day_return_ranking(self, end_date: str) -> pd.DataFrame:
        """获取近10日A股涨幅排名"""
        return self._calculate_period_return(10, end_date)
    
    def get_20day_return_ranking(self, end_date: str) -> pd.DataFrame:
        """获取近20日A股涨幅排名"""
        return self._calculate_period_return(20, end_date)
    
    def get_ytd_return_ranking(self, end_date: str) -> pd.DataFrame:
        """
        获取当年股票涨幅排行
        
        Args:
            end_date (str): 结束日期，格式为 YYYYMMDD
            
        Returns:
            pd.DataFrame: 当年涨幅排行数据
        """
        try:
            year = end_date[:4]
            start_date = f"{year}0101"
            
            # 获取当年第一个交易日
            trade_cal = self.pro.trade_cal(start_date=start_date, end_date=f"{year}0131")
            first_trade_day = trade_cal[trade_cal['is_open'] == 1]['cal_date'].iloc[0]
            
            # 获取年初和当前的行情数据
            start_data = self.pro.daily(trade_date=first_trade_day)
            end_data = self.pro.daily(trade_date=end_date)
            
            if start_data.empty or end_data.empty:
                return pd.DataFrame()
            
            # 计算年度涨幅
            merged_data = start_data.merge(
                end_data, 
                on='ts_code', 
                suffixes=('_start', '_end')
            )
            
            merged_data['ytd_return'] = (
                (merged_data['close_end'] - merged_data['close_start']) / 
                merged_data['close_start'] * 100
            )
            
            # 合并股票名称
            stock_basic = self._get_stock_basic()
            result = merged_data.merge(
                stock_basic[['ts_code', 'name']], 
                on='ts_code', 
                how='left'
            )
            
            result = result[['ts_code', 'name', 'close_start', 'close_end', 'ytd_return']].copy()
            result.columns = ['股票代码', '股票名称', '年初收盘价', '最新收盘价', '年度涨幅(%)']
            
            return result.sort_values('年度涨幅(%)', ascending=False)
            
        except Exception as e:
            print(f"获取年度涨幅排行失败: {e}")
            return pd.DataFrame()
    
    def get_high_volume_high_decline_stocks(self, trade_date: str, min_amount: float = 400000) -> pd.DataFrame:
        """
        获取每日成交金额大于指定值且跌幅大于5%的股票
        
        Args:
            trade_date (str): 交易日期，格式为 YYYYMMDD
            min_amount (float): 最小成交金额（千元），默认400000（4亿）
            
        Returns:
            pd.DataFrame: 符合条件的股票数据
        """
        try:
            daily_data = self.pro.daily(trade_date=trade_date)
            
            if daily_data is None or daily_data.empty:
                return pd.DataFrame()
            
            # 筛选条件：成交金额>4亿且跌幅>5%
            filtered_stocks = daily_data[
                (daily_data['amount'] > min_amount) & 
                (daily_data['pct_chg'] < -5.0)
            ].copy()
            
            if filtered_stocks.empty:
                return pd.DataFrame()
            
            # 合并股票名称
            stock_basic = self._get_stock_basic()
            result = filtered_stocks.merge(
                stock_basic[['ts_code', 'name']], 
                on='ts_code', 
                how='left'
            )
            
            result = result[['ts_code', 'name', 'close', 'pct_chg', 'vol', 'amount']].copy()
            result.columns = ['股票代码', '股票名称', '收盘价', '涨跌幅(%)', '成交量(手)', '成交额(千元)']
            
            return result.sort_values('涨跌幅(%)', ascending=True)  # 按跌幅从大到小排序
            
        except Exception as e:
            print(f"获取高成交额高跌幅股票数据失败: {e}")
            return pd.DataFrame()
    
    def get_new_high_large_cap_stocks(self, trade_date: str, min_market_cap: float = 30000000) -> pd.DataFrame:
        """
        获取每日新高且市值大于指定值的股票，按市值排序
        
        Args:
            trade_date (str): 交易日期，格式为 YYYYMMDD
            min_market_cap (float): 最小市值（万元），默认30000000（300亿）
            
        Returns:
            pd.DataFrame: 符合条件的股票数据
        """
        try:
            # 获取当日行情数据
            daily_data = self.pro.daily(trade_date=trade_date)
            
            if daily_data is None or daily_data.empty:
                return pd.DataFrame()
            
            # 获取前一个交易日
            trade_cal = self.pro.trade_cal(start_date=trade_date, end_date=trade_date)
            if trade_cal.empty or trade_cal.iloc[0]['is_open'] != 1:
                return pd.DataFrame()
            
            # 获取过去60个交易日的数据来判断是否创新高
            end_date_obj = datetime.strptime(trade_date, '%Y%m%d')
            start_date_obj = end_date_obj - timedelta(days=120)  # 预留足够天数
            start_date = start_date_obj.strftime('%Y%m%d')
            
            # 获取历史最高价数据（简化处理，使用过去60日最高价）
            hist_cal = self.pro.trade_cal(start_date=start_date, end_date=trade_date)
            hist_trade_days = hist_cal[hist_cal['is_open'] == 1]['cal_date'].tolist()[-60:]  # 最近60个交易日
            
            # 获取这些交易日的历史最高价
            all_hist_data = []
            for date in hist_trade_days[:-1]:  # 排除当日
                hist_data = self.pro.daily(trade_date=date)
                if not hist_data.empty:
                    all_hist_data.append(hist_data[['ts_code', 'high']])
            
            if not all_hist_data:
                return pd.DataFrame()
            
            # 计算历史最高价
            hist_combined = pd.concat(all_hist_data)
            hist_max = hist_combined.groupby('ts_code')['high'].max().reset_index()
            hist_max.columns = ['ts_code', 'hist_high']
            
            # 合并当日数据和历史最高价
            merged_data = daily_data.merge(hist_max, on='ts_code', how='inner')
            
            # 筛选创新高的股票（当日最高价 >= 历史最高价）
            new_high_stocks = merged_data[merged_data['high'] >= merged_data['hist_high']].copy()
            
            if new_high_stocks.empty:
                return pd.DataFrame()
            
            # 获取市值数据
            try:
                daily_basic = self.pro.daily_basic(trade_date=trade_date)
                if daily_basic.empty:
                    return pd.DataFrame()
                
                # 合并市值数据
                result = new_high_stocks.merge(
                    daily_basic[['ts_code', 'total_mv']], 
                    on='ts_code', 
                    how='inner'
                )
                
                # 筛选大市值股票
                result = result[result['total_mv'] > min_market_cap].copy()
                
                if result.empty:
                    return pd.DataFrame()
                
                # 合并股票名称
                stock_basic = self._get_stock_basic()
                result = result.merge(
                    stock_basic[['ts_code', 'name']], 
                    on='ts_code', 
                    how='left'
                )
                
                result = result[['ts_code', 'name', 'close', 'high', 'hist_high', 'total_mv']].copy()
                result.columns = ['股票代码', '股票名称', '收盘价', '当日最高价', '历史最高价', '总市值(万元)']
                
                return result.sort_values('总市值(万元)', ascending=False)
                
            except Exception as e:
                print(f"获取市值数据失败: {e}")
                return pd.DataFrame()
            
        except Exception as e:
            print(f"获取新高大市值股票数据失败: {e}")
            return pd.DataFrame()