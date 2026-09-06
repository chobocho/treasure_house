# 사실 검증 대장 (claims ledger)

> 덱에 들어가는 모든 역사·하드웨어·상수 주장은 여기에 출처와 함께 기록한다.
> 상태: 확인 / 정정 / 미확인
> 검증일: 2026-09-06. 출처 URL은 실제로 열어 본 것만 적었다.

## A. 하드웨어 · DOS

| # | 주장 | 상태 | 확인된 값 | 출처 |
|---|---|---|---|---|
| A1 | VGA 모드 13h = 320x200, 256색, A000h 세그먼트의 선형 프레임버퍼, 정확히 64,000바이트 | 확인 | 320x200x1바이트 = 64,000바이트. 화면 버퍼는 세그먼트 0xA000의 오프셋 0~63,999. 1987년 IBM PS/2와 함께 도입된 MCGA/VGA 표준 256색 모드 | https://en.wikipedia.org/wiki/Mode_13h |
| A2 | VGA DAC는 채널당 6비트 → 262,144색, 팔레트 256엔트리 | 확인 | DAC 내부에 18비트(R/G/B 각 6비트) 레지스터 256개. 각 성분 0~63이므로 64^3 = 262,144색 중 256색 동시 표시 | http://www.osdever.net/FreeVGA/vga/colorreg.htm , https://moddingwiki.shikadi.net/wiki/VGA_Palette |
| A3 | PIT(8253/8254) 입력 클럭 1,193,182 Hz, 기본 분주값 65,536 → 약 18.2065 Hz | 확인(정밀값 주의) | 정확한 값은 14.31818 MHz / 12 = **1,193,181.8181... Hz**이고 1,193,182는 흔히 쓰는 반올림값이다. 65,536으로 나누면 18.2065 Hz(= 54.9254 ms/틱). 자료에 따라 1193181 / 1193182가 혼용됨 | https://wiki.osdev.org/Programmable_Interval_Timer , https://en.wikibooks.org/wiki/X86_Assembly/Programmable_Interval_Timer |
| A4 | 리얼 모드 DOS의 컨벤셔널 메모리 640 KB 한계 | 확인 | 8088의 20비트 주소선 → 1 MiB 주소공간. IBM이 640 KB~1 MB 구간을 BIOS·어댑터 ROM·비디오 버퍼용으로 예약해 0x00000~0x9FFFF(640 KB)가 프로그램용으로 남음 | https://en.wikipedia.org/wiki/Conventional_memory , https://en.wikipedia.org/wiki/DOS_memory_management |
| A5 | 8086/286/386SX는 온칩 FPU 없음, 386DX는 387 필요, 486DX는 FPU 내장, 486SX는 미내장 | 확인 | 8087(1980)은 8086/8088용 최초의 외장 FPU, 80287은 80286용. 386DX는 별도 80387, 386SX는 80387SX가 필요. 1991년 말 Intel이 저가형 486SX를 내놓으면서 기존 제품을 486DX로 개명 — 둘의 유일한 차이는 FPU 내장 여부 | https://en.wikipedia.org/wiki/Intel_8087 , https://en.wikipedia.org/wiki/Intel_80387SX , https://www.os2museum.com/wp/486-overdrive/ |
| A6 | 모드 X(언체인드 플래너 320x240)가 존재하며 정사각 픽셀을 준다. 대중화한 사람은 Michael Abrash, Dr. Dobb's Journal | 확인 | 320x240 256색. 모드 13h의 약간 세로로 늘어난 픽셀 대신 정사각 픽셀. **1991년 7월** Dr. Dobb's Journal "Ramblings in Realtime" 칼럼에서 Abrash가 처음 공개적으로 소개. VGA 플래너(언체인드) 모드를 써서 256 KB 전체를 버퍼로 활용 | https://en.wikipedia.org/wiki/Mode_X , https://www.phatcode.net/res/224/files/html/ch47/47-02.html |

## B. 기하 용어

