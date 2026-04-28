CREATE TABLE Objective (
WatchListName varchar(64), 
Symbol	varchar(10),
TargetPrice	float null,
TargetProfit	double null,
TargetPercent	float null,
Remarks		varchar(200) null,
UpdateDatetime	datetime );

CREATE UNIQUE INDEX primaryObjective_1 on Objective (UpdateDatetime, WatchListName, Symbol);
CREATE INDEX Objective_1 on Objective (UpdateDatetime);
CREATE INDEX Objective_2 on Objective (WatchListName);
CREATE INDEX Objective_3 on Objective (Symbol);

