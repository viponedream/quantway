from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
from pyalgotrade import plotter

from pyalgotrade.tools import yahoofinance
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.stratanalyzer import returns
from pyalgotrade.stratanalyzer import trades
from pyalgotrade.stratanalyzer import drawdown
from pyalgotrade.utils import stats


class SMACrossOver(strategy.BacktestingStrategy):
    def __init__(self, feed, cash, instrument, shortSmaPeriod, longSmaPeriod):
        strategy.BacktestingStrategy.__init__(self, feed, cash)
        self.__instrument = instrument
        self.__longPos = None
        self.__shortPos = None
        # We'll use adjusted close values instead of regular close values.
        self.setUseAdjustedValues(True)
        self.__prices = feed[instrument].getCloseDataSeries()
        self.__curSMA = ma.SMA(self.__prices, 3)
        self.__shortSMA = ma.SMA(self.__prices, shortSmaPeriod)
        self.__longSMA = ma.SMA(self.__prices, longSmaPeriod)

    def getShortSMA(self):
        return self.__shortSMA

    def getLongSMA(self):
        return self.__longSMA

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
        else:
            assert(False)

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        if self.__longPos == position:
            self.info("SellToCover %s at $%.2f" % (self.__instrument, execInfo.getPrice()))
            self.__longPos = None
        elif self.__shortPos == position:
            self.info("BuyToCover %s at $%.2f" % (self.__instrument, execInfo.getPrice()))
            self.__shortPos = None
        else:
            assert(False)

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        position.exitMarket()

    def enterLongSignal(self, bar):
        return self.__curSMA[-1] > self.__curSMA[-2] and bar.getClose() > self.__longSMA[-1] and cross.cross_above(self.__shortSMA, self.__longSMA)

    def exitLongSignal(self, bar):
        return (bar.getClose() < self.__curSMA[-1] or cross.cross_below(self.__curSMA, self.__shortSMA)) and not self.__longPos.exitActive()

    def enterShortSignal(self, bar):
        return self.__curSMA[-1] < self.__curSMA[-2] and bar.getClose() < self.__shortSMA[-1] and cross.cross_below(self.__shortSMA, self.__longSMA)

    def exitShortSignal(self, bar):
        return (bar.getClose() > self.__curSMA[-1] or cross.cross_above(self.__curSMA, self.__shortSMA)) and not self.__shortPos.exitActive()

    def onBars(self, bars):
        # If a position was not opened, check if we should enter a long position.
        if self.__curSMA[-1] is None:
            return
        shares = self.getBroker().getShares(self.__instrument)
        bar = bars[self.__instrument]
        if self.__longPos is not None:
            if self.exitLongSignal(bar):
                self.__longPos.exitMarket()
        elif self.__shortPos is not None:
            if self.exitShortSignal(bar):
                self.__shortPos.exitMarket()
        else:
            if self.enterLongSignal(bar):
                shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getClose())
                self.__longPos = self.enterLong(self.__instrument, shares, True)
            elif self.enterShortSignal(bar):
                shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getClose())
                self.__shortPos = self.enterShort(self.__instrument, shares, True)
        """
        if self.__position is None:
            if cross.cross_above(self.__shortSMA, self.__longSMA) > 0:
                shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getClose())
                # Enter a buy market order. The order is good till canceled.
                self.__position = self.enterLong(self.__instrument, shares, True)
            if cross.cross_below(self.__shortSMA, self.__longSMA) > 0:
                shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getClose())
                self.__position = self.enterShort(self.__instrument, shares, True)

        # Check if we have to exit the position.
        elif not self.__position.exitActive():
            if cross.cross_below(self.__shortSMA, self.__longSMA) > 0 or cross.cross_above(self.__shortSMA, self.__longSMA) > 0:
                self.__position.exitMarket()
        """

def main(plot):

    cash = 50000

    instrument = "FB"
    shortSmaPeriod = 10
    longSmaPeriod = 20

    # Download the bars.
    feed = yahoofinance.build_feed([instrument], 2015, 2016, "../../data/")

    strat = SMACrossOver(feed, cash, instrument, shortSmaPeriod, longSmaPeriod)

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
        plt.getInstrumentSubplot(instrument).addDataSeries("shortSMA", strat.getShortSMA())
        plt.getInstrumentSubplot(instrument).addDataSeries("longSMA", strat.getLongSMA())
        # Plot the simple returns on each bar.
        plt.getOrCreateSubplot("returns").addDataSeries("Simple returns", retAnalyzer.getReturns())

    strat.run()
    print "Final portfolio value: $%.2f" % strat.getResult()
    print "Cumulative returns: %.2f %%" % (retAnalyzer.getCumulativeReturns()[-1] * 100)
    print "Average daily return: %.2f %%" % (stats.mean(retAnalyzer.getReturns()) * 100)
    print "Std. dev. daily return: %.4f" % (stats.stddev(retAnalyzer.getReturns()))
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
