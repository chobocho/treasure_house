package mygit

// 인덱스 (SPEC.md §7) — .git/index, 다음 커밋이 될 트리의 초안.
//
// 작업 트리와 저장소 사이의 이 파일 하나가 "스테이징" 의 실체다.
// 항목마다 경로·모드·blob 이름과 함께 파일의 stat 칸(시각·크기·
// inode)을 적어 두는데, git 은 그것으로 "안 바뀐 파일" 을 해시 없이
// 가려낸다. mygit 은 칸을 채워 두기만 하고 자신은 믿지 않는다(§7.2).
//
// 판 2 로 쓰고, 판 2·3 을 읽는다. 확장(TREE·REUC…)은 읽을 때
// 건너뛰고 쓰지 않는다. 수는 전부 빅 엔디언.

import (
	"bytes"
	"encoding/binary"
	"encoding/hex"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"syscall"
)

const maxName = 0xfff

// IndexEntry 는 인덱스 항목 하나. 이름은 16진 40글자.
type IndexEntry struct {
	Path, Oid                        string
	Mode, Size                       uint32
	Stage                            int
	CtimeS, CtimeNs, MtimeS, MtimeNs uint32
	Dev, Ino, Uid, Gid               uint32
	AssumeValid, SkipWorktree        bool
}

// EntryFromStat 는 작업 트리 파일의 stat 으로 항목을 채운다(§7.2).
// 모드는 소유자 실행 비트만 본다 — git 과 같다. 칸은 32비트로 자른다.
func EntryFromStat(path, abspath, oid string) (*IndexEntry, error) {
	var st syscall.Stat_t
	if err := syscall.Stat(abspath, &st); err != nil {
		return nil, err
	}
	e := &IndexEntry{Path: path, Oid: oid, Mode: 0o100644,
		Size: uint32(st.Size)}
	if st.Mode&0o100 != 0 {
		e.Mode = 0o100755
	}
	e.CtimeS, e.CtimeNs = uint32(st.Ctim.Sec), uint32(st.Ctim.Nsec)
	e.MtimeS, e.MtimeNs = uint32(st.Mtim.Sec), uint32(st.Mtim.Nsec)
	e.Dev, e.Ino = uint32(st.Dev), uint32(st.Ino)
	e.Uid, e.Gid = st.Uid, st.Gid
	return e, nil
}

// ParseIndex 는 인덱스 바이트 → 항목들. 끝 SHA-1 이 틀리면 오류.
// 판 3 은 flags 의 비트 14 가 서 있는 항목 뒤에 2바이트 확장 flags 가
// 더 있다(skip-worktree 가 거기 산다). O(파일 크기).
func ParseIndex(data []byte) ([]*IndexEntry, error) {
	corrupt := Fail("fatal: mygit: index file corrupt")
	if len(data) < 32 || string(data[:4]) != "DIRC" {
		return nil, corrupt
	}
	sum := Sum1(data[:len(data)-20])
	if !bytes.Equal(sum[:], data[len(data)-20:]) {
		return nil, corrupt
	}
	be := binary.BigEndian
	ver, count := be.Uint32(data[4:]), be.Uint32(data[8:])
	if ver == 4 {
		return nil, Fail("fatal: mygit: index v4 unsupported")
	}
	if ver != 2 && ver != 3 {
		return nil, Fail(fmt.Sprintf("fatal: mygit: index version %d",
			ver))
	}
	var out []*IndexEntry
	pos := 12
	for i := uint32(0); i < count; i++ {
		if pos+62 > len(data)-20 {
			return nil, corrupt
		}
		u := func(k int) uint32 { return be.Uint32(data[pos+4*k:]) }
		flags := be.Uint16(data[pos+60:])
		e := &IndexEntry{CtimeS: u(0), CtimeNs: u(1), MtimeS: u(2),
			MtimeNs: u(3), Dev: u(4), Ino: u(5), Mode: u(6), Uid: u(7),
			Gid: u(8), Size: u(9),
			Oid:         hex.EncodeToString(data[pos+40 : pos+60]),
			Stage:       int(flags>>12) & 3,
			AssumeValid: flags&0x8000 != 0}
		start := pos + 62
		if flags&0x4000 != 0 { // 판 3 의 확장 flags
			e.SkipWorktree = be.Uint16(data[start:])&0x4000 != 0
			start += 2
		}
		// 이름 길이가 0xfff 를 넘어도 NUL 까지 읽는다
		end := bytes.IndexByte(data[start:], 0)
		if end < 0 {
			return nil, corrupt
		}
		e.Path = string(data[start : start+end])
		pos += (start - pos + end + 8) / 8 * 8
		out = append(out, e)
	}
	return out, nil
}

// SerializeIndex 는 항목들 → 판 2 인덱스 바이트. 경로·단계 차례로
// 정렬한다. 항목 길이 = (62 + 이름 길이 + 8) &^ 7 — NUL 이 1‥8 개.
// 판 2 에는 확장 flags 가 없으므로 skip-worktree 는 여기서 사라진다.
func SerializeIndex(ents []*IndexEntry) []byte {
	s := append([]*IndexEntry(nil), ents...)
	sort.Slice(s, func(i, j int) bool {
		if s[i].Path != s[j].Path {
			return s[i].Path < s[j].Path
		}
		return s[i].Stage < s[j].Stage
	})
	be := binary.BigEndian
	buf := []byte("DIRC")
	buf = be.AppendUint32(buf, 2)
	buf = be.AppendUint32(buf, uint32(len(s)))
	for _, e := range s {
		start := len(buf)
		for _, v := range []uint32{e.CtimeS, e.CtimeNs, e.MtimeS,
			e.MtimeNs, e.Dev, e.Ino, e.Mode, e.Uid, e.Gid, e.Size} {
			buf = be.AppendUint32(buf, v)
		}
		raw, _ := hex.DecodeString(e.Oid)
		buf = append(buf, raw...)
		flags := uint16(e.Stage<<12) | uint16(min(len(e.Path), maxName))
		if e.AssumeValid {
			flags |= 0x8000
		}
		buf = be.AppendUint16(buf, flags)
		buf = append(buf, e.Path...)
		n := len(buf) - start
		buf = append(buf, make([]byte, 8-n%8)...)
	}
	sum := Sum1(buf)
	return append(buf, sum[:]...)
}

// ReadIndex 는 .git/index 를 읽는다. 없으면(첫 add 전) 빈 목록.
func ReadIndex(gitdir string) ([]*IndexEntry, error) {
	data, err := os.ReadFile(filepath.Join(gitdir, "index"))
	if errors.Is(err, fs.ErrNotExist) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return ParseIndex(data)
}

// WriteIndex 는 index.lock 에 쓰고 이름을 바꿔 넣는다(SPEC.md §7.4).
func WriteIndex(gitdir string, ents []*IndexEntry) error {
	p := filepath.Join(gitdir, "index")
	f, err := os.OpenFile(p+".lock", os.O_WRONLY|os.O_CREATE|os.O_EXCL,
		0o666)
	if errors.Is(err, fs.ErrExist) {
		return Fail("fatal: mygit: unable to lock " + p)
	}
	if err != nil {
		return err
	}
	_, err = f.Write(SerializeIndex(ents))
	f.Close()
	if err != nil {
		return err
	}
	return os.Rename(p+".lock", p)
}
