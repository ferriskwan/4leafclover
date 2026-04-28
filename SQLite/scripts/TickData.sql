CREATE TABLE TickData (
Symbol  varchar(10),
Interval varchar(10),
Timestamp datetime,
Open float,
High float,
Low float,
Close float,
Volume double,
UpdateDatetime datetime );

CREATE UNIQUE INDEX primaryTickData on TickData (Symbol, Interval, Timestamp);
CREATE INDEX TickData_1 on TickData (UpdateDatetime);