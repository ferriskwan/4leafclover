CREATE TABLE Position ( 
TradeDate	datetime null,
Symbol		varchar(10) not null,
Investment	boolean not null, -- if (Investment = True) then this is a position for a longer horizon, if (Investment = False) then this is a tactical short-term position
AvgPrice	float null,
Quantity	float not null,
UpdateDatetime datetime );

CREATE UNIQUE INDEX primaryPosition on Position (TradeDate, Symbol);
CREATE INDEX Position_1 on Position (UpdateDatetime);
CREATE INDEX Position_2 on Position (TradeDate);
CREATE INDEX Position_3 on Position (Investment);
