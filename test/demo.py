import MySQLdb as mdb

__author__ = 'kvbian'

if __name__=="__main__":
    conn=mdb.connect(host='127.0.0.1',user='border',passwd='border', db='finance', port=3306)
    cur=conn.cursor(mdb.cursors.DictCursor)
    cur.execute("SELECT id, symbol, sdate, open, high, low, close, volume from stock_data_1hour order by sdate desc limit 100")

    rows = cur.fetchall()

    for row in rows:
        print "%d, %s, %s, %0.2f" % (row['id'], row['symbol'], row['sdate'], row['open'])