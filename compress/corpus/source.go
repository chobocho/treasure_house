// ber — LDAP 이 쓰는 만큼의 BER 부호화.
//
// LDAP 은 글자가 아니라 바이트로 말한다. 그 바이트를 짜는 규칙이 BER
// 이고, 규칙의 뼈대는 딱 세 가지다.
//
//	[태그 1바이트][길이][내용]      = TLV (Tag-Length-Value)
//
// 내용 안에 또 TLV 가 들어가면 그게 묶음(SEQUENCE)이다. 그것뿐이다. 이
// 파일은 300줄이 안 되고, 그 안에 LDAP 이 쓰는 모든 부호화가 들어 있다.
// "프로토콜은 손바닥에 올려놓을 수 있을 만큼 작다" 는 이 덱의 주장이
// 처음으로 증명되는 자리다.
//
// 우리가 일부러 안 하는 것: 부정 길이(indefinite length) 형식. BER 에는
// "끝 표시가 나올 때까지" 라는 형식이 있지만 RFC 4511 §5.1 이 LDAP
// 에서는 definite form 만 쓰라고 못 박았다. 받으면 오류로 처리한다 —
// 받아 주면 그 순간 프로토콜이 아니라 추측이 된다.
package ber

import (
	"errors"
	"fmt"
)

// 태그의 위쪽 세 비트가 종류를, 여섯째 비트가 "안에 또 TLV 가 있는가"
// 를, 아래 다섯 비트가 번호를 담는다.
//
//	8 7 | 6 | 5 4 3 2 1
//	class| C |  번호
type Class byte

const (
	Universal   Class = 0x00 // 모두가 아는 것 (INTEGER, SEQUENCE …)
	Application Class = 0x40 // LDAP 이 정한 것 (BindRequest …)
	Context     Class = 0x80 // 그 자리에서만 뜻이 있는 것 (필터·인증)
	Private     Class = 0xC0 // 이 덱에서는 쓰지 않는다
)

const constructedBit byte = 0x20

// 자주 쓰는 보편 태그. 숫자를 외울 필요는 없지만, 캡처에서 이 바이트를
// 보면 무엇인지 알아볼 수 있어야 한다.
const (
	TagBoolean     = 0x01
	TagInteger     = 0x02
	TagOctetString = 0x04
	TagNull        = 0x05
	TagEnumerated  = 0x0A
	TagSequence    = 0x30 // 0x10 | constructed
	TagSet         = 0x31 // 0x11 | constructed
)

// ErrShort 는 "아직 덜 왔다" 는 뜻이다. 오류가 아니라 상태에 가깝다 —
// 서버의 읽기 고리가 이것을 보고 더 읽는다.
var ErrShort = errors.New("바이트가 아직 모자란다")

// Tag 는 태그 한 바이트를 만든다.
//
// 번호가 30 을 넘으면 여러 바이트로 적는 규칙이 따로 있는데, LDAP 은
// 25(IntermediateResponse)까지라 만들지 않는다. 조용히 틀린 바이트를
// 내느니 죽는 편이 낫다 — 그 바이트는 상대가 해석할 수 없다.
func Tag(c Class, constructed bool, n int) byte {
	if n < 0 || n > 30 {
		panic(fmt.Sprintf("태그 번호 %d — 0~30 만 만든다", n))
	}
	t := byte(c) | byte(n)
	if constructed {
		t |= constructedBit
	}
	return t
}

// EncodeLength 는 길이를 적는다.
//
// 127 까지는 한 바이트에 그대로. 그보다 크면 첫 바이트의 맨 위 비트를
// 켜고 아래 일곱 비트에 "길이를 적는 데 쓴 바이트 수" 를 담은 뒤,
// 그만큼의 빅엔디언 숫자를 잇는다. 그래서 128 은 81 80 이 된다 — 0x80
// 하나가 아니다. (0x80 하나는 부정 길이라는 다른 뜻이라서 쓸 수 없다.)
func EncodeLength(n int) []byte {
	if n < 0 {
		panic("길이가 음수다")
	}
	if n < 128 {
		return []byte{byte(n)}
	}
	var num []byte
	for v := n; v > 0; v >>= 8 {
		num = append([]byte{byte(v)}, num...)
	}
	return append([]byte{0x80 | byte(len(num))}, num...)
}

