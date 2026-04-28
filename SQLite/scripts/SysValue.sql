CREATE TABLE SysValue (
Name	varchar(20),
Type	varchar(20),
StrValue	varchar(64),
NumValue	double,
DateValue	datetime,
Desc	varchar(200),
UpdateDatetime	datetime );

CREATE UNIQUE INDEX PrimarySysValue on SysValue ( Name );
CREATE INDEX SysValue_1 on SysValue ( UpdateDatetime );

insert into SysValue values 
	('GLOBAL_STARTDATE', 'datetime', NULL, NULL, '2025-01-01', 'We will go as far back as this', CURRENT_TIMESTAMP),
	('GLOBAL_TODAY', 'datetime', NULL, NULL, '2026-04-24', 'This is what we process up to today', CURRENT_TIMESTAMP);