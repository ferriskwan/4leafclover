.separator '|'

-- Set the mode to list (which uses the separator)
.mode list

-- Turn on headers
.headers on

-- Tell SQLite to send all future results to a file
.output EOD_BN4.txt
select * from EODData where Symbol='BN4.SI' order by UpdateDatetime asc;

.output Tick_BN4.txt
select * from TickData where Symbol='BN4.SI' order by UpdateDatetime asc;

-- Tell SQLite to send all future results to the screen
.output stdout