// Encode 는 TLV 한 덩어리를 만든다. 이 파일에서 바이트를 내는 함수는
// 결국 전부 여기로 모인다.
func Encode(tag byte, content []byte) []byte {
	out := make([]byte, 0, 2+len(content))
	out = append(out, tag)
	out = append(out, EncodeLength(len(content))...)
	return append(out, content...)
}

// intBytes 는 정수를 2의 보수 · 빅엔디언 · **가장 짧게** 적는다.
//
// "가장 짧게" 가 규칙인 것이 중요하다. 128 을 0x80 한 바이트로 적으면
// 맨 위 비트가 켜져 있어 -128 로 읽힌다. 그래서 앞에 0x00 을 하나 더
// 붙여 00 80 두 바이트가 된다. 반대로 -1 은 FF 한 바이트면 충분하다.
// 시간·공간 모두 O(바이트 수) — 최대 8.
func intBytes(n int64) []byte {
	// 맨 앞 바이트가 남는지 보고 하나씩 깎는다.
	length := 8
	for length > 1 {
		top := byte(n >> uint(8*(length-1)))
		next := byte(n >> uint(8*(length-2)))
		// 앞 바이트가 0x00 이고 다음 바이트의 부호 비트가 0 이면
		// 남는다. 앞 바이트가 0xFF 이고 다음 바이트의 부호 비트가 1
		// 이어도 남는다.
		if (top == 0x00 && next&0x80 == 0) ||
			(top == 0xFF && next&0x80 != 0) {
			length--
			continue
		}
		break
	}
	out := make([]byte, length)
	for i := 0; i < length; i++ {
		out[i] = byte(n >> uint(8*(length-1-i)))
	}
	return out
}

// Int 는 보편 INTEGER 다. messageID, LDAP 판번호, 검색 크기 제한 따위.
func Int(n int64) []byte { return Encode(TagInteger, intBytes(n)) }

// Enum 은 ENUMERATED 다. 겉모습은 정수와 같고 태그만 다르다.
// LDAP 의 resultCode(성공 0, invalidCredentials 49 …)가 이것이다.
func Enum(n int64) []byte { return Encode(TagEnumerated, intBytes(n)) }

// Str 은 OCTET STRING 이다. 이름이 "문자열" 이지만 실제로는 바이트
// 묶음이다. LDAP 의 글자는 UTF-8 로 실려 간다(RFC 4511 §4.1.2
// LDAPString).
func Str(s string) []byte { return Encode(TagOctetString, []byte(s)) }

// Bytes 는 글자가 아닌 바이트를 OCTET STRING 으로 싣는다. objectGUID 는
// 16바이트 이진값이고 안에 0x00 이 들어 있다 — 그걸 글자로 다루면
// 거기서 잘린다. 7부에서 이 구분이 사고의 원인으로 돌아온다.
func Bytes(b []byte) []byte { return Encode(TagOctetString, b) }

// Bool 은 BOOLEAN 이다. BER 은 0 이 아닌 값을 참으로 보지만,
// 내보낼 때는 관례대로 0xFF 를 쓴다.
func Bool(v bool) []byte {
	if v {
		return Encode(TagBoolean, []byte{0xFF})
	}
	return Encode(TagBoolean, []byte{0x00})
}

func concat(parts [][]byte) []byte {
	n := 0
	for _, p := range parts {
		n += len(p)
	}
	out := make([]byte, 0, n)
	for _, p := range parts {
		out = append(out, p...)
	}
	return out
}

// Seq 는 여러 TLV 를 한 묶음으로 싼다. LDAP 메시지의 뼈대다.
func Seq(parts ...[]byte) []byte {
	return Encode(TagSequence, concat(parts))
}

// Set 은 순서가 뜻이 없는 묶음이다. 속성의 값들이 이것으로 온다.
func Set(parts ...[]byte) []byte {
	return Encode(TagSet, concat(parts))
}

// ── 읽기 ────────────────────────────────────────────────────────────

// TLV 는 떼어 낸 한 덩어리다. Value 는 머리(태그·길이)를 뺀 내용뿐이다.
type TLV struct {
	Tag   byte
	Value []byte
}

