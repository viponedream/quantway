# -*- coding: utf-8 -*-
import math
import datetime

import numpy as np
from scipy import stats

from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
from pyalgotrade.technical import linreg
from pyalgotrade import plotter

from pyalgotrade import dataseries
from pyalgotrade.tools import yahoofinance
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.stratanalyzer import returns
from pyalgotrade.stratanalyzer import trades
from pyalgotrade.stratanalyzer import drawdown
from pyalgotrade.utils import stats as pystats
from pyalgotrade.utils import dt

import sys

class dualThrust(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, smaPeriod):
        strategy.BacktestingStrategy.__init__(self, feed)
        self.__smaPeriod = smaPeriod
        self.__instrument = instrument
        self.__longPos = None
        self.__shortPos = None
        # We'll use adjusted close values instead of regular close values.
        self.setUseAdjustedValues(False)

        self.__highDataSeries = feed[instrument].getHighDataSeries()
        self.__closeDataSeries = feed[instrument].getPriceDataSeries()
        self.__lowDataSeries = feed[instrument].getLowDataSeries()

        self.__sma = ma.SMA(self.__closeDataSeries, smaPeriod)


    def getSMA(self):
        return self.__sma

    def onEnterCanceled(self, position):
        if self.__longPos == position:
            self.__longPos = None
        elif self.__shortPos == position:
            self.__shortPos = None

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        if self.__longPos == position:
            self.info("Long BUY %s at $%.2f" % (self.__instrument, execInfo.getPrice()))
        elif self.__shortPos == position:
            self.info("Short BUY %s at $%.2f" % (self.__instrument, execInfo.getPrice()))

    def onEnterCanceled(self, position):
        if self.__longPos == position:
            self.__longPos = None
        elif self.__shortPos == position:
            self.__shortPos = None

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        if self.__longPos == position:
            self.info("SellToCover %s at $%.2f" % (self.__instrument, execInfo.getPrice()))
            self.__longPos = None
        elif self.__shortPos == position:
            self.info("BuyToCover %s at $%.2f" % (self.__instrument, execInfo.getPrice()))
            self.__shortPos = None

    def enterLongSignal(self, bar, buyLine):
        return bar.getPrice() > buyLine

    def exitLongSignal(self, bar, sellLine):
        # 当股价两天内下跌6%，或者三天内下跌8%则卖出股票
        closeValues = self.__closeDataSeries._SequenceDataSeries__values
        case1 = (1- (closeValues[-1]/closeValues[-3])) >= 0.06
        case2 = (1- (closeValues[-2]/closeValues[-3])) >= 0.08
        return bar.getPrice() < sellLine or case1 or case2

    def enterShortSignal(self, bar, shortLine):
        return bar.getPrice() < shortLine

    def exitShortSignal(self, bar, buyLine):
        # 当股价两天内上涨6%，或者三天内上涨8%则卖出股票
        closeValues = self.__closeDataSeries._SequenceDataSeries__values
        case1 = ((closeValues[-1]/closeValues[-3]) - 1) >= 0.06
        case2 = ((closeValues[-2]/closeValues[-3]) - 1) >= 0.08
        return bar.getPrice() > buyLine or case1 or case2

    def onBars(self, bars):
        # If a position was not opened, check if we should enter a long position.
        if self.__sma[-1] is None or self.__sma[-2] is None:
            return

        bar = bars[self.__instrument]

        highValues = self.__highDataSeries._SequenceDataSeries__values
        closeValues = self.__closeDataSeries._SequenceDataSeries__values
        lowValues = self.__lowDataSeries._SequenceDataSeries__values

        HH = max(highValues)
        HC = max(closeValues)
        LC = min(closeValues)
        LL = min(lowValues)
        open = bar.getOpen()

        range = max((HH-LC), (HC-LL))
        K1 = 0.1
        K2 = 0.1

        buyLine = open + K1 * range
        shortLine = open - K2 * range

        print bar.getPrice(), range, buyLine, shortLine

        if self.__longPos is not None:
            if self.exitLongSignal(bar, shortLine):
                self.__longPos.exitMarket()
        elif self.__shortPos is not None:
            if self.exitShortSignal(bar, buyLine):
                self.__shortPos.exitMarket()
        else:
            shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getClose())
            if self.enterLongSignal(bar, buyLine):
                self.__longPos = self.enterLong(self.__instrument, shares, True)
            elif self.enterShortSignal(bar, shortLine):
                self.__shortPos = self.enterShort(self.__instrument, shares, True)


