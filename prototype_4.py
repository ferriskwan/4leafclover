import json
import sqlite3
import os
import ProcessData as pd
import charting as ch


def main():
    conn1 = pd.connect_clover()

#    data = pulldata("GLW", "1min", "2026-04-15", "2026-04-16")
#    data = pd.TickData_generate(conn1, "GLW")
#    print(json.dumps(data, indent=4))
    data = pd.EODData_generate(conn1, "GLW")  
#    data = pd.TickData_generate(conn1, "BN4.SI")
    ch.candlestick_chart(data)
#    data = pulldata("GLW", "1day", "2025-04-15", "2026-04-16")
#    print(json.dumps(data, indent=4))
#    data1 = pulldata("GLW", "1day", "2026-04-15", "2026-04-17")
#    data1 = md.pulldata_twelvedata("GLW", "5min", "2026-04-15", "2026-04-16")
#    print(json.dumps(data1, indent=4))
#    candlestick_chart(data1)
#    data2 = pulldata_yahoo("5E2.SI", "1d", "2025-04-15", "2026-04-17")
#    print(json.dumps(data2, indent=4))
#    daily_chart(data2)
#    data3 = pulldata_yahoo("5E2.SI", "5m", "2026-04-15", "2026-04-16")
#    data3 = md.pulldata_yahoo("GLW", "5m", "2026-04-15", "2026-04-16")
#    print(json.dumps(data3, indent=4))
#    candlestick_chart(data3)
#    data4 = pd.TickData_generate(conn1, "5E2.SI")
#    data4 = pd.EODData_generate(conn1, "GLW")
#    print(json.dumps(data4, indent=4))
#    ch.daily_chart(data4)


if __name__ == "__main__":
    main()


