package compresslib

// 알고리즘 이름 → 부호기·복호기. 이름이 곧 golden/ 의 디렉터리다.
// 다섯 언어가 같은 이름·같은 순서를 갖는다.

type Codec func([]byte) ([]byte, error)

type Entry struct {
	Name   string
	Encode Codec
	Decode Codec
}

// 순서가 곧 배우는 순서다 (PLAN.md §3 Tier 1).
var Entries = []Entry{
	{"bitio", BitioEncode, BitioDecode},
	{"intcode", IntcodeEncode, IntcodeDecode},
	{"rle", RleEncode, RleDecode},
	{"mtf", MtfEncode, MtfDecode},
	{"huffman", HuffmanEncode, HuffmanDecode},
	{"lzss", LzssEncode, LzssDecode},
	{"lzw", LzwEncode, LzwDecode},
	{"rangecoder", RangecoderEncode, RangecoderDecode},
	{"bwt", BwtEncode, BwtDecode},
	{"deflate", DeflateEncode, DeflateDecode},
}

func Find(name string) *Entry {
	for i := range Entries {
		if Entries[i].Name == name {
			return &Entries[i]
		}
	}
	return nil
}