func (t TLV) Class() Class      { return Class(t.Tag & 0xC0) }
func (t TLV) Constructed() bool { return t.Tag&constructedBit != 0 }
func (t TLV) Num() int          { return int(t.Tag & 0x1F) }

// Str 은 내용을 글자로 읽는다. 바이트가 필요하면 Value 를 그대로 쓸 것.
func (t TLV) Str() string { return string(t.Value) }

// Int 는 2의 보수로 읽는다. 첫 바이트의 맨 위 비트가 부호다.
func (t TLV) Int() (int64, error) {
	if len(t.Value) == 0 {
		return 0, errors.New("정수의 내용이 비어 있다")
	}
	if len(t.Value) > 8 {
		return 0, fmt.Errorf("정수가 %d바이트 — int64 에 안 들어간다",
			len(t.Value))
	}
	var n int64
	if t.Value[0]&0x80 != 0 {
		n = -1 // 음수는 위쪽 비트를 1 로 채우고 시작한다
	}
	for _, b := range t.Value {
		n = n<<8 | int64(b)
	}
	return n, nil
}

func (t TLV) Bool() (bool, error) {
	if len(t.Value) != 1 {
		return false, fmt.Errorf("BOOLEAN 이 %d바이트다", len(t.Value))
	}
	return t.Value[0] != 0, nil
}

// parseLength 는 길이와 "길이를 적는 데 쓴 바이트 수" 를 돌려준다.
func parseLength(b []byte) (length, used int, err error) {
	if len(b) == 0 {
		return 0, 0, ErrShort
	}
	first := b[0]
	if first < 0x80 {
		return int(first), 1, nil
	}
	if first == 0x80 {
		// RFC 4511 §5.1 — LDAP 은 definite form 만 쓴다
		return 0, 0, errors.New("부정 길이 형식은 LDAP 에서 못 쓴다")
	}
	n := int(first & 0x7F)
	if n > 4 {
		return 0, 0, fmt.Errorf("길이를 %d바이트로 적었다", n)
	}
	if len(b) < 1+n {
		return 0, 0, ErrShort
	}
	v := 0
	for _, c := range b[1 : 1+n] {
		v = v<<8 | int(c)
	}
	return v, 1 + n, nil
}

// Next 는 앞에서 TLV 하나를 떼어 내고 나머지를 돌려준다.
func Next(b []byte) (TLV, []byte, error) {
	if len(b) == 0 {
		return TLV{}, nil, ErrShort
	}
	if b[0]&0x1F == 0x1F {
		return TLV{}, nil, errors.New(
			"여러 바이트 태그 — 이 해석기는 번호 0~30 만 안다")
	}
	length, used, err := parseLength(b[1:])
	if err != nil {
		return TLV{}, nil, err
	}
	head := 1 + used
	if len(b) < head+length {
		return TLV{}, nil, ErrShort
	}
	v := b[head : head+length]
	return TLV{Tag: b[0], Value: v}, b[head+length:], nil
}

// Children 은 묶음의 내용을 TLV 여럿으로 푼다.
// 꼭 맞아떨어져야 한다 — 남는 바이트가 있으면 어딘가 잘못 읽은 것이다.
func Children(v []byte) ([]TLV, error) {
	var out []TLV
	rest := v
	for len(rest) > 0 {
		tlv, r, err := Next(rest)
		if err != nil {
			return nil, err
		}
		out = append(out, tlv)
		rest = r
	}
	return out, nil
}

// MessageLength 는 "이 메시지 한 통이 모두 몇 바이트인가" 를 앞부분만
// 보고 알려 준다.
//
// TCP 는 메시지 단위를 모른다. 한 통이 세 번에 나눠 올 수도, 두 통이 한
// 번에 붙어 올 수도 있다. 서버의 읽기 고리는 "지금 가진 바이트로 한
// 통이 완성되나, 아니면 얼마나 더 읽어야 하나" 를 알아야 하고, 그 답이
// 이 함수다. 아직 판단할 수 없으면 ErrShort 를 돌려준다.
func MessageLength(b []byte) (int, error) {
	if len(b) < 2 {
		return 0, ErrShort
	}
	length, used, err := parseLength(b[1:])
	if err != nil {
		return 0, err
	}
	return 1 + used + length, nil
}
