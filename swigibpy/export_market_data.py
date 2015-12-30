from wrapper_market_data import IBWrapper, IBclient
from swigibpy import Contract as IBcontract

from pandas.io import sql
import MySQLdb
import time
import datetime
import sys

def get_last_hist_data(client, symbol, startDate, endDate = datetime.datetime.now()):
    ibcontract = IBcontract()

    #ibcontract.secType = "FUT"
    #ibcontract.expiry="201809"
    #ibcontract.symbol="GE"
    #ibcontract.exchange="GLOBEX"
 
    ibcontract.secType = 'STK'
    ibcontract.exchange = 'SMART'
    ibcontract.currency = 'USD'
    ibcontract.primaryExchange = 'SMART'

    print("%s: %d-%s" % (endDate, index, symbol))
    ibcontract.symbol = symbol

    while (cmp(startDate, endDate) < 0):
        curDay = endDate + datetime.timedelta(days = -28)
        print curDay, endDate

        sdatetime=endDate.strftime("%Y%m%d %H:%M:%S %Z")
        ans=client.get_IB_historical_data(ibcontract, sdatetime, '4 W', '1 hour')

        endDate = curDay

    ans = ans.drop_duplicates(subset=['symbol', 'sdate'])
    #print ans
    #ans.to_csv("symbol.csv")
    #print ans
    #ans = ans.drop_duplicates(subset=['symbol', 'sdate'])

    conn=MySQLdb.connect(host='127.0.0.1',user='border',passwd='border', db='finance', port=3306)
    cur=conn.cursor()

    values=[]
    header = 'insert into stock_data_1hour(`symbol`, `sdate`, `open`, `high`, `low`, `close`, `volume`, `barcount`, `wap`, `hasgaps`, `ctime`) values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    for row in ans.iterrows():
        index, data = row
        values.append((data['symbol'], data['sdate'], data['open'], data['high'], data['low'],
                    data['close'], data['volume'], data['barcount'], data['wap'], data['hasgaps'], time.time()))
        #print 'Index: %s, symbol: %s, date: %s, close: %s' % (index, data['symbol'], data['sdate'], data['close'])

    cur.executemany(header, values)
    conn.commit()
    cur.close()
    conn.close()


def get_all_historical_data(start, end):
    '''
        Get Stock Historical Data
        start: start time, timeformat: %Y-%m-%d
        end:   end time, timeformat: %Y-%m-%d
    '''
    startDate = datetime.datetime.strptime(start, "%Y-%m-%d")    
    #endDate = datetime.datetime.strptime(end, "%Y-%m-%d")    
    endDate = datetime.datetime.now()

    callback = IBWrapper()
    client=IBclient(callback)

    symbols = ['SPY', 'QQQ', 'AAPL', 'FB', 'BIDU', 'RENN', 'FEYE', 'USO', 'ILMN']
    for index in range(len(symbols)):
        symbol = symbols[index]
        print("%s: %d-%s" % (endDate, index, symbol))
        get_last_hist_data(client, symbol, startDate)


if __name__=="__main__":

    """
    This simple example returns historical data
    """
    get_all_historical_data('2015-01-01', '2015-12-30')

