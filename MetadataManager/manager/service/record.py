from datetime import datetime

from flask import Blueprint, request, render_template, jsonify, url_for, redirect

from manager.model import RecordModel, db
from manager.utils import clean_form_data

class Record:

	def get(self, id=None, format='html', edit=False):
		if id is None:
			record = RecordModel()
		else:
			record = RecordModel.query.get_or_404(id)
		if format == "html":
			if edit:
				return render_template('edit.html', record=record.to_form())
			else:
				return render_template('record.html', record=record.to_json())
		elif format == "json":
			return jsonify(record.to_json())
		elif format == "solr":
			return jsonify(record.to_solr())

	def post(self, form):
		
		created = False
		record = RecordModel.query.filter_by(id=form['id']).first()

		if record is None:
			created = True
			record = RecordModel()
			record.id = form['id']

		cleaned_data = clean_form_data(form)

		cleaned_data['modified'] = datetime.now()

		for k, v in cleaned_data.items():
			setattr(record, k, v)

		if created:
			db.session.add(record)

		db.session.commit()

		record.export_to_staging()

		return redirect(url_for('manager.handle_record', id=record.id))