| # | 주장 | 상태 | 확인된 값 | 출처 |
|---|---|---|---|---|
| B7 | 진짜 아이소메트릭: 화면상 세 축이 서로 120도, 카메라 경사 arctan(1/sqrt2) = 35.264도, 지면 축의 화면 기울기 30도 | 확인 | 아이소메트릭은 세 좌표축이 균등 단축되고 축 사이 각이 120도인 축측투영. 큐브를 수직축 기준 ±45도 회전 후 수평축 기준 약 35.264도(정확히 arcsin(1/sqrt3) = arctan(1/sqrt2)) 회전. 지면 축은 수평에 대해 30도 | https://en.wikipedia.org/wiki/Isometric_projection |
| B8 | "2:1 다이메트릭"(가로 2px당 세로 1px)의 화면 각도 = arctan(1/2) = 26.565도. 엄밀히는 dimetric이지만 게임계는 관행적으로 isometric이라 부른다 | 확인 | 픽셀아트에서 가장 흔한 변형은 2:1 픽셀 비율이며 축이 수평에 대해 약 26.565도. 30도로 그리면 픽셀이 규칙적으로 떨어지지 않아 당시 하드웨어에서 2:1을 택했다. 수직축이 나머지 두 축과 다르게 취급되므로 기술적으로는 dimetric이지만 업계는 여전히 isometric이라 부른다 | https://en.wikipedia.org/wiki/Isometric_video_game_graphics , https://gridmakerpro.com/grids/perspective/dimetric/ |
| B9 | arctan(1/2) = 26.5651도, arctan(1/sqrt2) = 35.2644도 | 확인 | 직접 계산: arctan(0.5) = 26.56505117707799도, arctan(1/sqrt2) = 35.264389682754654도(= arcsin(1/sqrt3)) | 로컬 계산(Python math), 각도 정의는 https://en.wikipedia.org/wiki/Isometric_projection |

## C. 게임 역사

