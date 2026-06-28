.separator '|'

.mode list

.output EODData.csv
select * from EODData;

.output SysValue.csv
select * from SysValue;

.output TickData.csv
select * from TickData;

.output Trade.csv
select * from Trade;

.output WatchList.csv
select * from WatchList;

.output stdout