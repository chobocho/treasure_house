package compresslib

// 문맥 혼합 — SPEC §18.
//
// 여기까지의 코덱은 모델을 **하나** 골랐다. 문맥 혼합은 고르지 않는다
// — 여러 모델에게 묻고 **의견을 섞으며** 누구를 믿을지 배운다.
//
// 섞는 자리가 요점이다. 확률을 그냥 평균 내면 0.01 과 0.99 가 0.5 가
// 되어 두 모델의 확신이 사라진다. **로지스틱 영역** 에서 더해야 한다.

const (
	cmTableBits = 20
	cmTableSize = 1 << cmTableBits
	cmNumModels = 5
	cmProbOne   = 4096
	cmProbHalf  = cmProbOne / 2
	// 믹서 갱신의 시프트. lpaq 과 같은 16이다. 10 으로 두면 가중치가
	// 한 걸음에 5만씩 튀어 모델이 수렴하지 못한다.
	cmMixerShift       = 16
	cmMixerInit        = 1 << 14
	cmMixerUpdateShift = 16
	cmMixerLearn       = 16
	cmMixerClamp       = 1 << 20
	cmApmRate          = 7
	cmApm1Contexts     = 256
	cmApm2Contexts     = 1 << 16
	cmHashA            = 0x9E3779B1
	cmHashB            = 0x85EBCA6B
	cmCounterLimit     = 15
)

// 셈이 쌓일수록 천천히 움직인다. 처음 보는 문맥은 빨리 배우고 오래 본
// 문맥은 흔들리지 않아야 한다 — 고정 비율 하나로는 둘 다 못 한다.
var cmCounterRates = [16]uint{1, 1, 2, 2, 3, 3, 4, 4,
	4, 5, 5, 5, 5, 5, 5, 5}

// SQUASH-TABLE-BEGIN — gen_tables.py 가 다섯을 대조한다 (§18.6)
var cmSquashTable = [33]int{
	1, 2, 3, 6, 10, 16, 27, 45, 73, 120, 194, 310, 488, 747, 1101,
	1546, 2047, 2549, 2994, 3348, 3607, 3785, 3901, 3975, 4024,
	4050, 4068, 4079, 4085, 4089, 4092, 4093, 4094}

// SQUASH-TABLE-END

// 로지스틱: -2047..2047 → 0..4095. 표 사이를 직선으로 잇는다.
func cmSquash(d int) int {
	if d > 2047 {
		return 4095
	}
	if d < -2047 {
		return 0
	}
	w := d & 127
	i := (d >> 7) + 16
	return (cmSquashTable[i]*(128-w) + cmSquashTable[i+1]*w + 64) >> 7
}

// squash 의 역. 표를 뒤집어 만든다 — 따로 적을 값이 아니다.
var cmStretchTable = func() [cmProbOne]int16 {
	var table [cmProbOne]int16
	pi := 0
	for x := -2047; x <= 2047; x++ {
		v := cmSquash(x)
		for p := pi; p <= v; p++ {
			table[p] = int16(x)
		}
		pi = v + 1
	}
	for p := pi; p < cmProbOne; p++ {
		table[p] = 2047
	}
	return table
}()

func cmStretch(p int) int { return int(cmStretchTable[p]) }

func cmHash(ctx, c0 uint32) int {
	h := (ctx * cmHashA) ^ (c0 * cmHashB)
	return int(h >> (32 - cmTableBits))
}

// 적응 확률 지도 — 믹서의 답을 문맥에 맞춰 한 번 더 고친다 (§18.5).
type cmApm struct {
	t     []int32
	index int
}

func newCmApm(contexts int) *cmApm {
	t := make([]int32, contexts*33)
	for i := range t {
		t[i] = int32(cmSquash((i%33-16)*128) * 16)
	}
	return &cmApm{t: t}
}

func (a *cmApm) pp(pr, cx int) int {
	// 곱수는 32 다. 표가 33칸이라 0..4095 를 0..32 로 펴야 끝까지
	// 쓴다. lpaq1 의 23 이면 위쪽 아홉 칸이 죽어 확률이 잘린다.
	s := (cmStretch(pr) + 2048) * 32
	wt := s & 0xFFF
	j := cx*33 + s>>12
	a.index = j + wt>>11
	return int((a.t[j]*int32(4096-wt) + a.t[j+1]*int32(wt)) >> 16)
}

func (a *cmApm) update(bit int) {
	g := int32(bit<<16 + bit<<cmApmRate - bit - bit)
	a.t[a.index] += (g - a.t[a.index]) >> cmApmRate
}

// 문맥 모델 다섯 + 믹서 + APM 둘. 부호기와 복호기가 똑같이 쓴다.
type cmModel struct {
	order0  []uint16
	order0n []byte
	tables  [4][]uint16
	counts  [4][]byte
	weights []int32
	apm1    *cmApm
	apm2    *cmApm
	history uint32
	c0      uint32
	slots   [cmNumModels]int
	st      [cmNumModels]int
	pMix    int
}

