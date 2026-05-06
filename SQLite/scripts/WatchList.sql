CREATE TABLE WatchList ( 
WatchListName	varchar(64), 
Symbol		varchar(10),
Name		varchar(64),
Timezone	varchar(20),
UpdateDatetime	datetime );

CREATE UNIQUE INDEX primaryWatchList on WatchList (WatchListName, Symbol);
CREATE INDEX WatchList_1 on WatchList (UpdateDatetime);
CREATE INDEX WatchList_2 on WatchList (Timezone);

INSERT into WatchList values
	( 'Holding', 'D05.SI', 'DBS Bank', 'Asia/Singapore', CURRENT_TIMESTAMP ),
	( 'Watchlist', 'GLW', 'Corning Incorporated', 'America/New_York', CURRENT_TIMESTAMP ),
	( 'Holding', 'IBIT', 'iShares Bitcoin ETF', 'America/New_York', CURRENT_TIMESTAMP ),
	( 'Watchlist', 'SOXX', 'iShares Bitcoin ETF', 'America/New_York', CURRENT_TIMESTAMP ),
	( 'Holding', '5E2.SI', 'Seatrium Ltd', 'Asia/Singapore', CURRENT_TIMESTAMP ),
	( 'Watchlist', 'S58.SI', 'SATS Ltd', 'Asia/Singapore', CURRENT_TIMESTAMP ),
	( 'Watchlist', 'BN4.SI', 'Keppel Ltd', 'Asia/Singapore', CURRENT_TIMESTAMP ),
	( 'Watchlist', 'XE', 'X-Energy Inc', 'America/New_York', CURRENT_TIMESTAMP ),
	( 'Watchlist', 'S61.SI', 'SBS Transit', 'Asia/Singapore', CURRENT_TIMESTAMP ),
	( 'Watchlist', 'AMZN', 'Amazon', 'America/New_York', CURRENT_TIMESTAMP ),
	( 'Watchlist', 'TSM', 'TSMC ADR', 'America/New_York', CURRENT_TIMESTAMP ),
	( 'Index', '^SPX', 'S&P 500 Index', 'America/New_York', CURRENT_TIMESTAMP ),
	( 'Index', '^DJI', 'Dow Jones Ind Index', 'America/New_York', CURRENT_TIMESTAMP ),
	( 'Index', '^NDX', 'NASDAQ 100 Index', 'America/New_York', CURRENT_TIMESTAMP ),
	( 'Index', '^STI', 'STI Index', 'Asia/Singapore', CURRENT_TIMESTAMP );