| # | 주장 | 상태 | 확인된 값 | 출처 |
|---|---|---|---|---|
| C10 | Zaxxon — 1982, Sega, 아케이드, 축측투영 | 확인 | 1982년 Sega가 개발·발매한 아이소메트릭 슈터. 축측(axonometric) 투영을 처음 사용한 게임으로, 이름 자체가 AXONometric에서 왔다 | https://en.wikipedia.org/wiki/Q*bert (Zaxxon 선행 언급), https://ultimatepopculture.fandom.com/wiki/Zaxxon |
| C11 | Q*bert — 1982, Gottlieb, Warren Davis · Jeff Lee 제작 | 확인 | 1982년 Gottlieb가 아케이드용으로 개발·발매. 설계는 Warren Davis와 Jeff Lee(Lee가 캐릭터·원안, Davis가 구현). 아이소메트릭 그래픽으로 의사 3D 효과 | https://en.wikipedia.org/wiki/Q*bert |
| C12 | Knight Lore — 1984, Ultimate Play the Game, "Filmation" 엔진, ZX Spectrum | 확인 | 1984년 11월 ZX Spectrum으로 발매. Ultimate Play the Game(창업자 Chris·Tim Stamper) 개발·발매. Filmation 엔진은 이미지 마스킹으로 깊이 우선순위를 흉내냈다 | https://en.wikipedia.org/wiki/Knight_Lore |
| C13 | Ultima VIII: Pagan — 1994, Origin Systems, DOS | 확인 | 1994년 3월 23일 DOS 전용으로 Origin Systems가 개발·발매 | https://en.wikipedia.org/wiki/Ultima_VIII:_Pagan |
| C14 | Little Big Adventure(Relentless) — 1994, Adeline Software International, DOS, 아이소메트릭 | 확인(보완) | 1994년, 프랑스 Adeline Software 개발, **퍼블리셔는 Electronic Arts**, 감독 Frédérick Raynal. 북미 제목 Relentless. 아이소메트릭 시점 + 실제 3D 폴리곤 캐릭터 | https://en.wikipedia.org/wiki/Little_Big_Adventure |
| C15 | X-COM: UFO Defense(UFO: Enemy Unknown) — 1994, Mythos Games / MicroProse, DOS, 아이소메트릭 | 확인 | 1994년, Mythos Games와 MicroProse 개발, MicroProse가 MS-DOS·Amiga 등으로 발매. 지상전은 아이소메트릭 시점의 턴제 전술 | https://en.wikipedia.org/wiki/UFO:_Enemy_Unknown |
| C16 | Crusader: No Remorse — 1995, Origin Systems, DOS | 확인(보완) | 1995년 9월 MS-DOS로 발매. Origin Systems 개발, **퍼블리셔는 Electronic Arts**. Ultima VIII: Pagan 엔진을 강화해 사용한 2D 아이소메트릭 슈터 | https://en.wikipedia.org/wiki/Crusader:_No_Remorse |
| C17 | Fallout — 1997, Interplay/Black Isle, DOS와 Windows 동시 출시 | 정정 | 1997년 10월 10일 북미에서 MS-DOS·Windows용으로 발매된 것은 맞다. 다만 개발은 **Interplay의 RPG 부서**가 했고, "Black Isle Studios"라는 이름은 **Fallout 2 개발 중에 붙은 것**이므로 1편의 개발사로 Black Isle을 적으면 시대착오다 | https://en.wikipedia.org/wiki/Fallout_(video_game) , https://en.wikipedia.org/wiki/Fallout_(franchise) |
| C18 | Diablo — 1996년 12월, Blizzard North, Windows 95(DOS판 없음) | 부분 정정 | DOS판이 없다는 점은 확인(플랫폼은 Windows / PlayStation / Mac OS). 날짜는 자료가 갈린다: Blizzard 계열 위키는 1996년 12월 31일 출시(골드는 12월 하순), 영문 위키백과 인포박스의 **북미 정식 발매일은 1997년 1월 3일**이다. 흔히 인용되는 1996년 11월 30일은 오류 | https://en.wikipedia.org/wiki/Diablo_(video_game) , https://diablo-archive.fandom.com/wiki/Diablo_I |
| C19 | 어스토니시아 스토리 — 1994, 손노리, DOS, 쿼터뷰인가? | 부분 확인 | 1994년 손노리 제작, **유통은 소프트라이(Softry)**, MS-DOS. 시점은 MobyGames 계열 DB에서 "Diagonal-down"(사선 부감)으로 분류된다. 즉 넓은 의미의 쿼터뷰지만, 2:1 다이메트릭 격자라는 근거는 확인하지 못했다 | https://ko.wikipedia.org/wiki/어스토니시아_스토리 , https://www.myabandonware.com/game/astonishia-story-blk |
| C20 | 창세기전 — 1995, 소프트맥스, DOS, 전투가 쿼터뷰인가? | 부분 확인 | 1995년 12월 3.5인치 디스켓판으로 발매, 소프트맥스 개발, MS-DOS. 국산 SRPG. 시점은 MobyGames 계열 DB에서 "Diagonal-down"으로 분류(유통은 G&M Entertainment로 기재). "전투 화면이 2:1 쿼터뷰"라는 명시적 1차 서술은 확인하지 못했다 | https://ko.wikipedia.org/wiki/창세기전 , https://www.myabandonware.com/game/the-war-of-genesis-ifh , https://www.gamemeca.com/view.php?gid=124392 |
| C21 | SimCity 2000 — 1993, Maxis, 다이메트릭 시점 | 확인 | 1993년 Maxis. 전작의 부감 시점 대신 "near-isometric dimetric view"를 도입했고, 고저차와 지하 레이어가 추가됨 | https://en.wikipedia.org/wiki/SimCity_2000 |
| C22 | Populous — 1989, Bullfrog, 아이소메트릭 | 확인 | 1989년 Bullfrog Productions. 아이소메트릭 시점으로 지형 조작을 표현한 초기 대표작(갓 게임 장르의 시초) | https://en.wikipedia.org/wiki/Isometric_video_game_graphics |

## D. 알고리즘 · 상수