func newCmModel() *cmModel {
	m := &cmModel{
		order0:  make([]uint16, 256),
		order0n: make([]byte, 256),
		weights: make([]int32, 256*cmNumModels),
		apm1:    newCmApm(cmApm1Contexts),
		apm2:    newCmApm(cmApm2Contexts),
		c0:      1,
		pMix:    cmProbHalf,
	}
	for i := range m.order0 {
		m.order0[i] = cmProbHalf
	}
	for k := 0; k < 4; k++ {
		m.tables[k] = make([]uint16, cmTableSize)
		for i := range m.tables[k] {
			m.tables[k][i] = cmProbHalf
		}
		m.counts[k] = make([]byte, cmTableSize)
	}
	for i := range m.weights {
		m.weights[i] = cmMixerInit
	}
	return m
}

func (m *cmModel) predict() int {
	c0 := m.c0
	h := m.history
	m.slots[0] = int(c0 & 0xFF)
	for k := 0; k < 4; k++ {
		var mask uint32 = 0xFFFFFFFF
		if k < 3 {
			mask = 1<<uint(8*(k+1)) - 1
		}
		ctx := h & mask
		m.slots[k+1] = cmHash(ctx+uint32(k+1)*0x01000193, c0)
	}
	var probs [cmNumModels]int
	probs[0] = int(m.order0[m.slots[0]])
	for k := 0; k < 4; k++ {
		probs[k+1] = int(m.tables[k][m.slots[k+1]])
	}
	wbase := int(c0&0xFF) * cmNumModels
	var dot int64
	for i := 0; i < cmNumModels; i++ {
		m.st[i] = cmStretch(probs[i])
		dot += int64(m.weights[wbase+i]) * int64(m.st[i])
	}
	dot >>= cmMixerShift
	if dot > 2047 {
		dot = 2047
	}
	if dot < -2047 {
		dot = -2047
	}
	m.pMix = cmSquash(int(dot))
	p := (m.pMix + 3*m.apm1.pp(m.pMix, int(c0&0xFF))) >> 2
	cx2 := int((c0&0xFF)<<8 | h&0xFF)
	p = (p + 3*m.apm2.pp(p, cx2)) >> 2
	if p < 1 {
		p = 1
	}
	if p > 4094 {
		p = 4094
	}
	return p
}

func (m *cmModel) update(bit int) {
	target := bit << 12
	i0 := m.slots[0]
	m.order0[i0] = uint16(int(m.order0[i0]) +
		(target-int(m.order0[i0]))>>cmCounterRates[m.order0n[i0]])
	if int(m.order0n[i0]) < cmCounterLimit {
		m.order0n[i0]++
	}
	for k := 0; k < 4; k++ {
		i := m.slots[k+1]
		t := m.tables[k]
		c := m.counts[k]
		rate := cmCounterRates[c[i]]
		t[i] = uint16(int(t[i]) + (target-int(t[i]))>>rate)
		if int(c[i]) < cmCounterLimit {
			c[i]++
		}
	}
	err := (target - m.pMix) * cmMixerLearn
	wbase := int(m.c0&0xFF) * cmNumModels
	for i := 0; i < cmNumModels; i++ {
		v := int64(m.weights[wbase+i]) +
			int64(m.st[i]*err)>>cmMixerUpdateShift
		if v > cmMixerClamp {
			v = cmMixerClamp
		}
		if v < -cmMixerClamp {
			v = -cmMixerClamp
		}
		m.weights[wbase+i] = int32(v)
	}
	m.apm1.update(bit)
	m.apm2.update(bit)
	m.c0 = m.c0<<1 | uint32(bit)
	if m.c0 >= 256 {
		m.history = m.history<<8 | m.c0&0xFF
		m.c0 = 1
	}
}

func CmEncode(src []byte) (out []byte, err error) {
	defer guard(&err)
	if len(src) == 0 {
		return putVarint(nil, 0), nil
	}
	enc := newRcEncoder()
	model := newCmModel()
	for _, b := range src {
		for i := 7; i >= 0; i-- {
			bit := int(b>>uint(i)) & 1
			p := model.predict()
			// 코더는 P(0) 을 받는다. 모델은 P(1) 을 내므로 뒤집는다.
			enc.encodeBitP0(uint32(cmProbOne-p), bit)
			model.update(bit)
		}
	}
	enc.flush()
	return append(putVarint(nil, uint64(len(src))), enc.out...), nil
}

func CmDecode(src []byte) (out []byte, err error) {
	defer guard(&err)
	n, pos := getLength(src, 0)
	if n == 0 {
		if pos != len(src) {
			fail("빈 입력인데 뒤에 바이트가 있다")
		}
		return []byte{}, nil
	}
	dec := newRcDecoder(src, pos)
	model := newCmModel()
	result := make([]byte, 0, n)
	for k := 0; k < n; k++ {
		byteVal := 0
		for i := 0; i < 8; i++ {
			p := model.predict()
			bit := dec.decodeBitP0(uint32(cmProbOne - p))
			model.update(bit)
			byteVal = byteVal<<1 | bit
		}
		result = append(result, byte(byteVal))
	}
	return result, nil
}
