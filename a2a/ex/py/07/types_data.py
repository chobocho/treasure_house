# DataPart 의 dict 는 protobuf Value 가 되었다가 돌아온다.
#   python 07/types_data.py
import json

from a2a.helpers import get_data_parts, new_data_part

# region: data
req = {"date": "2026-10-30", "nights": 1, "headcount": 30}
part = new_data_part(req)
print("종류:", part.data.WhichOneof("kind"))
fields = part.data.struct_value.fields  # 안쪽은 Struct 의 map
print("headcount:", fields["headcount"].number_value)
back = get_data_parts([part])[0]
print("돌아온 값:", json.dumps(back, sort_keys=True))
print("같은가?", back == req)  # 30.0 == 30 은 참이다
print("타입:", type(back["headcount"]).__name__)
# endregion
