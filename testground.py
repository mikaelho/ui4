from dataclasses import dataclass

from ui4 import Form
from ui4 import serve


def setup(root):

    @dataclass
    class DataFormat:
        name: str = 'Demo Person'
        address: str = 'Some Street 1, Some Town, Some Country'
        age: int = 33
        email_me: bool = False
        email: str = 'some@email.com'

    Form(data=DataFormat(name='Another value'), dock=root.all)

serve(setup)
