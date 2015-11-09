#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyalgotrade.tools import yahoofinance

# ETF'
instruments_etf = ['QQQ', 'SPY', 'USO', 'UWTI', 'DWTI', 'IBB', 'IWM', 'XLF']

# 能源 energy'
instruments_energy = ['CSIQ', 'CLB', 'COP', 'SCTY', 'XOM', 'PSX', 'JKS', 'NOV', 'DO', 'BP',
                      'AA', 'SU']

# 生物 Biotechnology'
instruments_bio = ['BIIB', 'VBLT', 'CELG', 'GILD', 'JUNO', 'ILMN', 'NVTA', 'RMTI', 'HTBX', 'SNSS',
                   'OPK', 'MNKD', 'ESPR', 'EYES', 'SGMO', 'BLCM', 'AAVL', 'OVAS', 'DXCM', 'NLNK',
                   'GENE', 'TKMR', 'ISIS', 'KITE']

# 中概 China'
instruments_china = ['WBAI', 'YY', 'BABA', 'QIHU', 'BIDU', 'JD', 'JMEI']

# 科技 Technology'
instruments_tech = ['AAPL', 'FB', 'TWTR', 'GPRO', 'TSLA', 'TRUE', 'MSFT', 'YELP', 'LC', 'W',
                    'FEYE', 'HIMX', 'TRUE', 'CYBR', 'AMBA']

# 金融 financial'
instruments_fin = ['C', 'BAC', 'WFC', 'IBKR']

# 其他 other'
instruments_other = ['HABT', 'VA', 'S', 'SHAK', 'LOCO']

instruments = instruments_etf + instruments_energy + instruments_bio + instruments_china \
              + instruments_tech + instruments_fin + instruments_other

print('Stock Count: %d' % len(instruments))
print(instruments)

feed = yahoofinance.build_feed(instruments, 2000, 2015, '../data', skipErrors=True)

