'''Simple example of using the SWIG generated TWS wrapper to request historical
data from interactive brokers.

Note:
* Communication with TWS is asynchronous; requests to TWS are made through the
EPosixClientSocket class and TWS responds at some later time via the functions
in our EWrapper subclass.
* If you're using a demo account TWS will only respond with a limited time
period, no matter what is requested. Also the data returned is probably wholly
unreliable.

'''

import pandas as pd
import numpy as np

from datetime import datetime
from threading import Event

from swigibpy import EWrapper, EPosixClientSocket, Contract


WAIT_TIME = 5.0

useRTH = 0

#better to read these from a file
contractlist = pd.DataFrame([
    ['STK.AAPL'],
    ['STK.FB'],
    ['STK.QQQ'],
    ['STK.SPY']
    ])

columns = ['sym', 'Date', 'bidPrice', 'askPrice', 'lastPrice']
symbols = pd.DataFrame(data=np.zeros((0,len(columns))), columns=columns)

# make decent column names
contractlist.columns = ['sym']

def create_contract(security):
    if security.split('.')[0]=='FUT':
        contract = Contract()
        contract.symbol = security.split('.')[1]
        contract.secType = 'FUT'
        contract.exchange = 'GLOBEX'
        contract.currency = security.split('.')[2]
        contract.expiry= security.split('.')[3]
        contract.primaryExchange='GLOBEX'
    elif security.split('.')[0]=='CASH':
        contract = Contract()
        contract.symbol = security.split('.')[1]
        contract.secType = 'CASH'
        contract.exchange = 'IDEALPRO'
        contract.currency = security.split('.')[2]
        contract.primaryExchange='IDEALPRO'
    elif security.split('.')[0]=='STK':
        contract = Contract()
        contract.symbol = security.split('.')[1]
        contract.secType = 'STK'
        contract.exchange = 'SMART'
        contract.currency = 'USD'
        contract.primaryExchange='SMART'
    return contract

class HistoricalDataExample(EWrapper):
    '''Callback object passed to TWS, these functions will be called directly
    by TWS.

    '''

    def __init__(self):
        super(HistoricalDataExample, self).__init__()
        self.got_history = Event()

    def orderStatus(self, id, status, filled, remaining, avgFillPrice, permId,
                    parentId, lastFilledPrice, clientId, whyHeld):
        pass

    def openOrder(self, orderID, contract, order, orderState):
        pass

    def nextValidId(self, orderId):
        '''Always called by TWS but not relevant for our example'''
        pass

    def openOrderEnd(self):
        '''Always called by TWS but not relevant for our example'''
        pass

    def managedAccounts(self, openOrderEnd):
        '''Called by TWS but not relevant for our example'''
        pass

    def historicalData(self, reqId, date, open, high,
                       low, close, volume,
                       barCount, WAP, hasGaps):
        global symbols
        if date[:8] != 'finished':
            #date = datetime.strptime(date, "%Y%m%d").strftime("%d %b %Y")
            date = datetime.strptime(date, "%Y%m%d").strftime("%Y-%m-%d")
            print(("reqId: %s, History %s - Open: %s, High: %s, Low: %s, Close: "
                    "%s, Volume: %d") % (contractlist.loc[reqId]['sym'], date, open, high, low, close, volume))
            symbols = symbols.append({'sym':contractlist.loc[reqId]['sym'], 'Date':date, 'bidPrice':open, 'askPrice':close, 'lastPrice':high}, ignore_index=True)

            '''
        if date[:8] == 'finished':
            print("History request complete")
            self.got_history.set()
        else:
            date = datetime.strptime(date, "%Y%m%d").strftime("%d %b %Y")
            print(("reqId: %d, History %s - Open: %s, High: %s, Low: %s, Close: "
                   "%s, Volume: %d") % (reqId, date, open, high, low, close, volume))
        '''


# Instantiate our callback object
callback = HistoricalDataExample()

# Instantiate a socket object, allowing us to call TWS directly. Pass our
# callback object so TWS can respond.
tws = EPosixClientSocket(callback, reconnect_auto=True)

# Connect to tws running on localhost
if not tws.eConnect("", 7496, 42):
    raise RuntimeError('Failed to connect to TWS')

today = datetime.today()

for index, row in contractlist.iterrows():
    print 'Index:', index, ', Sym:', row['sym']
    #self.reqMktData(index, create_contract(row['sym']), '233', False)
    # Request some historical data.
    tws.reqHistoricalData(
        index,                                        # tickerId,
        create_contract(row['sym']),                                   # contract,
        today.strftime("%Y%m%d %H:%M:%S %Z"),       # endDateTime,
        "1 W",                                      # durationStr,
        "1 day",                                    # barSizeSetting,
        "TRADES",                                   # whatToShow,
        useRTH,                                          # useRTH,
        1,                                          # formatDate
        None                                        # chartOptions
    )

print("\n====================================================================")
print(" History requested, waiting %ds for TWS responses" % WAIT_TIME)
print("====================================================================\n")


try:
    callback.got_history.wait(timeout=WAIT_TIME)
    print symbols
except KeyboardInterrupt:
    pass
finally:
    if not callback.got_history.is_set():
        print('Failed to get history within %d seconds' % WAIT_TIME)

    print("\nDisconnecting...")
    tws.eDisconnect()
