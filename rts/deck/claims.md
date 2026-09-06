# 사실 검증 대장 (claims ledger)

> 덱에 들어가는 모든 역사·하드웨어·상수 주장은 여기에 출처와 함께 기록한다.
> 상태: 확인 / 부분 확인 / 정정 / 부분 정정 / 미확인
> 검증일: 2026-09-06. 출처 URL은 실제로 열어 본 것만 적었다.

## A. 하드웨어 · DOS

| # | 주장 | 상태 | 확인된 값 | 출처 |
|---|---|---|---|---|
| A1 | VGA 모드 13h = 320x200 256색, A000h 세그먼트의 선형 프레임버퍼, 정확히 64,000바이트 | 확인 | 320x200x1바이트 = 64,000바이트. 화면 버퍼는 세그먼트 0xA000의 오프셋 0~63,999. 1987년 도입된 VGA 표준 256색 모드 | https://en.wikipedia.org/wiki/Mode_13h |
| A2 | VGA DAC는 채널당 6비트 → 262,144색, 팔레트 256엔트리 | 확인 | DAC 내부 18비트(R/G/B 각 6비트) 레지스터 256개. 성분당 0~63이므로 64^3=262,144색 중 256색 동시 표시 | http://www.osdever.net/FreeVGA/vga/colorreg.htm , https://moddingwiki.shikadi.net/wiki/VGA_Palette |
| A3 | PIT(8253/8254) 입력 클럭 1,193,182 Hz, 분주값 65,536 → 18.2065 Hz(54.925ms/틱); 채널 2가 PC 스피커 구동; 분주값=1193182/목표주파수 | 확인(정밀값 주의) | 정확히는 14.31818MHz/12=1,193,181.8181...Hz이고 1,193,182는 반올림값. 채널 2 선택은 포트 0x43에 비트 1:0=10. 분주값 계산식 "1193182/f"은 OSDev 문서 그대로 | https://wiki.osdev.org/Programmable_Interval_Timer , https://forum.osdev.org/viewtopic.php?f=1&t=27024 |
| A4 | 386/486에서 386SX·486SX는 FPU 없음, 이 때문에 DOS 게임이 정수·고정소수점 연산을 씀 | 확인 | 386DX는 별도 80387, 386SX는 80387SX 필요. 486DX는 FPU 내장, 486SX는 미내장(486DX를 저가화하며 FPU 비활성화). FPU가 희귀·고가 옵션이던 시절이라 최대 호환을 위해 정수 연산을 우선했다는 것이 통설 | https://en.wikipedia.org/wiki/Intel_80387SX , https://en.wikipedia.org/wiki/Intel_8087 |
| A5 | VESA/SVGA 640x480 256색 모드가 1995년 DOS 게임에서 쓰임 | 부분 확인 | 모드 101h(640x480 256색 정사각픽셀)는 VESA 표준. "정사각픽셀 SVGA"는 1994년부터 게임계에 확산되기 시작했고, Warcraft II(1995)가 네이티브로 640x480 SVGA를 채택. 다만 1995년 "널리 쓰였다"고 단정할 만한 통계 출처는 못 찾음 | https://lilura1.blogspot.com/2022/06/Square-pixel-SVGA-Games-on-IBM-PC-MS-DOS.html , https://dosbox-x.com/wiki/Guide:Video-card-support-in-DOSBox%E2%80%90X |
| A6 | INT 33h 마우스 드라이버(함수 0=리셋, 함수 3=위치·버튼 읽기), INT 9=키보드 인터럽트 | 확인 | INT 33/AX=0000h는 리셋+상태읽기, AX=0003h는 위치(x,y)와 버튼 상태 반환. INT 9는 IRQ1/8259를 통해 스캔코드를 BIOS 키보드 버퍼(40:1Eh)에 저장하는 키보드 하드웨어 인터럽트 | https://stanislavs.org/helppc/int_33.html , https://stanislavs.org/helppc/int_9.html |
| A7 | EMS(LIM 4.0) vs XMS 메모리 차이 | 확인 | EMS/LIM 4.0(1987)은 384KB 상위메모리 영역에 64KB 창(16KB 페이지 4개)으로 뱅크스위칭, 최대 32MiB까지 지원(3.2는 8MB). XMS는 1MB 위의 확장메모리에 직접 접근하는 API로 XMS 2.0(1988)은 최대 64MB, XMS 3.0(1991)은 최대 4GB. EMS는 구형 PC 호환용 하드웨어적 우회, XMS는 신형 프로세서의 직접 접근 | https://en.wikipedia.org/wiki/Expanded_memory , https://en.wikipedia.org/wiki/Extended_memory |
| A8 | IPX/SPX(Novell)가 DOS 멀티플레이어 LAN 프로토콜, NetBIOS 연동, 널모뎀 시리얼·14.4/28.8kbps 모뎀 사용 | 부분 확인 | IPX/SPX는 Novell NetWare의 프로토콜로 "DOS 시대 멀티플레이어 게임의 사실상 표준"(Doom, Duke3D 등). NetBIOS는 IPX 위에서 NBIPX로 동작. 널모뎀 케이블(2·3핀 교차) 직결 방식도 다수 게임이 지원(Doom SERSETUP 등). 다만 14.4/28.8kbps 모뎀과 특정 게임의 연결을 명시한 1차 자료는 확보하지 못했고, 이는 V.32bis/V.34 표준 속도로 일반적으로 알려진 사실에 가깝다 | https://en.wikipedia.org/wiki/IPX/SPX , https://en.wikipedia.org/wiki/Null_modem |

