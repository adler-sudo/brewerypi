import click
from flask import current_app
from flask_migrate import Migrate, upgrade
from sqlalchemy import create_engine
from app import create_app, db
from app.models import Area, Element, ElementAttribute, ElementAttributeTemplate, ElementTemplate, Enterprise, EventFrame, EventFrameAttribute, \
	EventFrameAttributeTemplate, EventFrameNote, EventFrameTemplate, Lookup, LookupValue, Note, Role, Site, Tag, TagValue, TagValueNote, UnitOfMeasurement, User

app = create_app()
migrate = Migrate(app, db, directory = "db/migrations")

@app.shell_context_processor
def make_shell_context():
	return dict(app = app, db = db, Area = Area, Element = Element, ElementAttribute = ElementAttribute, ElementAttributeTemplate = ElementAttributeTemplate, 
		ElementTemplate = ElementTemplate, Enterprise = Enterprise, EventFrame = EventFrame, EventFrameAttribute = EventFrameAttribute, 
		EventFrameAttributeTemplate = EventFrameAttributeTemplate, EventFrameNote = EventFrameNote,	EventFrameTemplate = EventFrameTemplate, Lookup = Lookup, 
		LookupValue = LookupValue, Note = Note, Role = Role, Site = Site, Tag = Tag, TagValue = TagValue, TagValueNote = TagValueNote, 
		UnitOfMeasurement = UnitOfMeasurement, User = User)

@app.cli.command()
def deploy():
	print ("Creating database {} if it does not exist...".format(current_app.config["MYSQL_DATABASE"]))
	engine = create_engine(current_app.config["SQLALCHEMY_SERVER_URI"])
	connection = engine.connect()
	result = connection.execute("CREATE DATABASE IF NOT EXISTS {}".format(current_app.config["MYSQL_DATABASE"]))
	print ("Running database upgrade...")
	upgrade()
	print ("Inserting default roles if needed...")
	Role.insertDefaultRoles()
	print ("Inserting default administrator if needed...")
	User.insertDefaultAdministrator()

