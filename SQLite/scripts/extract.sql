.separator '|'

-- Set the mode to list (which uses the separator)
.mode list

-- Turn on headers
.headers on

-- Tell SQLite to send all future results to a file
.output EOD_GLW.txt
select * from EODData where Symbol='GLW' order by UpdateDatetime asc;

.output Tick_GLW.txt
select * from TickData where Symbol='GLW' order by UpdateDatetime asc;

-- Tell SQLite to send all future results to the screen
.output stdout