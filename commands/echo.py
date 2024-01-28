from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("message")

def execute_cmd(params):
	print(params)

