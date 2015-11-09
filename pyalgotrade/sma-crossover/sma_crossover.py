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
    def __init__(self, feed, instrument, smaPeriod):
        strategy.BacktestingStrategy.__init__(self, feed)
        self.__instrument = instrument
        self.__position = None
        # We'll use adjusted close values instead of regular close values.
        self.setUseAdjustedValues(True)
        self.__prices = feed[instrument].getPriceDataSeries()
        self.__sma = ma.SMA(self.__prices, smaPeriod)

    def getSMA(self):
        return self.__sma

    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):
        self.__position = None

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        self.__position.exitMarket()

    def onBars(self, bars):
        # If a position was not opened, check if we should enter a long position.
        if self.__position is None:
            if cross.cross_above(self.__prices, self.__sma) > 0:
                shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getPrice())
                # Enter a buy market order. The order is good till canceled.
                self.__position = self.enterLong(self.__instrument, shares, True)
        # Check if we have to exit the position.
        elif not self.__position.exitActive() and cross.cross_below(self.__prices, self.__sma) > 0:
            self.__position.exitMarket()

def main(plot):
    instrument = "FB"
    #smaPeriod = 163
    smaPeriod = 20

    # Download the bars.
    feed = yahoofinance.build_feed([instrument], 2014, 2015, "../../data/")

    strat = SMACrossOver(feed, instrument, smaPeriod)

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
        #plt = plotter.StrategyPlotter(strat, True, False, True)
        plt.getInstrumentSubplot(instrument).addDataSeries("sma", strat.getSMA())
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
