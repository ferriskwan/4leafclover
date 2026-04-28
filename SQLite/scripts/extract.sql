.separator '|'

-- Set the mode to list (which uses the separator)
.mode list

-- Turn on headers
.headers on

-- Tell SQLite to send all future results to a file
.output result.txt

select * from TickData where Symbol='IBIT' order by UpdateDatetime asc;

-- Tell SQLite to send all future results to the screen
.output stdout