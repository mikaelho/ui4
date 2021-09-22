from ui4 import Button
from ui4 import run
from ui4.table import Table


def setup(root):
    # Baseline fitted label
    Table(
        heading_row_content=['Select', 'Text'],
        content=[
            [Button(text='▶'), 'Two'],
            [Button(text='▶'), 'Four']
        ],
        dock=root.center,
    )


run(setup)