## B. RTS 게임 고증

| # | 주장 | 상태 | 확인된 값 | 출처 |
|---|---|---|---|---|
| B9 | Herzog Zwei — 1989, Technosoft, Mega Drive/Genesis, 프로토-RTS | 확인 | 일본 1989년·북미/유럽 1990년 발매. 개발 Technosoft, 발매 Sega(일본은 Technosoft 자체 발매). "Dune II보다 앞선" 초기 RTS로 명시되며 Warcraft·StarCraft·C&C 개발자들의 영감으로 인용됨 | https://en.wikipedia.org/wiki/Herzog_Zwei |
| B10 | Dune II — 1992, Westwood, Virgin, MS-DOS, 320x200, 타일 16x16?, 맵 크기, 유닛 한도 | 부분 확인 | 1992년 Westwood Studios 개발, Virgin Games 발매, MS-DOS 최초 출시(이후 Amiga·Genesis 등 이식) 확인. 맵은 64x64(최대 4096타일), 초기 캠페인 맵은 32x32. 유닛 한도는 플레이어 25기·CPU 20기(전체 합산 약 80기 상한)로 게임 자체의 SCENARIO.PAK "Maxunit=25" 값에 근거. **타일 픽셀 크기(16x16 여부)는 확인하지 못했다** | https://en.wikipedia.org/wiki/Dune_II , https://forum.dune2k.com/topic/23796-does-the-ai-adhere-to-the-unit-limit-of-25-per-house/ |
| B11 | Warcraft: Orcs & Humans — 1994, Blizzard, DOS, 320x200, 타일 32x32?, 4유닛 선택 한도 | 부분 정정 | 1994년 11월 15일 북미 MS-DOS 발매(북미 발매사 Blizzard, 유럽은 Interplay), 1996년 Mac 이식 확인. "클릭 또는 밴드박싱으로 최대 4기까지 그룹 선택"이 위키백과에 명시되어 4유닛 한도 확인. 해상도 320x200(모드13h)은 통념상 확실하나 원 게임 문서로 재확인은 못함. **타일은 32x32 가 아니라 16x16** — 원작 데이터를 그대로 읽는 재구현 War1gus 의 `scripts/stratagus.lua` 가 `SetTileSize(16, 16)` 으로 설정하고 "graphics are 320x200, but rendered 320x240" 이라 주석함(3차 리뷰, 2026-09-06 확인). Stratagus tileset 문서의 32x32 는 Warcraft II(Wargus) 기준이었음. 원작 1차 문서는 여전히 못 찾음 | https://en.wikipedia.org/wiki/Warcraft:_Orcs_%26_Humans , https://raw.githubusercontent.com/Wargus/war1gus/master/scripts/stratagus.lua |
| B12 | Warcraft II: Tides of Darkness — 1995, Blizzard, DOS, 640x480 SVGA, 맵 32~128, 9유닛 선택 | 확인 | 1995년 12월 MS-DOS 발매(북미 발매사 Davidson & Associates, 유럽 Zablac Entertainment). "Warcraft 1의 320x200 QVGA에서 정사각픽셀 640x480 SVGA로 해상도가 두 배가 됐다"고 다수 자료 일치. PUD 맵 포맷은 32x32/64x64/96x96/128x128 네 크기를 지원. 9유닛 선택 한도는 콘솔판(더 많은 유닛 선택 허용)과의 비교 서술에서 간접 확인 | https://en.wikipedia.org/wiki/Warcraft_II:_Tides_of_Darkness , https://formats.kaitai.io/warcraft_2_pud/ |
| B13 | Command & Conquer — 1995, Westwood, DOS 320x200(Gold판 640x400), 셀 크기 24x24 | 확인 | 1995년 Westwood Studios 개발·발매(유럽은 Virgin Interactive), DOS판은 MCGA 320x200. 지형 셀은 24x24픽셀(OpenRA 진영의 포맷 문서 기준). Windows 95용 재발매 "C&C Gold"는 640x400(및 640x480, 종횡비 왜곡) 지원 | https://en.wikipedia.org/wiki/Command_%26_Conquer_(1995_video_game) , https://moddingwiki.shikadi.net/wiki/Command_%26_Conquer_Tileset_Format |
| B14 | Command & Conquer: Red Alert — 1996, Westwood | 확인 | 북미 1996년 11월 22일, 유럽 12월 4일 발매. Westwood Studios 개발·발매, 플랫폼은 MS-DOS·Windows·(후속) PlayStation | https://en.wikipedia.org/wiki/Command_%26_Conquer:_Red_Alert |
| B15 | Age of Empires — 1997, Ensemble/Microsoft, Windows 95 전용(DOS판 없음) | 확인 | 1997년 10월(북미 10/13) 발매, 개발 Ensemble Studios, 발매 Microsoft. 최소사양이 Windows 95/NT4 SP3 + DirectX5이며 DOS는 요구사항·플랫폼 목록 어디에도 없음(위키백과 플랫폼란: Windows/Windows Mobile/Mac) | https://en.wikipedia.org/wiki/Age_of_Empires_(video_game) |
| B16 | StarCraft — 1998, Blizzard, Windows(DOS 없음), 타일 32x32 | 확인 | 1998년 3월 31일 Windows 발매(1999년 Mac 이식), DOS판 없음. 맵 타일은 32x32픽셀 이미지 단위로 통행성·고저·시야 정보를 가짐 | https://en.wikipedia.org/wiki/StarCraft_(video_game) |
| B17 | Total Annihilation — 1997, Cavedog, 3D 유닛 방식 | 부분 확인 | 1997년 9월 30일 Windows·Mac 발매(DOS 없음), Cavedog 개발. 유닛·건물은 실시간 3D 렌더링이 맞지만, **지형은 완전한 3D가 아니라 높이값을 가진 2D 래스터(하이트맵)** — "true 3D terrain"이라 단정하면 과장이다. 유닛 상한은 최초 250기, 이후 패치로 500기 | https://en.wikipedia.org/wiki/Total_Annihilation |
| B18 | 충무공전(1996?)·임진록(HQ team, DOS?) | 정정 | 충무공전: 1996년, 트리거소프트+HQ team 합작 개발(트리거소프트 발매), MS-DOS, RTS — **다만 나무위키뿐 1차/위키백과 출처가 없다.** 임진록: 1997년 1월, HQ팀(드림웨어) 개발, 유통 삼성전자(나무위키만 명시)이며 **플랫폼은 DOS가 아니라 Windows**(한국어 위키백과 인포박스 명시) — 과제 전제(HQ Team·DOS)의 플랫폼 부분은 오류. 장르는 두 게임 모두 "실시간전략(시뮬레이션)"으로 기재됨 | https://namu.wiki/w/%EC%B6%A9%EB%AC%B4%EA%B3%B5%EC%A0%84 , https://ko.wikipedia.org/wiki/%EC%9E%84%EC%A7%84%EB%A1%9D_(%EB%B9%84%EB%94%94%EC%98%A4_%EA%B2%8C%EC%9E%84) , https://namu.wiki/w/%EC%9E%84%EC%A7%84%EB%A1%9D(%EA%B2%8C%EC%9E%84) |

