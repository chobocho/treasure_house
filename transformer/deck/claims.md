# 주장 대장 — 이 덱이 적는 모든 사실의 출처

> **규칙: 슬라이드에 적기 전에 여기 먼저 적는다.** (PLAN.md §0.4)
>
> 논문 날짜·arXiv 번호·모델 크기·논문이 적은 하이퍼파라미터(d_model·워밍업
> 스텝·BLEU·파라미터 수) — 기억으로 적을 수 있을 것 같은 것일수록 반드시
> 틀린다. 한 줄을 여기 적는 일은 30초지만, 틀린 한 줄을 독자가 믿는 일은
> 되돌릴 수 없다.
>
> 출처의 우선순위 (위가 강하다):
>
> 1. 논문 원문 — arXiv 번호와 절·표. `make papers` 로 `papers/<키>.txt` 에
>    받아 둔 본문에서 인용한다. 기억으로 옮기지 않는다.
> 2. 공식 모델 카드·저장소 README
> 3. 위키백과 — **그 문서의 각주를 따라가 원출처를 확인한 경우에만.**
>
> 근거를 못 찾은 문장은 둘 중 하나다: 빼거나,
> 슬라이드에 `<span class="unv">미확인</span>` 을 붙여 모른다고 적는다.
>
> **지식 기준일 규율** — 2025년 이후의 일(최신 모델, 파라미터 수, 문맥 길이,
> "최고 성능")은 만들 때 WebSearch 로 다시 확인하고 본문에 "2026-09 기준" 을
> 박는다. 그런 문장이 들어갈 자리는 1부의 "오늘" 장뿐이다. (PLAN.md §0.5)

## 적는 꼴

한 줄에 주장 하나. 칸은 넷이다.

```
| 주장 | 출처 | 어떻게 확인했나 | 확인한 날 |
```

- **주장** — 슬라이드에 적힐 문장 그대로. "대략", "약" 같은 말을 빼고 수를 적는다.
- **출처** — arXiv 번호와 절·표, 모델 카드 URL 중 가장 강한 것.
- **어떻게 확인했나** — `papers/vaswani2017.txt 표 3 인용` · `WebSearch 2건 교차`
  · `py/transformerlib/model.py count_params 로 계산` 처럼, 다음 사람이 되짚을 수 있게.
- **확인한 날** — YYYY-MM-DD. 빠르게 바뀌는 사실은 이 날짜가 곧 유효기간이다.

`deck/check_claims.py` 가 조각 산문에 적힌 네 자리 연도를 전부 훑어,
이 파일이나 `data/*.tsv` 에 없으면 빌드를 멈춘다. 연도처럼 보이지만
연도가 아닌 수는 `deck/years_ok.txt` 에 적는다.

## 이미 알고 있는 함정 (PLAN.md §5 3단계에서 출처를 붙여 확정한다)

- GPT-2 small — 논문의 "117M" 과 실제 파라미터 수(묶인 임베딩 포함)의 차이
- Attention Is All You Need — arXiv v1 날짜와 NeurIPS 학회 날짜의 차이
- BERT-base — 논문의 "110M" 과 실제로 센 수의 차이
- Adam 논문의 β2 기본값과 트랜스포머 논문이 쓴 β2 의 차이
- GELU — 정확한 식(오차함수)과 tanh 근사의 차이

---

## 주장 목록

