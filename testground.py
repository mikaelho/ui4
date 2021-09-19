from ui4 import run
from ui4.table import Table


def setup(root):
    # Baseline fitted label
    Table(content=[['One', 'Two'], ['Three', 'Four']], dock=root.center)


run(setup)
