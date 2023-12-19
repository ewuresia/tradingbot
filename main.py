# region imports
from AlgorithmImports import *
import numpy as np
# endregion

class EmotionalFluorescentYellowShark(QCAlgorithm):

    def Initialize(self):
        self.SetCash(100000)

        self.SetStartDate(2020,9,1)
        self.SetEndDate(2023,9,1)

        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol

        self.lookback = 20 #Looking back 20 days, does not matter algorthm will dynamically chnage lookback length

        self.ceiling, self.floor = 30, 10 #limits for lookback length

        self.intialStopRisk = 0.98 #will allow for 2% loss before hit
        self.trailingStopRisk = 0.9 #will trail the price by 10%

        self.Schedule.On(self.DateRules.EveryDay(self.symbol),  
                        self.TimeRules.AfterMarketOpen(self.symbol, 20),
                        Action(self.EveryMarketOpen)) #which days method is called(everyday our security trades), the time which our method is called, which method is called.

    def OnData(self, data):
        self.Plot("Data Chart", self.symbol, self.Securities[self.symbol].Close)

    def EveryMarketOpen(self):
        close = self.History(self.symbol, 31, Resolution.Daily)["close"] #closing price of secutrity over past 31 days.Returns df.
        todayvol = np.std(close[1:31]) #volatilty calculated by std
        yesterdayvol = np.std(close[0:30])
        deltavol = (todayvol - yesterdayvol) / todayvol #normalized difference of yesterday and today
        self.lookback = round(self.lookback * (1 + deltavol)) #lookbac length increases w vol increase and vice versa.

        if self.lookback > self.ceiling: #bound checking
            self.lookback = self.ceiling
        elif self.lookback < self.floor:
            self.lookback = self.floor

        self.high = self.History(self.symbol, self.lookback, Resolution.Daily)["high"]

        if not self.Securities[self.symbol].Invested and self.Securities[self.symbol].Close >= max(self.high[:-1]):
            self.SetHoldings(self.symbol, 1) #checks not currently invested and breakout is happening, buys at market price if met
            self.breakoutlvl = max(self.high[:-1])
            self.highestPrice = self.breakoutlvl

        if self.Securities[self.symbol].Invested:
            if not self.Transactions.GetOpenOrders(self.symbol): #gets open orders checks if our symbol is in this
                self.stopMarketTicket = self.StopMarketOrder(self.symbol, -self.Portfolio[self.symbol].Quantity, self.intialStopRisk * self.breakoutlvl) #send out stop loss order

            if self.Securities[self.symbol].Close > self.highestPrice and \
                self.intialStopRisk * self.breakoutlvl < self.Securities[self.symbol].Close * self.trailingStopRisk: #determines wether a new high was made
                self.highestPrice = self.Securities[self.symbol].Close #update highest price to latest closing price
                updateFields = UpdateOrderFields() #new update order object
                updateFields.StopPrice = self.Securities[self.symbol].Close * self.trailingStopRisk #use object to update order price of stop loss
                self.stopMarketTicket.Update(updateFields)

                self.Debug(updateFields.StopPrice) #checks new order price

            self.Plot("Data Chart", "Stop Price", self.stopMarketTicket.Get(OrderField.StopPrice))
            