| # | 주장 | 상태 | 확인된 값 | 출처 |
|---|---|---|---|---|
| D23 | Borland Turbo C/C++ rand(): x = 22695477*x + 1 (mod 2^32), 반환 (x>>16)&0x7FFF | 부분 정정 | 승수 22695477, 증분 1은 확인. 다만 영문 위키백과 LCG 표는 Borland C/C++ 항목의 **모듈러스를 2^31**로, 출력을 "bits 30..16 in rand(), 30..0 in lrand()"로 적는다. 실제로 2^32와 2^31 중 어느 쪽을 써도 bits 30..16은 동일하므로 rand() 출력은 같다(로컬에서 5스텝 대조해 일치 확인). "mod 2^32"라고 쓸 거면 각주로 이 사정을 밝히는 편이 안전하다. 위키 표에 "Turbo C++" 별도 항목은 없다(Turbo Pascal 4.0은 2^32/134775813/1로 별도 기재) | https://en.wikipedia.org/wiki/Linear_congruential_generator |
| D24 | Hull-Dobell 정리(1962): c와 m이 서로소, a-1이 m의 모든 소인수로 나눠떨어짐, m이 4의 배수면 a-1도 4의 배수 | 확인 | 저자 T. E. Hull, A. R. Dobell, "Random Number Generators", SIAM Review 4(3), 230-254, 1962년 7월. 조건 3개가 위키백과 서술과 일치(필요충분조건) | https://en.wikipedia.org/wiki/Linear_congruential_generator , https://epubs.siam.org/doi/10.1137/1004061 |
| D25 | 다이아몬드-스퀘어: Fournier, Fussell, Carpenter, CACM 1982, "Computer rendering of stochastic models" | 확인 | Fournier, Alain; Fussell, Don; Carpenter, Loren (1982년 6월). "Computer rendering of stochastic models". Communications of the ACM 25(6): 371-384. SIGGRAPH 1982에서 소개 | https://en.wikipedia.org/wiki/Diamond-square_algorithm , https://dl.acm.org/doi/10.1145/358523.358553 |
| D26 | CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, 반사 없음, xorout 0x0000, "123456789" 체크값 0x29B1 | 확인 | RevEng 카탈로그: width=16 poly=0x1021 init=0xffff refin=false refout=false xorout=0x0000 check=0x29b1 residue=0x0000, 정식 명칭 **CRC-16/IBM-3740**(CCITT-FALSE는 별칭). 로컬 구현으로 0x29B1 재현 확인 | https://reveng.sourceforge.io/crc-catalogue/16.htm |
| D27 | CRC-16/ARC: poly 0x8005 반사, init 0x0000, 체크값 0xBB3D | 확인 | width=16 poly=0x8005 init=0x0000 refin=true refout=true xorout=0x0000 check=0xbb3d residue=0x0000. 로컬 구현(0xA001 반사 다항식)으로 0xBB3D 재현 확인 | https://reveng.sourceforge.io/crc-catalogue/16.htm |
| D28 | DOOM은 16.16 고정소수점, FRACBITS = 16 | 확인 | 공개된 DOOM 소스 m_fixed.h: `#define FRACBITS 16`, `#define FRACUNIT (1<<FRACBITS)`, `typedef int fixed_t;` | https://raw.githubusercontent.com/id-Software/DOOM/master/linuxdoom-1.10/m_fixed.h |
| D29 | 브레젠험 직선 알고리즘 — J. E. Bresenham, IBM Systems Journal, 1965 | 확인 | Bresenham, J. E. "Algorithm for computer control of a digital plotter", IBM Systems Journal 4(1), 25-30, 1965. 곱셈·나눗셈 없이 구현 가능하다는 것이 논문의 요지 | https://dl.acm.org/doi/10.1147/sj.41.0025 , https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm |
| D30 | alpha max plus beta min: alpha = 0.960433870103, beta = 0.397824734759, 최대 오차 약 3.96% | 확인 | 위키백과가 최적값으로 명시하는 값과 일치하며 최대 오차 3.96%. 로컬에서 0~90도를 1/1000도 간격으로 스윕해 최대 상대오차 3.9566%를 재현 | https://en.wikipedia.org/wiki/Alpha_max_plus_beta_min_algorithm |
| D31 | 1/sqrt(2)의 16.16 고정소수점 = round(65536/sqrt2) = 46341 | 확인 | 65536/sqrt(2) = 46340.950011841574 → 반올림 46341. 46341/65536 = 0.7071075439, 참값 0.7071067812와의 오차 약 7.6e-7 (계산으로 검증, 출처 불필요) | 로컬 계산 |
| D32 | A* 옥타일 휴리스틱(직선 10, 대각 14): h = 10*(dx+dy) - 6*min(dx,dy), 14는 10*sqrt2 = 14.142의 정수 근사, 8방향 격자에서 허용적·일관적 | 확인 | 10*sqrt(2) = 14.142135623730951이므로 14는 그 정수 근사가 맞다. 항등식 10*(dx+dy) - 6*min = 14*min + 10*(max-min)을 dx,dy 0..5 전 범위에서 확인 — 즉 장애물이 없을 때의 정확한 이동 비용이므로 그 비용 모델에서 허용적이자 일관적이다(대각 실비용을 10*sqrt2로 두면 h가 과소평가가 되어 여전히 허용적). 옥타일은 8방향 격자에서 권장되는 표준 휴리스틱 | https://theory.stanford.edu/~amitp/GameProgramming/Heuristics.html , https://www.gameaipro.com/GameAIPro/GameAIPro_Chapter17_Pathfinding_Architecture_Optimizations.pdf |

