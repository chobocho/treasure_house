기능 목록은 부(또는 부를 나눈 조각)마다 파일 하나다: pNN.tsv · pNNb.tsv …
칸: id | version | kind | title | cite-key | cite-sec | slide-id | msgid
  · version  releases.tsv 의 버전(끝의 .0 은 있어도 없어도 같다: 8 = 8.0)
  · kind     lang · runtime · compiler · library · ecosystem · platform
  · title    한국어 이름 (버전 개관 표에 그대로 실린다)
  · cite-key/cite-sec  deck/cites.py 가 docs/ 에서 찾는다(§ 제목 또는 .cs 의 한 줄 전체)
  · slide-id 그 기능의 전용 장(pN-v<배지 class>-<slug>). 비우면 개관 표에만 실린다
  · msgid    컴파일러가 버전을 확인하는 기능이면 data/langgates.tsv 의 MessageID —
             있으면 그 게이트의 버전과 행의 버전이 같아야 한다(기억으로 적은 버전이 걸린다)
make data-check 가 전부 검사한다(tools/make_data.py).
