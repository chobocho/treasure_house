기능 목록은 부마다 파일 하나다: pNN.tsv (NN = 부 번호, 두 자리).
칸: id | version | kind | title | cite-key | cite-sec | slide-id
  · version  1.N (Go 1 은 1.0, 초안은 1.28)
  · kind     lang · toolchain · runtime · stdlib · ecosystem · platform
  · title    한국어 이름 (개관 표에 그대로 실린다)
  · cite-key/cite-sec  deck/cites.py 가 docs/ 에서 찾는다. relnotes-1.N·api-1.N 이면 그 버전이 행의 버전과 같아야 한다
  · slide-id 그 기능의 전용 장. 비우면 릴리스 개관 표에만 실린다
make data-check 가 전부 검사한다(tools/make_data.py).
