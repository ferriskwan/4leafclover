CREATE TABLE EODData (
Symbol varchar(10), 
Date date, 
Open float, 
High float, 
Low float, 
Close float, 
Volume double,
UpdateDatetime datetime);

CREATE UNIQUE INDEX primaryEODData on EODData (Symbol, Date);
CREATE INDEX EODData_1 on EODData (UpdateDatetime);