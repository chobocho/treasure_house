package mygit

// 팩 (SPEC.md §13) — 객체 여럿을 한 파일에, 비슷한 것은 델타로.
//
// 느슨한 객체는 파일 하나에 객체 하나지만, 팩은 객체들을 이어 붙이고
// 비슷한 객체는 "바탕에서 여기를 복사, 여기에 이것을 끼움" 이라는
// 델타로 적는다. 색인(.idx)은 이름 → 팩 안 자리의 표다. 팩 끝
// 20바이트는 팩 전체의 SHA-1 이고, 그것이 곧 파일 이름이다.

import (
	"bytes"
	"encoding/binary"
	"encoding/hex"
	"fmt"
	"hash/crc32"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

var typeNames = map[int]string{1: "commit", 2: "tree", 3: "blob",
	4: "tag"}
var typeCodes = map[string]int{"commit": 1, "tree": 2, "blob": 3,
	"tag": 4}

const (
	ofsDelta = 6
	refDelta = 7
)

// PackEntry 는 팩 항목 하나를 되살린 것. PackedType 은 팩에 적힌
// 형식(6·7 은 델타), Type·Body 는 되살린 객체, Depth·Base 는 델타
// 사슬. BaseOffset 은 OFS_DELTA 의 바탕 자리(없으면 -1).
type PackEntry struct {
	Offset, End, BaseOffset, PackedType, Depth int
	Crc                                        uint32
	Delta, Body                                []byte
	Base, Type, Oid                            string
}

// External 은 팩 밖의 REF_DELTA 바탕을 (형식, 몸) 으로 준다.
type External func(oid string) (string, []byte, error)

// varintLE 는 7비트씩 작은 쪽부터(델타 머리의 크기).
func varintLE(data []byte, pos int) (int, int) {
	val, shift := 0, 0
	for {
		b := data[pos]
		pos++
		val |= int(b&0x7f) << shift
		shift += 7
		if b&0x80 == 0 {
			return val, pos
		}
	}
}

// entryHeader 는 항목 머리 → (형식, 크기, 다음 자리). 첫 바이트의 낮은
// 4비트가 크기의 시작이고, 이어지는 바이트는 7비트씩 위로 붙는다.
func entryHeader(data []byte, pos int) (int, int, int) {
	b := data[pos]
	pos++
	typ, size, shift := int(b>>4)&7, int(b&15), 4
	for b&0x80 != 0 {
		b = data[pos]
		pos++
		size |= int(b&0x7f) << shift
		shift += 7
	}
	return typ, size, pos
}

// ofsDist 는 OFS_DELTA 의 거리 — 큰 쪽부터, 이어지는 바이트마다 +1.
func ofsDist(data []byte, pos int) (int, int) {
	b := data[pos]
	pos++
	n := int(b & 0x7f)
	for b&0x80 != 0 {
		b = data[pos]
		pos++
		n = (n+1)<<7 | int(b&0x7f)
	}
	return n, pos
}

// ApplyDelta 는 델타를 바탕에 적용한다(SPEC.md §13.1). O(결과 길이).
func ApplyDelta(base, delta []byte) ([]byte, error) {
	size, pos := varintLE(delta, 0)
	if size != len(base) {
		return nil, Fail("fatal: mygit: delta base size mismatch")
	}
	want, pos := varintLE(delta, pos)
	out := make([]byte, 0, want)
	for pos < len(delta) {
		op := delta[pos]
		pos++
		switch {
		case op&0x80 != 0: // 복사
			off, n := 0, 0
			for k := 0; k < 4; k++ {
				if op&(1<<k) != 0 {
					off |= int(delta[pos]) << (8 * k)
					pos++
				}
			}
			for k := 0; k < 3; k++ {
				if op&(0x10<<k) != 0 {
					n |= int(delta[pos]) << (8 * k)
					pos++
				}
			}
			if n == 0 {
				n = 0x10000
			}
			if off+n > len(base) {
				return nil, Fail("fatal: mygit: delta copy out of " +
					"range")
			}
			out = append(out, base[off:off+n]...)
		case op != 0: // 끼움
			out = append(out, delta[pos:pos+int(op)]...)
			pos += int(op)
		default:
			return nil, Fail("fatal: mygit: delta opcode 0 is " +
				"reserved")
		}
	}
	if len(out) != want {
		return nil, Fail("fatal: mygit: delta result size mismatch")
	}
	return out, nil
}

// ReadPack 은 팩 바이트 → 항목들, 자리 차례. 앞에서부터 읽으며 zlib
// 스트림이 먹은 바이트 수로 다음 항목을 찾고, 델타는 바탕을 먼저
// 되살린 뒤 적용한다. O(팩 크기 + 되살린 크기).
func ReadPack(data []byte, ext External) ([]*PackEntry, error) {
	if len(data) < 32 || string(data[:4]) != "PACK" {
		return nil, Fail("fatal: mygit: not a pack file")
	}
	sum := Sum1(data[:len(data)-20])
	if !bytes.Equal(sum[:], data[len(data)-20:]) {
		return nil, Fail("fatal: mygit: pack checksum mismatch")
	}
	ver := binary.BigEndian.Uint32(data[4:])
	count := int(binary.BigEndian.Uint32(data[8:]))
	if ver != 2 && ver != 3 {
		return nil, Fail(fmt.Sprintf("fatal: mygit: pack version %d",
			ver))
	}
	var ents []*PackEntry
	pos := 12
	for i := 0; i < count; i++ {
		e := &PackEntry{Offset: pos, BaseOffset: -1}
		var size int
		e.PackedType, size, pos = entryHeader(data, pos)
		switch {
		case e.PackedType == ofsDelta:
			var n int
			n, pos = ofsDist(data, pos)
			e.BaseOffset = e.Offset - n
		case e.PackedType == refDelta:
			e.Base = hex.EncodeToString(data[pos : pos+20])
			pos += 20
		case typeNames[e.PackedType] == "":
			return nil, Fail(fmt.Sprintf("fatal: mygit: bad pack "+
				"entry type %d", e.PackedType))
		}
		raw, used, err := DecompressPrefix(data, pos)
		if err != nil {
			return nil, err
		}
		if len(raw) != size {
			return nil, Fail("fatal: mygit: pack entry size mismatch")
		}
		pos += used
		e.End = pos
		e.Crc = crc32.ChecksumIEEE(data[e.Offset:pos])
		if t := typeNames[e.PackedType]; t != "" {
			e.Type, e.Body = t, raw
		} else {
			e.Delta = raw
		}
		ents = append(ents, e)
	}
	if pos != len(data)-20 {
		return nil, Fail("fatal: mygit: pack has trailing garbage")
	}
	return ents, resolveDeltas(ents, ext)
}

// resolveDeltas 는 델타 사슬을 풀어 형식·몸·이름·깊이를 채운다.
// 바탕이 뒤에 있을 수 있어(REF_DELTA) 되살릴 것이 줄지 않을 때까지
// 되풀이한다. O(항목 수 × 사슬 깊이) 최악.
func resolveDeltas(ents []*PackEntry, ext External) error {
	byOff := map[int]*PackEntry{}
	byOid := map[string]*PackEntry{}
	var pending []*PackEntry
	for _, e := range ents {
		byOff[e.Offset] = e
		if e.Type != "" {
			e.Oid = HashObject(e.Type, e.Body)
			byOid[e.Oid] = e
		} else {
			pending = append(pending, e)
		}
	}
	for len(pending) > 0 {
		var left []*PackEntry
		for _, e := range pending {
			var b *PackEntry
			if e.BaseOffset >= 0 {
				if b = byOff[e.BaseOffset]; b == nil {
					return Fail("fatal: mygit: bad OFS_DELTA base")
				}
			} else if b = byOid[e.Base]; b == nil && ext != nil {
				t, body, err := ext(e.Base)
				if err != nil {
					return err
				}
				if e.Body, err = ApplyDelta(body, e.Delta); err != nil {
					return err
				}
				e.Type, e.Depth = t, 1
				e.Oid = HashObject(e.Type, e.Body)
				byOid[e.Oid] = e
				continue
			}
			if b == nil || b.Type == "" {
				left = append(left, e)
				continue
			}
			body, err := ApplyDelta(b.Body, e.Delta)
			if err != nil {
				return err
			}
			e.Type, e.Body = b.Type, body
			e.Depth, e.Base = b.Depth+1, b.Oid
			e.Oid = HashObject(e.Type, e.Body)
			byOid[e.Oid] = e
		}
		if len(left) == len(pending) {
			return Fail("fatal: mygit: unresolved delta base")
		}
		pending = left
	}
	return nil
}

// IdxEntry 는 색인의 한 줄 — 이름, 팩 안 자리, CRC.
type IdxEntry struct {
	Oid    string
	Offset int
	Crc    uint32
}

// ReadIdx 는 색인 판 2 → (항목들, 팩 체크섬 20바이트).
func ReadIdx(data []byte) ([]IdxEntry, []byte, error) {
	if len(data) < 8+256*4+40 ||
		string(data[:8]) != "\xfftOc\x00\x00\x00\x02" {
		return nil, nil, Fail("fatal: mygit: not a version 2 pack " +
			"index")
	}
	sum := Sum1(data[:len(data)-20])
	if !bytes.Equal(sum[:], data[len(data)-20:]) {
		return nil, nil, Fail("fatal: mygit: pack index checksum " +
			"mismatch")
	}
	be := binary.BigEndian
	n := int(be.Uint32(data[8+255*4:]))
	p := 8 + 256*4
	out := make([]IdxEntry, n)
	for k := range out {
		out[k].Oid = hex.EncodeToString(data[p+20*k : p+20*k+20])
		out[k].Crc = be.Uint32(data[p+20*n+4*k:])
		v := be.Uint32(data[p+24*n+4*k:])
		if v&0x80000000 != 0 { // 2 GiB 넘는 자리의 표
			big := p + 28*n + 8*int(v&0x7fffffff)
			out[k].Offset = int(be.Uint64(data[big:]))
		} else {
			out[k].Offset = int(v)
		}
	}
	return out, data[len(data)-40 : len(data)-20], nil
}

// WriteIdx 는 항목들 → 색인 판 2 바이트(SPEC.md §13.2). 이름 차례로
// 정렬한 fanout·이름·CRC·자리, 팩 체크섬, 그 앞 전부의 SHA-1. 같은
// 팩이면 git 의 .idx 와 바이트까지 같다.
func WriteIdx(entries []*PackEntry, packSum []byte) []byte {
	ents := append([]*PackEntry(nil), entries...)
	sort.Slice(ents, func(i, j int) bool {
		return ents[i].Oid < ents[j].Oid
	})
	var fan [256]uint32
	for _, e := range ents {
		b, _ := hex.DecodeString(e.Oid[:2])
		fan[b[0]]++
	}
	for k := 1; k < 256; k++ {
		fan[k] += fan[k-1]
	}
	be := binary.BigEndian
	buf := []byte("\xfftOc")
	buf = be.AppendUint32(buf, 2)
	for _, f := range fan {
		buf = be.AppendUint32(buf, f)
	}
	for _, e := range ents {
		raw, _ := hex.DecodeString(e.Oid)
		buf = append(buf, raw...)
	}
	for _, e := range ents {
		buf = be.AppendUint32(buf, e.Crc)
	}
	var big []uint64
	for _, e := range ents {
		if e.Offset >= 0x80000000 {
			buf = be.AppendUint32(buf, 0x80000000|uint32(len(big)))
			big = append(big, uint64(e.Offset))
		} else {
			buf = be.AppendUint32(buf, uint32(e.Offset))
		}
	}
	for _, o := range big {
		buf = be.AppendUint64(buf, o)
	}
	buf = append(buf, packSum...)
	sum := Sum1(buf)
	return append(buf, sum[:]...)
}

func varintOut(n int) []byte {
	var out []byte
	for {
		b := byte(n & 0x7f)
		n >>= 7
		if n == 0 {
			return append(out, b)
		}
		out = append(out, b|0x80)
	}
}

// copyOp 은 복사 명령 — 0 이 아닌 바이트만 쓴다. 길이 0x10000 은 길이
// 바이트 없이.
func copyOp(off, n int) []byte {
	op, tail := byte(0x80), []byte{}
	for k := 0; k < 4; k++ {
		if b := byte(off >> (8 * k)); b != 0 {
			op |= 1 << k
			tail = append(tail, b)
		}
	}
	if n != 0x10000 {
		for k := 0; k < 3; k++ {
			if b := byte(n >> (8 * k)); b != 0 {
				op |= 0x10 << k
				tail = append(tail, b)
			}
		}
	}
	return append([]byte{op}, tail...)
}

const block = 16

// MakeDelta 는 바탕 → 결과의 델타(SPEC.md §13.3). 다섯 언어가 같은
// 바이트를 낸다. 바탕을 16바이트 칸으로 잘라 "칸 내용 → 처음 나온
// 자리" 표를 만들고, 결과를 앞에서부터 훑으며 표에 있는 칸이면 앞으로
// 늘일 수 있는 만큼 복사, 없으면 한 바이트씩 끼울 것에 모은다.
// O(결과 길이 × 복사 길이) 최악.
func MakeDelta(base, target []byte) []byte {
	table := map[string]int{}
	for off := 0; off+block <= len(base); off += block {
		k := string(base[off : off+block])
		if _, ok := table[k]; !ok {
			table[k] = off
		}
	}
	out := append(varintOut(len(base)), varintOut(len(target))...)
	var pend []byte
	flush := func() {
		for k := 0; k < len(pend); k += 127 {
			chunk := pend[k:min(k+127, len(pend))]
			out = append(append(out, byte(len(chunk))), chunk...)
		}
		pend = pend[:0]
	}
	for i := 0; i < len(target); {
		o, ok := -1, false
		if i+block <= len(target) {
			o, ok = table[string(target[i:i+block])]
		}
		if !ok {
			pend = append(pend, target[i])
			i++
			if len(pend) == 127 {
				flush()
			}
			continue
		}
		n := block
		for o+n < len(base) && i+n < len(target) &&
			base[o+n] == target[i+n] {
			n++
		}
		flush()
		for k := 0; k < n; {
			step := min(0x10000, n-k)
			out = append(out, copyOp(o+k, step)...)
			k += step
		}
		i += n
	}
	flush()
	return out
}

func entryHead(typ, size int) []byte {
	b := byte(typ<<4) | byte(size&15)
	size >>= 4
	var out []byte
	for size > 0 {
		out = append(out, b|0x80)
		b = byte(size & 0x7f)
		size >>= 7
	}
	return append(out, b)
}

// ofsOut 은 OFS_DELTA 거리 — 큰 쪽부터, 이어지는 바이트마다 1 을 뺀다.
func ofsOut(n int) []byte {
	out := []byte{byte(n & 0x7f)}
	for n >>= 7; n > 0; n >>= 7 {
		n--
		out = append([]byte{0x80 | byte(n&0x7f)}, out...)
	}
	return out
}

// PackItem 은 WritePack 이 넣을 객체 하나. Base 는 델타 바탕의 목록
// 번호(없으면 -1) — 바탕은 목록에서 앞에 있어야 한다(OFS_DELTA).
type PackItem struct {
	Type string
	Body []byte
	Base int
}

// WritePack 은 → (팩 바이트, 항목들).
func WritePack(items []PackItem) ([]byte, []*PackEntry) {
	out := []byte("PACK")
	out = binary.BigEndian.AppendUint32(out, 2)
	out = binary.BigEndian.AppendUint32(out, uint32(len(items)))
	var ents []*PackEntry
	for _, it := range items {
		e := &PackEntry{Offset: len(out), BaseOffset: -1, Type: it.Type,
			Body: it.Body, Oid: HashObject(it.Type, it.Body)}
		raw := it.Body
		var head []byte
		if it.Base < 0 {
			e.PackedType = typeCodes[it.Type]
			head = entryHead(e.PackedType, len(raw))
		} else {
			b := ents[it.Base]
			raw = MakeDelta(b.Body, it.Body)
			e.Delta, e.PackedType, e.Base = raw, ofsDelta, b.Oid
			e.Depth, e.BaseOffset = b.Depth+1, b.Offset
			head = append(entryHead(ofsDelta, len(raw)),
				ofsOut(e.Offset-b.Offset)...)
		}
		out = append(append(out, head...), Compress(raw)...)
		e.End = len(out)
		e.Crc = crc32.ChecksumIEEE(out[e.Offset:e.End])
		ents = append(ents, e)
	}
	sum := Sum1(out)
	return append(out, sum[:]...), ents
}

// VerifyLines 는 git verify-pack -v 와 바이트까지 같은 줄들(§13.3).
func VerifyLines(entries []*PackEntry, packPath string) []string {
	ents := append([]*PackEntry(nil), entries...)
	sort.Slice(ents, func(i, j int) bool {
		return ents[i].Offset < ents[j].Offset
	})
	var rows []string
	hist := map[int]int{}
	for k, e := range ents {
		end := e.End
		if k+1 < len(ents) {
			end = ents[k+1].Offset
		}
		// 크기는 팩에 적힌 크기 — 델타면 델타의 크기다(git 과 같다)
		size := len(e.Body)
		if e.Delta != nil {
			size = len(e.Delta)
		}
		row := fmt.Sprintf("%s %-6s %d %d %d", e.Oid, e.Type, size,
			end-e.Offset, e.Offset)
		if e.Depth > 0 {
			row += fmt.Sprintf(" %d %s", e.Depth, e.Base)
		}
		rows = append(rows, row)
		hist[e.Depth]++
	}
	plural := func(n int) string {
		if n == 1 {
			return "1 object"
		}
		return fmt.Sprintf("%d objects", n)
	}
	rows = append(rows, "non delta: "+plural(hist[0]))
	delete(hist, 0)
	var depths []int
	for d := range hist {
		depths = append(depths, d)
	}
	sort.Ints(depths)
	for _, d := range depths {
		rows = append(rows, fmt.Sprintf("chain length = %d: %s", d,
			plural(hist[d])))
	}
	return append(rows, packPath+": ok")
}

// ── 팩 안의 객체 읽기 (SPEC.md §5.2) ────────────────────────────────

// packCache 는 팩 파일(경로·크기·시각)마다 되살린 객체들.
var packCache = map[string]map[string]Object{}

func init() {
	PackedObjects = packedObjects
}

// packedObjects 는 objects/pack 의 팩 안 객체 전부. 작은 저장소를 위한
// 곧은 방법이다 — 색인으로 자리를 찾아 그 항목만 푸는 대신 팩 전체를
// 되살려 기억해 둔다. 팩에 없는 REF_DELTA 바탕은 느슨한 객체에서.
func packedObjects(gitdir string) (map[string]Object, error) {
	dir := filepath.Join(gitdir, "objects", "pack")
	files, _ := os.ReadDir(dir)
	out := map[string]Object{}
	for _, f := range files {
		name := f.Name()
		if !strings.HasSuffix(name, ".idx") {
			continue
		}
		pp := filepath.Join(dir, strings.TrimSuffix(name, ".idx")+
			".pack")
		st, err := os.Stat(pp)
		if err != nil {
			continue // 짝 .pack 이 없는 색인은 없는 것으로
		}
		key := fmt.Sprintf("%s\x00%d\x00%d", pp, st.Size(),
			st.ModTime().UnixNano())
		objs, ok := packCache[key]
		if !ok {
			data, err := os.ReadFile(pp)
			if err != nil {
				return nil, err
			}
			ents, err := ReadPack(data, func(o string) (string, []byte,
				error) {
				return ReadObject(gitdir, o)
			})
			if err != nil {
				return nil, err
			}
			objs = map[string]Object{}
			for _, e := range ents {
				objs[e.Oid] = Object{e.Type, e.Body}
			}
			packCache[key] = objs
		}
		for o, v := range objs {
			if _, dup := out[o]; !dup {
				out[o] = v
			}
		}
	}
	return out, nil
}