def main(plot):
    instrument = "FB"
    smaPeriod = 10

    # Download the bars.
    feed = yahoofinance.build_feed([instrument], 2015, 2016, "../../data/")

    strat = dualThrust(feed, instrument, smaPeriod)

    retAnalyzer = returns.Returns()
    strat.attachAnalyzer(retAnalyzer)

    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    strat.attachAnalyzer(sharpeRatioAnalyzer)

    tradesAnalyzer = trades.Trades()
    strat.attachAnalyzer(tradesAnalyzer)

    drawDownAnalyzer = drawdown.DrawDown()
    strat.attachAnalyzer(drawDownAnalyzer)


    if plot:
        plt = plotter.StrategyPlotter(strat, True, True, True)
        plt.getInstrumentSubplot(instrument).addDataSeries("sma", strat.getSMA())
        # Plot the simple returns on each bar.
        plt.getOrCreateSubplot("returns").addDataSeries("Simple returns", retAnalyzer.getReturns())

    strat.run()
    print "Final portfolio value: $%.2f" % strat.getResult()
    print "Cumulative returns: %.2f %%" % (retAnalyzer.getCumulativeReturns()[-1] * 100)
    print "Average daily return: %.2f %%" % (pystats.mean(retAnalyzer.getReturns()) * 100)
    print "Std. dev. daily return: %.4f" % (pystats.stddev(retAnalyzer.getReturns()))
    print "Sharpe ratio: %.2f" % (sharpeRatioAnalyzer.getSharpeRatio(0.05))
    print "Max. drawdown: %.2f %%" % (drawDownAnalyzer.getMaxDrawDown() * 100)
    print "Longest drawdown duration: %s" % (drawDownAnalyzer.getLongestDrawDownDuration())

    print
    print "Total trades: %d" % (tradesAnalyzer.getCount())
    if tradesAnalyzer.getCount() > 0:
        profits = tradesAnalyzer.getAll()
        print "Avg. profit: $%2.f" % (profits.mean())
        print "Profits std. dev.: $%2.f" % (profits.std())
        print "Max. profit: $%2.f" % (profits.max())
        print "Min. profit: $%2.f" % (profits.min())
        rets = tradesAnalyzer.getAllReturns()
        print "Avg. return: %2.f %%" % (rets.mean() * 100)
        print "Returns std. dev.: %2.f %%" % (rets.std() * 100)
        print "Max. return: %2.f %%" % (rets.max() * 100)
        print "Min. return: %2.f %%" % (rets.min() * 100)

    print
    print "Profitable trades: %d" % (tradesAnalyzer.getProfitableCount())
    if tradesAnalyzer.getProfitableCount() > 0:
        profits = tradesAnalyzer.getProfits()
        print "Avg. profit: $%2.f" % (profits.mean())
        print "Profits std. dev.: $%2.f" % (profits.std())
        print "Max. profit: $%2.f" % (profits.max())
        print "Min. profit: $%2.f" % (profits.min())
        rets = tradesAnalyzer.getPositiveReturns()
        print "Avg. return: %2.f %%" % (rets.mean() * 100)
        print "Returns std. dev.: %2.f %%" % (rets.std() * 100)
        print "Max. return: %2.f %%" % (rets.max() * 100)
        print "Min. return: %2.f %%" % (rets.min() * 100)

    print
    print "Unprofitable trades: %d" % (tradesAnalyzer.getUnprofitableCount())
    if tradesAnalyzer.getUnprofitableCount() > 0:
        losses = tradesAnalyzer.getLosses()
        print "Avg. loss: $%2.f" % (losses.mean())
        print "Losses std. dev.: $%2.f" % (losses.std())
        print "Max. loss: $%2.f" % (losses.min())
        print "Min. loss: $%2.f" % (losses.max())
        rets = tradesAnalyzer.getNegativeReturns()
        print "Avg. return: %2.f %%" % (rets.mean() * 100)
        print "Returns std. dev.: %2.f %%" % (rets.std() * 100)
        print "Max. return: %2.f %%" % (rets.max() * 100)
        print "Min. return: %2.f %%" % (rets.min() * 100)

    if plot:
        plt.plot()


if __name__ == "__main__":
    main(True)
