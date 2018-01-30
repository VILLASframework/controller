from .. import command

class ModelCommand(command.Command):

	@staticmethod
	def run(connection, args):
		raise NotImplementedError
