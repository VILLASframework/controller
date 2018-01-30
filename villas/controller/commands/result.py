from .. import command

class ResultCommand(command.Command):

	@staticmethod
	def run(connection, args):
		raise NotImplementedError
