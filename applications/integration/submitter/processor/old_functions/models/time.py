from pydantic import BaseModel, Field

'''
Time definition:
- name = recorded name of the time
- begin = recorded start time of the operation
- end = recored end time of the operation
- total = recored total time of the operation
'''

class Time(BaseModel):
    name: str = Field('fill', alias = 'name')
    start: int = Field('0', alias = 'start')
    end: int = Field('0', alias = 'end')
    total: int = Field('0', alias = 'total')