| 주장 | 출처 | 어떻게 확인했나 | 확인한 날 |
|---|---|---|---|
| GPT-2 small 은 논문 표 2 에서 117M(12층·d_model 768)으로 적혀 있다 | radford2019 표 2 (https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf) | PDF 를 받아 pypdf 로 글을 뽑아 표 2 "117M 12 768" 확인 | 2026-09-16 |
| GPT-2 의 117M·345M 은 OpenAI 스스로 틀렸다고 정정했고 지금 이름은 124M·355M 이다 (실제로 센 수는 7부 코드로 확인) | openai/gpt-2 README.md "Note that our original parameter counts were wrong due to an error (in our previous blog posts and paper)" · DEVELOPERS.md (download_model.py 124M/355M/774M/1558M) | raw.githubusercontent.com 에서 README·DEVELOPERS.md 를 받아 문장 확인. 124,439,808 은 코드로 셀 예정(7부) | 2026-09-16 |
| GPT-2 는 어휘 50,257 개, 문맥 1024 토큰이다 | radford2019 §2.3 "The vocabulary is expanded to 50,257. We also increase the context size from 512 to 1024 tokens" · openaipublic gpt-2/models/124M/hparams.json (n_vocab 50257, n_ctx 1024) | PDF 본문(pypdf) 인용 + hparams.json 4개(124M·355M·774M·1558M) curl 로 확인 | 2026-09-16 |
| BERT-base 는 논문에서 L=12, H=768, A=12, Total Parameters=110M, BERT-large 는 L=24, H=1024, A=16, 340M 이다 | devlin2018 (arXiv 1810.04805) §3 | papers/devlin2018.txt 36행 인용. 실제로 센 수(109,482,240)는 코드로 셀 예정(7부) — 차이를 다룬 1차 출처는 못 찾음 | 2026-09-16 |
| 'Attention Is All You Need' arXiv v1 은 2017-06-12 에 올라왔다 | arXiv 1706.03762 v1 | export.arxiv.org API published 값 = papers/vaswani2017.txt 첫 줄 | 2026-09-16 |
| 같은 논문의 학회 발표는 NIPS 2017(롱비치 컨벤션 센터, 2017년 12월 4~9일)이다 — arXiv 공개보다 약 6개월 뒤 | https://neurips.cc/Conferences/2017 ("Mon Dec 4th through Sat the 9th") · papers.nips.cc 초록 페이지(Advances in Neural Information Processing Systems 30) | WebFetch 2건 | 2026-09-16 |
| Adam 논문의 권장 기본값은 α=0.001, β1=0.9, β2=0.999, ε=10⁻⁸ 이다 | kingma2014 (arXiv 1412.6980v9) §2 알고리즘 1 설명문 "Good default settings for the tested machine learning problems are α = 0.001, β1 = 0.9, β2 = 0.999 and ε = 10−8" | ar5iv 본문이 비어(PDF 포함 문서) arxiv.org/pdf/1412.6980v9 를 pypdf 로 뽑아 2쪽 인용 | 2026-09-16 |
| 트랜스포머 논문은 Adam 을 β1=0.9, β2=0.98, ε=10⁻⁹ 로 썼다 — Adam 기본값과 β2·ε 가 다르다 | vaswani2017 §5.3 | papers/vaswani2017.txt 5.3절 인용 | 2026-09-16 |
| GELU 의 정확한 식은 x·Φ(x) = x·½[1+erf(x/√2)] 이다 | hendrycks2016 (arXiv 1606.08415) §2 | papers/hendrycks2016.txt 15행 인용 | 2026-09-16 |
| GELU 의 tanh 근사는 0.5x(1+tanh[√(2/π)(x+0.044715x³)]), 시그모이드 근사는 xσ(1.702x) 이다 | hendrycks2016 §2 | papers/hendrycks2016.txt 16~19행 인용. 상수는 0.044715 (0.044158 아님) | 2026-09-16 |
| GPT-2 공개 코드의 gelu 는 논문과 같은 상수 0.044715 를 쓴다 | https://github.com/openai/gpt-2/blob/c2dae27c1029770cea40978813f17a5fd545b883/src/model.py#L25-L26 `return 0.5*x*(1+tf.tanh(np.sqrt(2/np.pi)*(x+0.044715*tf.pow(x, 3))))` | raw.githubusercontent.com 의 master 와 커밋 c2dae27 두 판을 받아 25~26행 확인 | 2026-09-16 |
| 트랜스포머 base 는 N=6, d_model=512, h=8, d_k=d_v=64, d_ff=2048 이다 | vaswani2017 §3.1(N=6, d_model=512) · §3.2.2(h=8, d_k=d_v=64) · §3.3(d_ff=2048) · 표 3 | papers/vaswani2017.txt 해당 절 인용, data/hyper_vaswani.tsv 와 대조 | 2026-09-16 |
| 드롭아웃 P_drop=0.1(base), 라벨 스무딩 ε_ls=0.1 이다 | vaswani2017 §5.4 · 표 3 | papers/vaswani2017.txt 인용. paper_text.py --grep 은 이 두 문단의 절을 "-" 로 보고한다(글머리표 소제목 탓), 실제 위치는 5.4절 | 2026-09-16 |
| big 모델은 d_model=1024, d_ff=4096, h=16, P_drop=0.3 이고 EN-FR 에서는 P_drop=0.1 을 썼다 | vaswani2017 표 3 · §6.1 | papers/vaswani2017.txt 인용 | 2026-09-16 |
| 학습률 워밍업은 warmup_steps=4000 이고 lrate = d_model^-0.5 · min(step^-0.5, step·warmup^-1.5) 이다 | vaswani2017 §5.3 식 (3) | papers/vaswani2017.txt 인용 | 2026-09-16 |
| 한 대의 기계에 NVIDIA P100 GPU 8장, base 는 스텝당 약 0.4초로 100,000 스텝(12시간), big 은 스텝당 1.0초로 300,000 스텝(3.5일) | vaswani2017 §5.2 | papers/vaswani2017.txt 인용 | 2026-09-16 |
| newstest2014 BLEU: base 27.3(EN-DE)·38.1(EN-FR), big 28.4(EN-DE)·41.8(EN-FR) | vaswani2017 표 2 · 초록(41.8) | papers/vaswani2017.txt 인용. 주의: 같은 논문 §6.1 본문은 EN-FR big 을 "41.0" 으로 적어 표 2·초록과 어긋난다 — 덱은 표 2 값을 쓰고 차이를 밝힌다 | 2026-09-16 |
| EN-DE 는 약 450만 문장 쌍·공유 BPE 어휘 약 37000, EN-FR 은 3600만 문장·워드피스 어휘 32000 이다 | vaswani2017 §5.1 | papers/vaswani2017.txt 인용 | 2026-09-16 |
| GPT-3 의 여덟 모델은 모두 3000억(300 billion) 토큰으로 학습했고 문맥은 2048 토큰이다 | brown2020 표 2.1 설명문 · §2.1 | papers/brown2020.txt 54~55행 인용 | 2026-09-16 |
| GPT-3 표 2.1 은 13B 모델의 d_model 을 5140 으로 적는데 n_heads 40 × d_head 128 = 5120 과 맞지 않는다 | brown2020 표 2.1 | papers/brown2020.txt 인용, 인쇄된 값 그대로 data/models.tsv 에 옮김 | 2026-09-16 |
| Kaplan 외: L(N)=(N_c/N)^α_N, α_N≈0.076, N_c≈8.8×10¹³(임베딩 제외 파라미터); L(D) α_D≈0.095, D_c≈5.4×10¹³ 토큰; L(C_min) α≈0.050 | kaplan2020 §1.2 식 (1.1)~(1.3) | papers/kaplan2020.txt 37~43행 인용 | 2026-09-16 |
| Kaplan 외: 계산량이 늘면 주로 모델을 키워야 한다 — N ∝ C_min^0.73 | kaplan2020 §1.2 · 식 (6.1) | papers/kaplan2020.txt 58·216행 인용 | 2026-09-16 |
| Kaplan 외: 학습 계산량은 C ≈ 6NBS (임베딩 제외, 6 은 순전파+역전파) | kaplan2020 §1.3 · §3 | papers/kaplan2020.txt 67·137행 인용 | 2026-09-16 |
| Chinchilla: 계산 예산이 늘 때 모델 크기와 학습 토큰 수를 "대략 같은 비율로" 늘려야 한다 (a≈0.50/0.49/0.46, Kaplan 은 0.73) | hoffmann2022 §3.4 표 2 | papers/hoffmann2022.txt 62~67행 인용 | 2026-09-16 |
| Chinchilla 는 70B 파라미터를 1.4조(1.4T) 토큰으로 학습했고, 같은 계산량의 Gopher 는 280B·300B 토큰이다 | hoffmann2022 §1 표 1 · §4.1 | papers/hoffmann2022.txt 15~21·73행 인용 | 2026-09-16 |
| 논문은 "파라미터당 20 토큰" 이라는 문구를 쓰지 않는다. 표 3(접근 1)은 1B→20.2B 토큰, 10B→205.1B 토큰, 67B→1.5T 토큰을 적는다 | hoffmann2022 §3.4 표 3 | papers/hoffmann2022.txt 에서 "per parameter" 검색 0건, 표 3 행 인용. 덱에는 "약 20배" 대신 표의 수를 적는다 | 2026-09-16 |
| Chinchilla 손실 적합: L(N,D)=E+A/N^0.34+B/D^0.28, E=1.69, A=406.4, B=410.7 | hoffmann2022 부록 D.2 식 (10) | papers/hoffmann2022.txt 279~280행 인용 | 2026-09-16 |
| LLaMA 6.7B·13.0B 은 1.0T 토큰, 32.5B·65.2B 는 1.4T 토큰으로 학습했다 | touvron2023 §2.2 표 2 · 그림 1 설명문 | papers/touvron2023.txt 40~43행 인용 | 2026-09-16 |
| BPE 는 Gage(1994)의 압축 알고리즘을 Sennrich 외가 단어 분할에 가져온 것이다 | sennrich2015 (arXiv 1508.07909) §3.2 | papers/sennrich2015.txt 3.2절 인용 | 2026-09-16 |
| GPT-1 은 12층 디코더 전용, 768차원·12헤드, FFN 3072, 512 토큰 문맥, BPE 40,000 병합, GELU 를 썼다 | radford2018 §4.1 Model specifications (https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf) | PDF 를 pypdf 로 뽑아 인용. 논문에 파라미터 수는 없다 | 2026-09-16 |
| GPT-2 는 레이어 정규화를 각 하위 블록의 **입력** 쪽으로 옮기고(사전 활성 잔차망처럼), 마지막 셀프 어텐션 블록 뒤에 레이어 정규화를 하나 더 두었다 | radford2019 §2.3 "Layer normalization (Ba et al., 2016) was moved to the input of each sub-block, similar to a pre-activation residual network (He et al., 2016) and an additional layer normalization was added after the final self-attention block." | cdn.openai.com PDF 를 받아 pypdf 로 글을 뽑아 문장을 대조 | 2026-09-16 |
| GPT-2 는 잔차 층의 가중치를 초기화 때 1/√N 배(N 은 잔차 층의 수)로 줄였다 | radford2019 §2.3 "We scale the weights of residual layers at initialization by a factor of 1/√N where N is the number of residual layers." | 같은 PDF 대조. 이 덱의 SPEC §3.5 는 0.02/√(2L) — 블록마다 잔차 층이 둘이라 N = 2L | 2026-09-16 |
| 트랜스포머 논문은 두 임베딩 층과 소프트맥스 앞 선형 변환이 같은 가중치 행렬을 나눠 쓴다(Press·Wolf 와 비슷하게) | vaswani2017 §3.4 "In our model, we share the same weight matrix between the two embedding layers and the pre-softmax linear transformation, similar to [30]." | papers/vaswani2017.txt 3.4절 인용 | 2026-09-16 |
| 입력 임베딩과 출력 임베딩을 묶자고 제안한 논문 | press2016 초록·§3 Weight Tying | papers/press2016.txt 인용 | 2026-09-16 |
| 학습된 위치 임베딩과 사인 인코딩은 거의 같은 결과를 냈고(표 3 (E)), 사인을 고른 까닭은 학습 때보다 긴 길이로 외삽할 수 있으리라는 가설이었다 | vaswani2017 §3.5 · 표 3 행 (E) | papers/vaswani2017.txt 3.5절·표 3 인용 | 2026-09-16 |
| post-LN 트랜스포머는 학습률 워밍업이 필수에 가깝고, pre-LN 은 초기화에서 기울기가 잘 행동해 워밍업을 뺄 수 있음을 보였다 | xiong2020 §1 기여 목록 · §3.3 | papers/xiong2020.txt 1절 인용 | 2026-09-16 |
| Kaplan 외는 학습 계산량을 C ≈ 6NBS(임베딩 제외 N)로 어림하고, d_model > n_ctx/12 이면 문맥에 달린 비용이 작다고 적는다 | kaplan2020 §2.1 · §1.3 | papers/kaplan2020.txt 인용 | 2026-09-16 |
| 잔차 학습 F(x) + x 는 한 층 이상을 건너뛰는 "shortcut connection" 으로 구현된다 | he2015 §1 | papers/he2015.txt 인용 | 2026-09-16 |
| √d_k 로 나누는 까닭 — d_k 가 크면 내적의 크기가 커져 소프트맥스가 기울기가 아주 작은 영역으로 밀린다고 추측했고, 각주에서 성분이 독립·평균 0·분산 1 이면 q·k 의 분산이 d_k 라고 설명한다 | vaswani2017 §3.2.1 과 각주 1 | papers/vaswani2017.txt 3.2.1절 인용 | 2026-09-16 |
| 스케일링이 없는 내적 어텐션은 d_k 가 크면 덧셈 어텐션보다 못하다 | vaswani2017 §3.2.1 "additive attention outperforms dot product attention without scaling for larger values of d_k" | papers/vaswani2017.txt 인용 | 2026-09-16 |
| 멀티헤드 어텐션은 서로 다른 표현 부분공간의 정보를 서로 다른 위치에서 함께 볼 수 있게 하고, 헤드마다 차원이 줄어 전체 계산량은 전체 차원의 헤드 하나와 비슷하다 | vaswani2017 §3.2.2 | papers/vaswani2017.txt 인용 | 2026-09-16 |
| 트랜스포머 이전의 어텐션(Bahdanau 외)은 정렬 모델을 순전파 신경망으로 두고 RNN 번역기와 함께 학습했다 | bahdanau2014 §3.1 | papers/bahdanau2014.txt 인용 | 2026-09-16 |
| FlashAttention 은 N×N 어텐션 행렬을 느린 메모리에 만들지 않으려고 이미 알려진 두 기법 — 타일링(블록마다 소프트맥스를 크기 조정으로 분해)과 재계산(역전파 때 다시 계산) — 을 쓴다 | dao2022 §3.1 "We apply two established techniques (tiling, recomputation) …" | papers/dao2022.txt 3.1절 인용 | 2026-09-16 |
