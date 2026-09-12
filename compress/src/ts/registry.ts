// 알고리즘 이름 → 부호기·복호기. 이름이 곧 golden/ 의 디렉터리다.
// 다섯 언어가 같은 이름·같은 순서를 갖는다.
import { Bytes } from './common';
import * as ans from './ans';
import * as bitio from './bitio';
import * as bwt from './bwt';
import * as deflate from './deflate';
import * as huffman from './huffman';
import * as intcode from './intcode';
import * as lzss from './lzss';
import * as lzw from './lzw';
import * as mtf from './mtf';
import * as rangecoder from './rangecoder';
import * as rle from './rle';

export type Codec = (src: Bytes) => Bytes;

export interface Entry {
  name: string;
  encode: Codec;
  decode: Codec;
}

// 순서가 곧 배우는 순서다 (PLAN.md §3 Tier 1).
export const ENTRIES: Entry[] = [
  { name: 'bitio', encode: bitio.encode, decode: bitio.decode },
  { name: 'intcode', encode: intcode.encode, decode: intcode.decode },
  { name: 'rle', encode: rle.encode, decode: rle.decode },
  { name: 'mtf', encode: mtf.encode, decode: mtf.decode },
  { name: 'huffman', encode: huffman.encode, decode: huffman.decode },
  { name: 'lzss', encode: lzss.encode, decode: lzss.decode },
  { name: 'lzw', encode: lzw.encode, decode: lzw.decode },
  { name: 'rangecoder',
    encode: rangecoder.encode, decode: rangecoder.decode },
  { name: 'bwt', encode: bwt.encode, decode: bwt.decode },
  { name: 'deflate', encode: deflate.encode, decode: deflate.decode },
  { name: 'ans', encode: ans.encode, decode: ans.decode },
];

export function find(name: string): Entry | undefined {
  return ENTRIES.find((e) => e.name === name);
}