## 정정이 필요한 항목

- **A3 (PIT 클럭):** 1,193,182 Hz는 반올림값이다. 정확히는 14.31818 MHz / 12 = **1,193,181.8181... Hz**. 덱에서 "정확히 1,193,182 Hz"라고 쓰지 말고 "약 1.193182 MHz(정확히는 14.31818 MHz의 1/12)"로 쓸 것. 파생값 18.2065 Hz, 54.9254 ms는 그대로 써도 된다.
- **C14 / C16 (퍼블리셔):** Little Big Adventure와 Crusader: No Remorse는 개발사(Adeline / Origin)와 별개로 **퍼블리셔가 Electronic Arts**다. "Adeline이 발매", "Origin이 발매"로 쓰면 부정확.
- **C17 (Fallout):** 1997년 10월 10일 MS-DOS·Windows 출시는 맞지만, **Black Isle Studios라는 이름은 Fallout 2 개발 중에 생겼다**. 1편의 개발 주체는 "Interplay의 RPG 부서". 덱에는 "Interplay(후일의 Black Isle)" 정도로 표기할 것.
- **C18 (Diablo):** "1996년 12월"은 출하/골드 기준이고, 영문 위키백과 인포박스의 **북미 발매일은 1997년 1월 3일**이다. 덱에서 단정하려면 "1996년 말 출하, 1997년 1월 3일 북미 정식 발매"로 병기할 것. DOS판이 없다는 주장은 확인됨(Windows/PlayStation/Mac OS만 존재).
- **D23 (Borland rand):** 승수 22695477·증분 1은 확인되지만, 영문 위키백과는 모듈러스를 **2^31**로 기재한다. 2^32로 쓰든 2^31로 쓰든 (x>>16)&0x7FFF 출력은 동일함을 수치로 확인했으므로, 덱에서는 "32비트 상태에 대해 x = 22695477x + 1, 출력은 비트 30..16"처럼 출력 비트 기준으로 서술하는 편이 안전하다.
- **C19 (어스토니시아 스토리) — 부분 미확인:** 1994 / 손노리 / MS-DOS는 확인. 유통사는 소프트라이. 시점은 DB상 "Diagonal-down"으로만 확인되며, **2:1 다이메트릭 격자라는 증거는 찾지 못했다**. 덱에서 "정통 2:1 쿼터뷰의 한국 사례"로 단정하지 말 것.
- **C20 (창세기전) — 부분 미확인:** 1995년 12월 / 소프트맥스 / MS-DOS / SRPG는 확인. 시점도 DB상 "Diagonal-down". 다만 **"전투 화면이 쿼터뷰"라는 명시적 1차 서술은 확보하지 못했다**. 스크린샷 근거를 별도로 확보하기 전에는 단정 표현을 피할 것.
- **C22 (Populous) 주의:** 아이소메트릭으로 널리 서술되지만, B8의 논지대로 실제 픽셀 격자는 2:1 다이메트릭 계열이다. 덱에서 B8과 C22를 나란히 놓을 때 모순되어 보이지 않도록 "관행적으로 아이소메트릭이라 부른다"는 단서를 달 것.

## 슬라이드 대응

| # | 슬라이드 id |
|---|---|