@app.cli.command()
@click.option("--enable-all-users", is_flag = True)
@click.option("--infer-attribute-templates", is_flag = True)
@click.option("--set-user-ids-to-pi-user", is_flag = True)
def migrate(enable_all_users, infer_attribute_templates, set_user_ids_to_pi_user):
	if enable_all_users is True:
		print("Setting all users to enabled...")
		for user in User.query.all():
			user.Enabled = True
		db.session.commit()

	if infer_attribute_templates is True:
		print("Attempting to infer Element Attribute Templates LookupId or UnitOfMeasurementId...")
		for elementAttributeTemplate in ElementAttributeTemplate.query.all():
			lookupId = None
			numberOfUniqueLookupIds = 0
			numberOfUniqueUnitOfMeasurementIds = 0
			unitOfMeasurementId = None
			for elementAttribute in elementAttributeTemplate.ElementAttributes:
				if elementAttribute.Tag.LookupId is not None:
					if elementAttribute.Tag.LookupId != lookupId:
						lookupId = elementAttribute.Tag.Lookup.LookupId
						numberOfUniqueLookupIds = numberOfUniqueLookupIds + 1
				elif elementAttribute.Tag.UnitOfMeasurementId is not None:
					if elementAttribute.Tag.UnitOfMeasurementId != unitOfMeasurementId:
						unitOfMeasurementId = elementAttribute.Tag.UnitOfMeasurementId
						numberOfUniqueUnitOfMeasurementIds = numberOfUniqueUnitOfMeasurementIds + 1
				else:
					print('TagId "{}" does not have a LookupId or UnitOfMeasurementId. Aborting.'.format(elementAttribute.Tag.TagId))
					quit()

			if numberOfUniqueLookupIds == 1 and numberOfUniqueUnitOfMeasurementIds == 0:
				lookup = Lookup.query.get_or_404(lookupId)
				print('High confidence in associating attribute template "{}" in element template "{}" with lookup "{}".'. \
					format(elementAttributeTemplate.Name, elementAttributeTemplate.ElementTemplate.Name, lookup.Name))
				elementAttributeTemplate.LookupId = lookup.LookupId
			elif numberOfUniqueLookupIds == 0 and numberOfUniqueUnitOfMeasurementIds == 1:
				unitOfMeasurement = UnitOfMeasurement.query.get_or_404(unitOfMeasurementId)
				print('High confidence in associating attribute template "{}" in element template "{}" with UoM "{}".'. \
					format(elementAttributeTemplate.Name, elementAttributeTemplate.ElementTemplate.Name, unitOfMeasurement.Abbreviation))
				elementAttributeTemplate.UnitOfMeasurementId = unitOfMeasurement.UnitOfMeasurementId
			else:
				print('Low confidence in inferring lookup or UoM for attribute template "{}" in element template "{}".'. \
					format(elementAttributeTemplate.Name, elementAttributeTemplate.ElementTemplate.Name))

		print("Attempting to infer Event Frame Attribute Templates LookupId or UnitOfMeasurementId...")
		for eventFrameAttributeTemplate in EventFrameAttributeTemplate.query.all():
			lookupId = None
			numberOfUniqueLookupIds = 0
			numberOfUniqueUnitOfMeasurementIds = 0
			unitOfMeasurementId = None
			for eventFrameAttribute in eventFrameAttributeTemplate.EventFrameAttributes:
				if eventFrameAttribute.Tag.LookupId is not None:
					if eventFrameAttribute.Tag.LookupId != lookupId:
						lookupId = eventFrameAttribute.Tag.Lookup.LookupId
						numberOfUniqueLookupIds = numberOfUniqueLookupIds + 1
				elif eventFrameAttribute.Tag.UnitOfMeasurementId is not None:
					if eventFrameAttribute.Tag.UnitOfMeasurementId != unitOfMeasurementId:
						unitOfMeasurementId = eventFrameAttribute.Tag.UnitOfMeasurementId
						numberOfUniqueUnitOfMeasurementIds = numberOfUniqueUnitOfMeasurementIds + 1
				else:
					print('TagId "{}" does not have a LookupId or UnitOfMeasurementId. Aborting.'.format(elementAttribute.Tag.TagId))
					quit()

			if numberOfUniqueLookupIds == 1 and numberOfUniqueUnitOfMeasurementIds == 0:
				lookup = Lookup.query.get_or_404(lookupId)
				print('High confidence in associating attribute template "{}" in event frame template "{}" in element template "{}" with lookup "{}".'. \
					format(eventFrameAttributeTemplate.Name, eventFrameAttributeTemplate.EventFrameTemplate.Name,
					eventFrameAttributeTemplate.EventFrameTemplate.ElementTemplate.Name, lookup.Name))
				eventFrameAttributeTemplate.LookupId = lookup.LookupId
			elif numberOfUniqueLookupIds == 0 and numberOfUniqueUnitOfMeasurementIds == 1:
				unitOfMeasurement = UnitOfMeasurement.query.get_or_404(unitOfMeasurementId)
				print('High confidence in associating attribute template "{}" in event frame template "{}" in element template "{}" with UoM "{}".'. \
					format(eventFrameAttributeTemplate.Name, eventFrameAttributeTemplate.EventFrameTemplate.Name,
					eventFrameAttributeTemplate.EventFrameTemplate.ElementTemplate.Name, unitOfMeasurement.Abbreviation))
				eventFrameAttributeTemplate.UnitOfMeasurementId = unitOfMeasurement.UnitOfMeasurementId
			else:
				print('Low confidence in inferring lookup or UoM for attribute template "{}" in event frame template "{}" in element template "{}".'. \
					format(eventFrameAttributeTemplate.Name, eventFrameAttributeTemplate.EventFrameTemplate.Name,
					eventFrameAttributeTemplate.EventFrameTemplate.ElementTemplate.Name))

		db.session.commit()

	if set_user_ids_to_pi_user is True:
		piUser = User.query.filter_by(Name = "pi").one_or_none()
		if piUser == None:
			print('"pi" user not found. Aborting.')
			quit()

		print('Setting UserId to "{}" for all Event Frames...'.format(piUser.Name))
		for eventFrame in EventFrame.query.all():
			eventFrame.UserId = piUser.UserId
		db.session.commit()

		print('Setting UserId to "{}" for all Notes...'.format(piUser.Name))
		for note in Note.query.all():
			note.UserId = piUser.UserId
		db.session.commit()

		print('Setting UserId to "{}" for all TagValues...'.format(piUser.Name))
		for tagValue in TagValue.query.all():
			tagValue.UserId = piUser.UserId
		db.session.commit()
