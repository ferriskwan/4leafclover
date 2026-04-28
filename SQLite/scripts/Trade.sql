CREATE TABLE Trade ( 
ID		integer primary key,
Symbol		varchar(10) not null,
BuySell		char(1) not null, -- 'B' = Buy, 'S' = Sell
TradeDate	datetime not null,
Investment	boolean not null, -- if (Investment = True) then this is a position for a longer horizon, if (Investment = False) then this is a tactical short-term position
Price		float null,
Quantity	float not null,
Remarks		varchar(200) null,
UpdateDatetime	datetime );

CREATE INDEX Trade_1 on Trade (UpdateDatetime);
CREATE INDEX Trade_2 on Trade (Symbol, BuySell);
CREATE INDEX Trade_3 on Trade (Symbol, TradeDate);

insert into Trade values
	( NULL, 'GLW', 'B', '2026-04-22', false, 100.55, 100, NULL, CURRENT_TIMESTAMP ),
	( NULL,'D05.SI', 'B', '2025-12-10', true, 38.13, 1000, NULL, CURRENT_TIMESTAMP ),
	( NULL,'5E2.SI', 'B', '2026-04-16', true, Null, 7000, NULL, CURRENT_TIMESTAMP );