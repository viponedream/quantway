from swigibpy import EWrapper
import time
import random

import sys
import datetime
from swigibpy import EPosixClientSocket

from IButils import autodf

MEANINGLESS_NUMBER=999

symbols_dict = dict()

EMPTY_HDATA=autodf("symbol", "sdate", "open", "high", "low", "close", "volume", "barcount", "wap", "hasgaps")

### how many seconds before we give up
MAX_WAIT=30

def return_IB_connection_info():
    """
    Returns the tuple host, port, clientID required by eConnect

    """
    host=""
    port=7496
    #clientid=999
    clientid = random.randint(100, 10000) + random.randint(100, 10000) 

    return (host, port, clientid)

class IBWrapper(EWrapper):
    """

        Callback object passed to TWS, these functions will be called directly
    by TWS.

    """

    def init_error(self):
        setattr(self, "flag_iserror", False)

    def error(self, id, errorCode, errorString):
        """
        error handling, simple for now

        Here are some typical IB errors
        INFO: 2107, 2106
        WARNING 326 - can't connect as already connected
        CRITICAL: 502, 504 can't connect to TWS.
            200 no security definition found
            162 no trades

        """

        ## Any errors not on this list we just treat as information
        ERRORS_TO_TRIGGER=[201, 103, 502, 504, 509, 200, 162, 420, 2105, 1100, 478, 201, 399]

        if errorCode in ERRORS_TO_TRIGGER:
            errormsg="IB error id %d errorcode %d string %s" %(id, errorCode, errorString)
            print errormsg
            setattr(self, "flag_iserror", True)
            setattr(self, "error_msg", True)

        ## Wrapper functions don't have to return anything


    ## The following are not used

    def nextValidId(self, orderId):
        pass

    def managedAccounts(self, openOrderEnd):
        pass

    def init_historicprices(self, tickerid):
        if "data_historicdata" not in dir(self):
            histdict=dict()
        else:
            histdict=self.data_historicdata

        histdict[tickerid]=EMPTY_HDATA
        setattr(self, "data_historicdata", histdict)
        setattr(self, "flag_historicdata_finished", False)

    def historicalData(self, reqId, date, openprice, high,
                       low, close, volume,
                       barCount, WAP, hasGaps):

        global symbols_dict
        if date[:8] == 'finished':
            setattr(self, "flag_historicdata_finished", True)
        else:
            historicdata=self.data_historicdata[reqId]

            if len(str(date)) > 8:
                date = datetime.datetime.strptime(date, "%Y%m%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
            else:
                date=datetime.datetime.strptime(date,"%Y%m%d")

            historicdata.add_row(symbol=symbols_dict[reqId], sdate=date, open=openprice, high=high,
                low=low, close=close, volume=volume, barcount=barCount, wap=WAP, hasgaps=hasGaps)
            #print("symbol: %s, Date: %s, open: %f" % (symbols_dict[reqId], str(date), openprice))


class IBclient(object):
    def __init__(self, callback):
        tws = EPosixClientSocket(callback)
        (host, port, clientid)=return_IB_connection_info()
        tws.eConnect(host, port, clientid)

        self.tws=tws
        self.cb=callback


    def get_IB_historical_data(self, ibcontract, sdatetime, durationStr="1 Y", barSizeSetting="1 day", tickerid=MEANINGLESS_NUMBER):

        """
        Returns historical prices for a contract, up to today

        tws is a result of calling IBConnector()

        """
        global symbols_dict
        symbols_dict[tickerid] = ibcontract.symbol

        today=datetime.datetime.now()
        #d1=datetime.datetime.now()
        #today = d1 + datetime.timedelta(days = -3)

        self.cb.init_error()
        self.cb.init_historicprices(tickerid)

        # Request some historical data.
        self.tws.reqHistoricalData(
                tickerid,                                          # tickerId,
                ibcontract,                                   # contract,
                sdatetime,                                   # endDateTime, today.strftime("%Y%m%d %H:%M:%S %Z")
                durationStr,                                      # durationStr,
                barSizeSetting,                                    # barSizeSetting,
                "TRADES",                                   # whatToShow,
                1,                                          # useRTH,
                1,                                           # formatDate
                None
            )

        start_time=time.time()
        finished=False
        iserror=False

        while not finished and not iserror:
            finished=self.cb.flag_historicdata_finished
            iserror=self.cb.flag_iserror

            if (time.time() - start_time) > MAX_WAIT:
                iserror=True
            pass

        if iserror:
            print self.cb.error_msg
            raise Exception("Problem getting historic data")

        historicdata=self.cb.data_historicdata[tickerid]
        #results=historicdata.to_pandas("date")
        results=historicdata.to_pandas()
        return results
