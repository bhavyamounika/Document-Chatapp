from flask import Flask, render_template, request,  jsonify
from loremipsum import get_paragraphs, get_sentences
from werkzeug import secure_filename
import random
import string

import json
import mysql.connector

mydb = mysql.connector.connect(
  host="127.0.0.1",
  user="root",
  passwd="",
  database="product_labs"
)

app = Flask(__name__)

@app.route('/')
def hello_world():
	mycursor = mydb.cursor()
	data = {}
	docs_data = {}
	sql = "SELECT p.*, u.username, u.profile_pic FROM (SELECT c.*, d.document_name, d.document_url FROM `chat` c LEFT JOIN `documents` d ON c.document_id = d.document_id) p LEFT JOIN `users` u ON p.user_id = u.userid ORDER BY p.timestamp ASC"
	mycursor.execute(sql)
	records = mycursor.fetchall()
	for row in records:
		if row[6] == 1:
			each_data = {
				'fileUrl'  : row[10],
				'message' : row[4],
				'name' : row[11],
				'type' : "file",
				'url' : row[12]
			}
			if row[1] in data:
				data[row[1]].append(each_data)
			else:
				data[row[1]] = [each_data]
			
			if row[1] in docs_data:
				docs_data[row[1]].append(row[2])
			else:
				docs_data[row[1]] = [row[2]]
		else:
			message = {
				'message': row[4],
				'name': row[11],
				'type': "replies",
				'url': row[12]
			}
			bot_pic = "https://discord.bots.gg/img/user_icon_placeholder.png" if "1" in row[1]  else "https://d2.alternativeto.net/dist/icons/autoresponder-bot_139878.png?width=128&height=128&mode=crop&upscale=false"
			reply = {
				'message' : row[5],
				'name': row[4],
				'type': "sent",
				'url': bot_pic
			}
			
			if row[1] in data:
				data[row[1]].append(message)
				data[row[1]].append(reply)
			else:
				data[row[1]] = [message, reply]
			
			if row[8] != 0:
				thumps = 'up' if row[8] == 1 else 'down'
				msg = thumps
				feedback = {
					'message':msg,
					'name':row[11],
					'type':'like',
					'url':row[12]
				}
				feedback_respone = {
					'message':"Thanks for the feedback!",
					'name':row[11],
					'type':'sent',
					'url':bot_pic
				}
				data[row[1]].append(feedback)
				data[row[1]].append(feedback_respone)
   
	return render_template('index.html', data=json.dumps(data), docs_data=json.dumps(docs_data))

@app.route('/message')
def reply():
	# print(request.args['message'])
	message = request.args['message']
	botid = request.args['bot_id']
	doc_id = request.args['doc_id']
	reply  = get_sentences(1)[0]
	mycursor = mydb.cursor()
	# sql = "INSERT INTO customers (name, address) VALUES (%s, %s)"
	sql = "INSERT INTO `chat`( `bot_name`, `document_id`, `user_id`, `message`, `reply`) VALUES (%s, %s, %s, %s, %s)"
	val = (botid, doc_id , 0 , message, reply)
	mycursor.execute(sql, val)
	mydb.commit()
	return reply

@app.route('/feedback')
def feedback():
	bot_id = request.args['bot_id']
	feedback = 1 if request.args['thumps'] == "up" else -1
	sql = "UPDATE `chat` SET `feedback`="+str(feedback)+" WHERE `message_id` = (SELECT `message_id` FROM (SELECT * FROM `chat`) AS c WHERE c.`bot_name`='"+str(bot_id)+"' ORDER BY c.`message_id` DESC LIMIT 1 )"
	mycursor = mydb.cursor()
	
	mycursor.execute(sql)
	mydb.commit()
	
	return "Thanks for the feedback!"

@app.route('/upload', methods = ['GET', 'POST'])
def upload_file():
	if request.method == 'POST':
		f = request.files['file']
		botid = request.form['bot_id']
		x = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))
		actfile = secure_filename(f.filename)
		savepath = 'static/uploads/'+x+'_'+actfile
		f.save(savepath)
		mycursor = mydb.cursor()
		sql = "INSERT INTO `documents`( `document_name`, `document_url`, `userid`) VALUES (%s, %s, %s)"
		val = (actfile, savepath, 0)
		mycursor.execute(sql, val)
		mydb.commit()
		doc_id = mycursor.lastrowid

		sql = "INSERT INTO `chat`( `bot_name`, `document_id`, `user_id`, `message`, `isFile`, `reply`) VALUES (%s, %s, %s, %s, %s, %s)"
		val = (botid, doc_id, 0, actfile, 1, '')
		mycursor.execute(sql, val)
		mydb.commit()
		
		return jsonify({'url':savepath, 'doc_id':doc_id })

if __name__ == '__main__':
	app.static_url_path=app.config.get('STATIC_FOLDER')
	app.static_folder = app.root_path + app.static_url_path
	app.run()