## C. 논문 · 알고리즘 출처

| # | 주장 | 상태 | 확인된 값 | 출처 |
|---|---|---|---|---|
| C19 | "1500 Archers on a 28.8" — Terrano & Bettner, GDC 2001, 2턴 지연 락스텝 | 정정 | 원문 PDF 표지 저자 순서는 **Paul Bettner가 먼저, Mark Terrano가 다음**("Paul Bettner / Mark Terrano", 각 Ensemble Studios 이메일 병기) — 흔히 "Terrano & Bettner"로 인용되는 것과 반대다. GDC2001 2001-03-22 14:30 발표. 원문에 "commands were being processed for one turn... and sent out for execution two turns in the future"라고 명시되어 2턴 지연 락스텝이 정확히 확인됨. 시뮬레이션은 "deterministic"이라고도 명시 | https://zoo.cs.yale.edu/classes/cs538/readings/papers/terrano_1500arch.pdf (원문 직접 확인) |
| C20 | Lanchester's laws — F.W. Lanchester, 1916, "Aircraft in Warfare" | 확인 | 1916년 저서 "Aircraft in Warfare: The Dawn of the Fourth Arm"에서 선형 법칙(고대 백병전, 1대1 소모)과 제곱 법칙(원거리 화기전, n배 병력差는 n² 배 화력 우위 필요) 제시 | https://en.wikipedia.org/wiki/Lanchester%27s_laws |
| C21 | Hull & Dobell 1962, SIAM Review, 완전주기 LCG 3조건 | 확인 | T.E. Hull, A.R. Dobell, "Random Number Generators", SIAM Review 4(3), 230-254, 1962. 3조건: (1) c와 m이 서로소 (2) a-1이 m의 모든 소인수로 나뉨 (3) m이 4의 배수면 a-1도 4의 배수 — 위키백과 서술과 일치 | https://en.wikipedia.org/wiki/Linear_congruential_generator |
| C22 | Borland C rand(): 승수 22695477, 증분 1, 모듈러스 2^32 | 부분 정정 | 승수·증분은 확인되나 위키백과 LCG 표는 Borland C/C++의 **모듈러스를 2^31**로 적고 출력은 "rand()=비트 30..16, lrand()=비트 30..0"이라 기재한다. "2^32"라고 쓰려면 출력 비트 기준 서술로 보완할 것 | https://en.wikipedia.org/wiki/Linear_congruential_generator |
| C23 | HPA* — Botea, Müller, Schaeffer, JGD 2004, 최적 대비 약 1% 이내 | 부분 확인 | Journal of Game Development(2004) 게재는 다수 2차 출처(Semantic Scholar 등)에서 일치. "최적화된 A* 대비 최대 10배 빠르면서 최적해의 약 1% 이내"라는 수치는 여러 2차 자료에 반복 인용되나, 원문 PDF는 폰트 인코딩 문제로 텍스트 추출이 안 돼 1차 문서로 직접 재확인하지 못했다 | https://www.semanticscholar.org/paper/Near-Optimal-Hierarchical-Path-Finding-Botea-M%C3%BCller/b0f0432ba69e4d730b93a75e3d19c8e9d811efac |
| C24 | JPS — Harabor & Grastien, AAAI 2011, A*와 동일 비용의 최적해 | 확인 | Daniel Harabor, Alban Grastien, "Online Graph Pruning for Pathfinding on Grid Maps", AAAI 2011(Vol.25 No.1). 초록에 "always computes optimal solutions"이라 명시, 균일비용 격자에서 A*와 동일 비용 경로를 보장하며 A* 대비 한 자릿수 이상 가속 | https://ojs.aaai.org/index.php/AAAI/article/view/7994 |
| C25 | 다이아몬드-스퀘어 — Fournier, Fussell, Carpenter, CACM 1982 | 확인 | Fournier, Fussell, Carpenter, "Computer rendering of stochastic models", CACM 25(6), 371-384, 1982년 6월. SIGGRAPH 1982에서 소개 | https://en.wikipedia.org/wiki/Diamond-square_algorithm , https://dl.acm.org/doi/10.1145/358523.358553 |
| C26 | 중점원 알고리즘 — Bresenham 1977(venue), Pitteway 1967(선행) | 확인 | Bresenham, "A linear algorithm for incremental digital display of circular arcs", CACM 20(2), 100-106, 1977년 2월. Pitteway, "Algorithm for drawing ellipses or hyperbolae with a digital plotter", Computer Journal 10(3), 282-289, 1967년 11월 — 원의 특수사례를 포함하는 원추곡선 알고리즘으로 Bresenham보다 10년 앞섬 | https://dl.acm.org/doi/10.1145/359423.359432 , https://www.semanticscholar.org/paper/Algorithm-for-drawing-ellipses-or-hyperbolae-with-a-Pitteway/f4a978f05fbe39054b5db0306658751ca09ce61a |
| C27 | 플로우필드/데이크스트라맵 — "Dijkstra Maps Are Awesome"(roguebasin), Supreme Commander 2 GDC 2011(Emerson), Game AI Pro | 정정 | roguebasin 글의 정확한 제목은 "Dijkstra Maps Are Awesome"이 아니라 **"The Incredible Power of Dijkstra Maps"**(Brogue 제작자 작성)다. Elijah Emerson의 "Crowd Pathfinding and Steering Using Flow Field Tiles"는 Supreme Commander 2 작업 경험을 바탕으로 Game AI Pro(2013) 23장에 수록됨(GDC 2011 발표라는 확증은 못 얻음) | https://www.roguebasin.com/index.php/The_Incredible_Power_of_Dijkstra_Maps , https://www.gameaipro.com/GameAIPro/GameAIPro_Chapter23_Crowd_Pathfinding_and_Steering_Using_Flow_Field_Tiles.pdf |
| C28 | CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, "123456789"→0x29B1 | 확인 | RevEng 카탈로그: width=16 poly=0x1021 init=0xffff refin/refout=false xorout=0x0000 check=0x29b1. 정식 명칭은 **CRC-16/IBM-3740**(CCITT-FALSE는 별칭) | https://reveng.sourceforge.io/crc-catalogue/16.htm |
| C29 | FNV-1a 32비트: offset basis 2166136261, prime 16777619 | 확인 | 고안자 Fowler·Noll·Vo의 공식 문서에 "32 bit offset_basis = 2166136261", "32 bit FNV_prime = 2^24+2^8+0x93 = 16777619"로 명시. FNV-1과 FNV-1a는 같은 상수를 쓰고 XOR·곱셈 순서만 다르다 | http://www.isthe.com/chongo/tech/comp/fnv/ |
| C30 | 가우스 원 문제: 반지름 r=1..8의 격자점 수 N(r)=#{(x,y): x²+y²≤r²} | 확인 | 로컬 전수 계산 결과 r=1:5, r=2:13, r=3:29, r=4:49, r=5:81, r=6:113, r=7:149, r=8:197(중심점 포함) | 로컬 계산(Python, 전수탐색) |
| C31 | 셀룰러 오토마타 동굴 생성 "4-5 규칙" | 확인 | RogueBasin 원문: "벽 타일은 이웃 8칸 중 벽이 4개 이상이면 유지, 빈 칸은 벽이 5개 이상이면 벽이 됨"(3x3 영역에 벽 5개 이상이면 벽) — 흔히 "B5678/S45678"류 규칙으로 불림. 무작위 초기 채움 후 3~5회 반복이 일반적 | https://www.roguebasin.com/index.php/Cellular_Automata_Method_for_Generating_Random_Cave-Like_Levels |
| C32 | Warcraft II 데미지 공식: 기본데미지+관통 - 방어력, 50% 무작위 감소 변형 | 확인 | Blizzard 공식 전략 가이드(classic.battle.net)에 "(기본데미지-방어력)+관통데미지=최대데미지, 실제 데미지는 이 최대치의 50%~100% 사이 무작위"라고 명시되어 있어 커뮤니티 역산이 아니라 **공식 문서로 확인됨**. 팬 사이트 artho.com의 역산 공식도 동일 결론(ceil(최대/2)~최대) | http://classic.battle.net/war2/basic/combat.shtml , http://artho.com/warcraft/combateq.html |

