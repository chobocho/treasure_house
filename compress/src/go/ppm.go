package compresslib

// PPM — 부분 일치 예측 — SPEC §17.
//
// 앞 두 바이트로 다음 바이트를 찍는다. 틀리면 "틀렸다"(탈출) 고 말하고
// 앞 한 바이트로, 또 틀리면 맨손으로 찍는다. 탈출값은 방법 C 다
// — 문맥에서 본 서로 다른 기호의 수가 곧 탈출의 빈도다.
//
// **모든 기호가 배제된 문맥은 건너뛴다.** 탈출이 확실해 비트가 0이다.
// 이걸 잊으면 부호기만 탈출을 적어 거기서 어긋난다 — PPM 의 고전 버그.

import "sort"

const (
	ppmMaxOrder = 2
	ppmAlphabet = 256
	// 문맥의 합계가 이 값에 닿으면 모든 셈을 반으로 줄인다.
	ppmMaxTotal = 8192
)

// 문맥 열쇠 — 바이트 0~2개. 길이를 같이 담아 ()·(a)·(a,b) 를 구별한다.
type ppmKey struct {
	order int
	a, b  byte
}

type ppmTable map[int]uint32
type ppmModel map[ppmKey]ppmTable

func ppmContextKeys(history []byte) []ppmKey {
	var keys []ppmKey
	for order := ppmMaxOrder; order >= 0; order-- {
		if order > len(history) {
			continue
		}
		k := ppmKey{order: order}
		switch order {
		case 1:
			k.a = history[len(history)-1]
		case 2:
			k.a = history[len(history)-2]
			k.b = history[len(history)-1]
		}
		keys = append(keys, k)
	}
	return keys
}

func ppmUpdate(model ppmModel, key ppmKey, sym int) {
	table := model[key]
	if table == nil {
		table = ppmTable{}
		model[key] = table
	}
	table[sym]++
	var total uint32
	for _, v := range table {
		total += v
	}
	if total >= ppmMaxTotal {
		for s, v := range table {
			if v>>1 < 1 {
				table[s] = 1
			} else {
				table[s] = v >> 1
			}
		}
	}
}

// 배제되지 않은 기호를 번호 오름차순으로. 누적합의 순서가 곧 이것이다.
func ppmVisible(table ppmTable, excluded []bool) []int {
	var syms []int
	for s := range table {
		if !excluded[s] {
			syms = append(syms, s)
		}
	}
	sort.Ints(syms)
	return syms
}

func ppmPushHistory(history []byte, b byte) []byte {
	history = append(history, b)
	if len(history) > ppmMaxOrder {
		history = history[1:]
	}
	return history
}

func PpmEncode(src []byte) (out []byte, err error) {
	defer guard(&err)
	if len(src) == 0 {
		return putVarint(nil, 0), nil
	}
	enc := newRcEncoder()
	model := ppmModel{}
	var history []byte
	for _, b := range src {
		excluded := make([]bool, ppmAlphabet)
		coded := false
		for _, key := range ppmContextKeys(history) {
			table, ok := model[key]
			if !ok {
				continue
			}
			syms := ppmVisible(table, excluded)
			if len(syms) == 0 {
				continue // 모두 배제 — 아무것도 안 적는다
			}
			esc := uint32(len(syms))
			tot := esc
			for _, s := range syms {
				tot += table[s]
			}
			if _, has := table[int(b)]; has && !excluded[b] {
				var cum uint32
				for _, s := range syms {
					if s == int(b) {
						break
					}
					cum += table[s]
				}
				enc.encodeFreq(cum, table[int(b)], tot)
				coded = true
				break
			}
			enc.encodeFreq(tot-esc, esc, tot)
			for _, s := range syms {
				excluded[s] = true
			}
		}
		if !coded {
			// -1차 — 남은 기호에 균등하게 (§17.4)
			var rest, index uint32
			for s := 0; s < ppmAlphabet; s++ {
				if excluded[s] {
					continue
				}
				if s < int(b) {
					index++
				}
				rest++
			}
			enc.encodeFreq(index, 1, rest)
		}
		for _, key := range ppmContextKeys(history) {
			ppmUpdate(model, key, int(b))
		}
		history = ppmPushHistory(history, b)
	}
	enc.flush()
	return append(putVarint(nil, uint64(len(src))), enc.out...), nil
}

func PpmDecode(src []byte) (out []byte, err error) {
	defer guard(&err)
	n, pos := getLength(src, 0)
	if n == 0 {
		if pos != len(src) {
			fail("빈 입력인데 뒤에 바이트가 있다")
		}
		return []byte{}, nil
	}
	dec := newRcDecoder(src, pos)
	model := ppmModel{}
	var history []byte
	result := make([]byte, 0, n)
	for k := 0; k < n; k++ {
		excluded := make([]bool, ppmAlphabet)
		found := -1
		for _, key := range ppmContextKeys(history) {
			table, ok := model[key]
			if !ok {
				continue
			}
			syms := ppmVisible(table, excluded)
			if len(syms) == 0 {
				continue
			}
			esc := uint32(len(syms))
			tot := esc
			for _, s := range syms {
				tot += table[s]
			}
			v := dec.decodeFreq(tot)
			var cum uint32
			hit := -1
			for _, s := range syms {
				if v >= cum && v < cum+table[s] {
					hit = s
					break
				}
				cum += table[s]
			}
			if hit >= 0 {
				dec.decodeUpdate(cum, table[hit], tot)
				found = hit
				break
			}
			dec.decodeUpdate(tot-esc, esc, tot)
			for _, s := range syms {
				excluded[s] = true
			}
		}
		if found < 0 {
			var rest []int
			for s := 0; s < ppmAlphabet; s++ {
				if !excluded[s] {
					rest = append(rest, s)
				}
			}
			v := dec.decodeFreq(uint32(len(rest)))
			found = rest[v]
			dec.decodeUpdate(v, 1, uint32(len(rest)))
		}
		result = append(result, byte(found))
		for _, key := range ppmContextKeys(history) {
			ppmUpdate(model, key, found)
		}
		history = ppmPushHistory(history, byte(found))
	}
	return result, nil
}
