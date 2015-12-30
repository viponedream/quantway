from wrapper_market_data import IBWrapper, IBclient
from swigibpy import Contract as IBcontract

from pandas.io import sql
import MySQLdb
import time
import datetime
import sys

def get_last_hist_data(endDate):
    callback = IBWrapper()
    client=IBclient(callback)

    ibcontract = IBcontract()

    #ibcontract.secType = "FUT"
    #ibcontract.expiry="201809"
    #ibcontract.symbol="GE"
    #ibcontract.exchange="GLOBEX"

    symbols = ['AAPL', 'FB', 'TWTR', 'BIDU']

    ibcontract.secType = 'STK'
    ibcontract.exchange = 'SMART'
    ibcontract.currency = 'USD'
    ibcontract.primaryExchange = 'SMART'

    for index in range(len(symbols)):
        print("%d-%s" % (index, symbols[index]))
        ibcontract.symbol = symbols[index]
        #ans=client.get_IB_historical_data(ibcontract, '1 W', '1 day')
        sdatetime=endDate.strftime("%Y%m%d %H:%M:%S %Z")
        ans=client.get_IB_historical_data(ibcontract, sdatetime, '3 W', '1 hour')
        #ans=client.get_IB_historical_data(ibcontract, sdatetime, '3 W', '1 day')

    #print ans
    #ans.to_csv("symbols.csv")
    print ans.head()

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
    endDate = datetime.datetime.strptime(end, "%Y-%m-%d")    

    while (cmp(startDate, endDate) < 0):
        curDay = endDate + datetime.timedelta(days = -21)
        print curDay, endDate
        get_last_hist_data(endDate)
        endDate = curDay

    #get_last_hist_data(endDate)
    #get_last_hist_data(curDay)
    

if __name__=="__main__":

    """
    This simple example returns historical data
    """
    #get_all_historical_data('2015-01-01', '2015-12-29')
    get_all_historical_data('2015-01-01', '2015-06-23')
    sys.exit()