## 정정이 필요한 항목

- **A3 (PIT 클럭):** "정확히 1,193,182Hz"라 쓰지 말 것. 14.31818MHz/12=1,193,181.818...Hz이며 1,193,182는 반올림값.
- **B18 (임진록 플랫폼):** DOS가 아니라 **Windows** 전용(한국어 위키백과 인포박스 확인). 덱에서 "DOS 게임"으로 단정하면 오류.
- **B18 (충무공전/임진록 출처):** 한국어 위키백과 정식 문서가 없는 항목(충무공전)이 있어 나무위키(2차 출처)에만 의존한다. 단정적 서술 자제.
- **B17 (Total Annihilation):** "최초의 완전한 3D 지형" 같은 과장 금지 — 지형은 높이값을 가진 2D 하이트맵이고, 완전 3D인 것은 유닛·건물뿐.
- **C19 (저자 순서):** "Terrano & Bettner"가 아니라 원문 표지 기준 **Paul Bettner가 1저자, Mark Terrano가 2저자**.
- **C22 (Borland rand 모듈러스):** 위키백과 LCG 표는 2^32가 아니라 **2^31**로 기재하며, 출력은 비트 30..16 기준으로 서술한다.
- **C27 (roguebasin 글 제목):** "Dijkstra Maps Are Awesome"이 아니라 정식 제목은 **"The Incredible Power of Dijkstra Maps"**.
- **C23 (HPA* 1% 수치) — 부분 확인 한계:** 다수 2차 자료가 반복 인용하는 수치이나, 원문 PDF의 폰트 인코딩 문제로 1차 문서 텍스트 재확인에는 실패했다. 덱에서 이 수치를 쓸 때 "여러 후속 문헌에서 반복 인용되는 수치"로 완곡하게 표기할 것.
- **B10 (Dune II 타일 크기), B11 (Warcraft 타일 크기) — 2차 자료뿐:** 원작 1차 문서를 찾지 못했다. Warcraft 는 War1gus 설정으로 **16x16** 이 방증되며(32x32 는 Warcraft II 의 값), 덱에서 픽셀 수치를 단정하지 말 것.
