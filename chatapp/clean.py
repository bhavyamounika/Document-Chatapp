import mysql.connector

mydb = mysql.connector.connect(
  host="127.0.0.1",
  user="root",
  passwd="",
  database="product_labs"
)


table = ['chat','documents']
for t in table:
	mycursor = mydb.cursor()
	sql = "TRUNCATE "+t
	mycursor.execute(sql)
	mycursor.close()

mydb.close()