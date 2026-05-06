.separator '|'

-- Set the mode to list (which uses the separator)
.mode list

-- Turn on headers
.headers on

-- Tell SQLite to send all future results to a file
.output EOD_TSM.txt
select * from EODData where Symbol='TSM' order by UpdateDatetime asc;

.output Tick_TSM.txt
select * from TickData where Symbol='TSM' order by UpdateDatetime asc;

-- Tell SQLite to send all future results to the screen
.output stdout