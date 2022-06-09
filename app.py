from flask import Flask, render_template, request, send_file, redirect, url_for
import pandas as pd
from AutoDataClean import AutoDataClean
try:
	from werkzeug.utils import secure_filename
except:
	from werkzeug import secure_filename
import itertools
from draw import draw_graph

import os
app = Flask(__name__)
#app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 #파일 업로드 용량 제한 단위:바이트

pipeline = None
f = None
categ = None
@app.errorhandler(404)
def page_not_found(error):
	app.logger.error(error)
	return render_template('page_not_found.html'), 404

#HTML 렌더링
@app.route('/')
def home_page():
	return render_template('home.html')

#업로드 HTML 렌더링
@app.route('/upload')
def upload_page():
	return render_template('upload.html')

#파일 업로드 처리
@app.route('/charts')
def show_charts():
	global pipeline, f
	tmp = []
	type = None
	label = None
	titles = None

	print(pipeline.time_series, pipeline.categ_features, pipeline.num_features)
	if pipeline.time_series == False:
		result = list(itertools.combinations(list(pipeline.num_features), 2))
		for x, y in result:
			tmp.append([{'x': list(pipeline.output[x].apply(str).values)[i],
						 'y': list(pipeline.output[y].apply(str).values)[i]} for i in
						range(len(list(pipeline.output[x].values)))])
		type = 'bubble'
		label = ''
		titles = result

	else:
		for feature in pipeline.num_features:
			tmp.append(list(pipeline.output[feature].apply(str).values))
		type = 'line'
		label = list(pipeline.output[pipeline.time_series].apply(str).values)
		titles = list(pipeline.num_features)

	tmp2 = []
	type2 = 'bar'
	label2 = []
	titles2 = list(pipeline.categ_features)

	for feature in pipeline.categ_features:
		# tmp.append(list(pipeline.output[feature].values))
		label2.append(list(pipeline.output[feature].value_counts().keys()))
		tmp2.append(list(map(lambda x: str(x), list(pipeline.output[feature].value_counts().values))))

	return render_template('charts.html',
						   type=type, values=tmp, titles=titles, num=range(len(pipeline.num_features)), label=label,
						   type2=type2, values2=tmp2, titles2=titles2, num2=range(len(pipeline.categ_features)), label2=label2,
						   columns=str(pipeline.categ_features + pipeline.num_features))

@app.route('/dashboard', methods = ['GET', 'POST'])
def dashboard():
	global pipeline, f, categ
	if request.method == 'POST':
		f = request.files['file']
		print(request.form['param'])
		#저장할 경로 + 파일명
		f.save('./uploads/' + secure_filename(f.filename))
		data = pd.read_csv('./uploads/' + secure_filename(f.filename), encoding='cp949')
		pipeline = AutoDataClean(data, outlier_param=float(request.form['param']))
		pipeline.output.to_csv('./downloads/' + '(OUTPUT)' + secure_filename(f.filename), mode='w', encoding='cp949')
		print(pipeline.output.columns)
		draw_graph('corr', pipeline)
		draw_graph('num', pipeline)
		draw_graph('categ', pipeline)

		if pipeline.categ_features != []:
			categ = True
		else:
			categ = False
	return render_template('dashboard.html', columns=str(pipeline.categ_features + pipeline.num_features),
						   categ=categ)

@app.route('/chart', methods = ['GET', 'POST'])
def pick():
	if request.method == 'POST':
		text = request.form['text']
		return redirect(url_for('chart', name=text))


@app.route('/chart/<name>')
def chart(name):
	global pipeline
	text = name
	tmp = []
	type = None
	label = None
	titles = None

	print(pipeline.time_series, pipeline.categ_features, pipeline.num_features)

	if text in pipeline.num_features:
		if pipeline.time_series == False:
			result = [[text, i] for i in list(pipeline.num_features) if i != text]
			for x, y in result:
				tmp.append([{'x': list(pipeline.output[x].apply(str).values)[i],
							 'y': list(pipeline.output[y].apply(str).values)[i]} for i in
							range(len(list(pipeline.output[x].values)))])
			type = 'bubble'
			label = ''
			titles = result

		else:
			tmp.append(list(pipeline.output[text].apply(str).values))
			type = 'line'
			label = list(pipeline.output[pipeline.time_series].apply(str).values)
			titles = [text]
	else:
		type = 'bar'
		label = list(pipeline.output[text].value_counts().keys())
		tmp.append(list(map(lambda x: str(x), list(pipeline.output[text].value_counts().values))))
		titles = [text]

	return render_template('chart.html', type=type, values=tmp, titles=titles,
						   num=range(len(tmp)), label=label, columns=str(pipeline.categ_features + pipeline.num_features))

#테이블
@app.route('/table')
def table():
	global pipeline, f
	if pipeline != None:
		return render_template('table.html', tables=[pipeline.output.to_html()], titles=[secure_filename(f.filename)])
	else:
		return render_template('page_not_found.html')

#로그
@app.route('/log')
def log():
	global pipeline
	if pipeline != None:
		tmp = open('./autoclean.log', 'rt', encoding='UTF8')
		log = tmp.readlines()
		tmp.close()
		return render_template('log.html', log=log, outlier=pipeline.added_outlier, timeseries=pipeline.added_timecycle)
	else:
		return render_template('page_not_found.html')

#다운로드 HTML 렌더링
@app.route('/downfile')
def down_page():
	files = os.listdir("./downloads")
	return render_template('filedown.html',files=files)

#파일 다운로드 처리
@app.route('/fileDown', methods = ['GET', 'POST'])
def down_file():
	if request.method == 'POST':
		sw=0
		files = os.listdir("./downloads")
		for x in files:
			if(x==request.form['file']):
				sw=1
				path = "./downloads/"
				return send_file(path + request.form['file'],
						attachment_filename = request.form['file'],
						as_attachment=True)

		return render_template('page_not_found.html')
	else:
		return render_template('page_not_found.html')

if __name__ == '__main__':
	#서버 실행
	app.run(host='0.0.0.0', debug = True)
