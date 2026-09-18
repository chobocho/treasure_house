// 팩의 시험 — SPEC.md §13, 11단계 "packfile — 읽기, 그다음 쓰기".
//
// golden/pack/ 은 진짜 git 이 쓴 팩 둘이다 — ofs(repack 이 쓴,
// OFS_DELTA)와 ref(pack-objects 가 쓴, REF_DELTA). .verify 는 git
// verify-pack -v, .show-index 는 git show-index 의 출력이다. 가장 강한
// 시험은 git 의 팩에서 mygit 이 다시 만든 색인이 git 의 .idx 와
// 바이트까지 같은가다.
import * as assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { afterEach, beforeEach, describe, test } from 'node:test';
import * as cli from '../src/cli';
import * as objects from '../src/objects';
import * as pack from '../src/pack';
import * as golden from './golden';

const NAMES = ['ofs', 'ref'];

// git show-index → [자리, 이름, crc 8글자].
function showIndex(name: string): [number, string, string][] {
  const text = golden.read('pack', name + '.show-index').toString();
  return text.split('\n').filter((l) => l).map((line) => {
    const [off, oid, crc] = line.split(' ');
    return [Number(off), oid, crc.slice(1, -1)];
  });
}

const packSize = (e: pack.PackEntry) => (e.delta ?? e.body)!.length;

describe('read', () => {
  test('s13_1 every object and its delta chain', () => {
    for (const name of NAMES) {
      const ents = pack.readPack(golden.read('pack', name + '.pack'));
      const want = new Map<string, string[]>();
      const text = golden.read('pack', name + '.verify').toString();
      for (const line of text.split('\n')) {
        const cols = line.split(/\s+/);
        if (cols.length >= 5 && cols[0].length === 40) {
          want.set(cols[0], cols);
        }
      }
      assert.deepEqual(ents.map((e) => e.oid).sort(),
        [...want.keys()].sort(), name);
      for (const e of ents) {
        const cols = want.get(e.oid)!;
        // 크기 칸은 팩에 적힌 크기 — 델타면 델타의 크기(§13.3)
        assert.deepEqual([e.type, packSize(e), e.offset],
          [cols[1], Number(cols[2]), Number(cols[4])]);
        if (cols.length > 5) {
          assert.deepEqual([e.depth, e.base],
            [Number(cols[5]), cols[6]], e.oid);
        }
        assert.equal(objects.hashObject(e.type, e.body!), e.oid);
      }
      const kinds = new Set(ents.map((e) => e.packedType));
      assert.ok(kinds.has(name === 'ofs' ? 6 : 7), name);
    }
  });

  test('s13_2 idx matches show-index', () => {
    for (const name of NAMES) {
      const idx = pack.readIdx(golden.read('pack', name + '.idx'));
      const got = idx.entries.map(([oid, off, crc]) =>
        [off, oid, crc.toString(16).padStart(8, '0')]);
      const key = (r: (string | number)[]) => r.join(' ');
      assert.deepEqual(got.map(key).sort(),
        showIndex(name).map(key).sort(), name);
    }
  });

  test('s13_1 bad trailer', () => {
    const data = Buffer.from(golden.read('pack', 'ofs.pack'));
    data[data.length - 1] ^= 1;
    golden.assertGitError(() => pack.readPack(data));
  });
});

describe('write idx', () => {
  test('s13_2 rebuilt idx is byte identical to git', () => {
    for (const name of NAMES) {
      const data = golden.read('pack', name + '.pack');
      const ents = pack.readPack(data);
      assert.deepEqual(pack.writeIdx(ents, data.subarray(-20)),
        golden.read('pack', name + '.idx'), name);
    }
  });
});

describe('delta', () => {
  test('s13_1 apply deltas from git', () => {
    let n = 0;
    for (const name of NAMES) {
      const ents = pack.readPack(golden.read('pack', name + '.pack'));
      const byOid = new Map(ents.map((e) => [e.oid, e]));
      for (const e of ents) {
        if (!e.base) continue;
        assert.deepEqual(
          pack.applyDelta(byOid.get(e.base)!.body!, e.delta!), e.body);
        n++;
      }
    }
    assert.ok(n > 0);
  });

  test('s13_3 make delta bytes are pinned', () => {
    // SPEC.md §13.3 의 알고리즘을 손으로 따라가 얻은 바이트:
    // 크기 32 · 34, 복사(0,16), 끼움 "XY", 복사(0,16)
    const base = Buffer.from('0123456789abcdef'.repeat(2));
    const target = Buffer.concat([base.subarray(0, 16),
      Buffer.from('XY'), base.subarray(16)]);
    assert.deepEqual(pack.makeDelta(base, target),
      Buffer.from('\x20\x22\x90\x10\x02XY\x90\x10', 'latin1'));
  });

  test('s13_3 round trip', () => {
    const base = golden.make('counter:70000');
    const bang = Buffer.concat([base.subarray(0, 30000),
      Buffer.from('!'), base.subarray(30000)]);
    const rev = Buffer.from(base).reverse().subarray(0, 5000);
    for (const target of [base, bang, Buffer.alloc(0),
      Buffer.alloc(300, 'x'), Buffer.concat([rev, base])]) {
      const d = pack.makeDelta(base, target);
      assert.deepEqual(pack.applyDelta(base, d), target);
    }
  });

  test('s13_1 delta errors', () => {
    const abc = Buffer.from('abc');
    golden.assertGitError(() => pack.applyDelta(abc,
      Buffer.from([3, 1, 0])));                    // 예약 명령 0
    golden.assertGitError(() => pack.applyDelta(abc,
      Buffer.from('\x04\x01\x01x', 'latin1')));    // 바탕 크기가 틀림
  });
});

function repo() {
  const box = { tmp: '', root: '', gitdir: '' };
  const run = async (...args: string[]): Promise<Buffer> => {
    const [code, out, err] = await cli.run(args, box.root, {
      ...process.env, GIT_CEILING_DIRECTORIES: box.tmp,
      GIT_AUTHOR_NAME: 'A', GIT_AUTHOR_EMAIL: 'a@x',
      GIT_AUTHOR_DATE: '1700000000 +0900', GIT_COMMITTER_NAME: 'C',
      GIT_COMMITTER_EMAIL: 'c@x',
      GIT_COMMITTER_DATE: '1700000000 +0900' });
    assert.equal(code, 0, `${args.join(' ')}: ${err}`);
    return out;
  };
  beforeEach(async () => {
    box.tmp = golden.tempdir();
    box.root = path.join(box.tmp, 'w');
    box.gitdir = path.join(box.root, '.git');
    fs.mkdirSync(box.root);
    await run('init');
  });
  afterEach(() => golden.rmTree(box.tmp));
  return { box, run };
}

describe('verify-pack', () => {
  const { box, run } = repo();

  test('s13_3 output is git verbatim', async () => {
    for (const name of NAMES) {
      for (const ext of ['pack', 'idx']) {
        fs.writeFileSync(path.join(box.root, `${name}.${ext}`),
          golden.read('pack', `${name}.${ext}`));
      }
      const out = await run('verify-pack', '-v', name + '.idx');
      assert.deepEqual(out, golden.read('pack', name + '.verify'),
        name);
    }
  });
});

describe('objects in packs', () => {
  const { box, run } = repo();

  test('s13_3 unpack then read loose', async () => {
    fs.writeFileSync(path.join(box.root, 'ofs.pack'),
      golden.read('pack', 'ofs.pack'));
    await run('unpack-pack', 'ofs.pack');
    for (const [, oid] of showIndex('ofs')) {
      const p = objects.objectPath(box.gitdir, oid);
      assert.ok(fs.existsSync(p), oid);
    }
  });

  test('s5_2 read object finds packed objects', () => {
    const pdir = path.join(box.gitdir, 'objects', 'pack');
    for (const ext of ['pack', 'idx']) {
      fs.writeFileSync(path.join(pdir, 'pack-x.' + ext),
        golden.read('pack', 'ofs.' + ext));
    }
    for (const [, oid] of showIndex('ofs')) {
      const [t, body] = objects.readObject(box.gitdir, oid);
      assert.equal(objects.hashObject(t, body), oid);
      assert.equal(objects.findObject(box.gitdir, oid.slice(0, 8)),
        oid);
    }
  });
});

describe('pack-objects', () => {
  const { box, run } = repo();

  async function makeHistory(): Promise<void> {
    let body = '';
    for (let i = 0; i < 200; i++) {
      body += `line ${i} of a growing file\n`;
    }
    for (let v = 0; v < 4; v++) {
      fs.writeFileSync(path.join(box.root, 'grow.txt'),
        body + `extra ${v}\n`.repeat(v + 1));
      await run('add', '.');
      await run('commit', '-m', `v${v}`);
    }
  }

  async function check(delta: boolean): Promise<pack.PackEntry[]> {
    await makeHistory();
    const flags = delta ? ['--delta'] : [];
    const sha = (await run('pack-objects', ...flags,
      '.git/objects/pack/pack')).toString().trim();
    const stem = path.join(box.gitdir, 'objects', 'pack',
      `pack-${sha}`);
    const data = fs.readFileSync(stem + '.pack');
    assert.equal(data.subarray(-20).toString('hex'), sha);
    const ents = pack.readPack(data);
    const idx = pack.readIdx(fs.readFileSync(stem + '.idx'));
    const oids = ents.map((e) => e.oid).sort();
    assert.deepEqual(idx.entries.map(([o]) => o).sort(), oids);
    assert.deepEqual(objects.allLoose(box.gitdir).sort(), oids);
    return ents;
  }

  test('s13_3 plain pack holds every object', async () => {
    const ents = await check(false);
    assert.ok(ents.every((e) => e.packedType < 5));
  });

  test('s13_3 delta pack uses ofs deltas', async () => {
    const deltas = (await check(true))
      .filter((e) => e.packedType === pack.OFS_DELTA);
    // 옛 판 셋이 한 판씩 새것을 바탕으로 — 깊이 1·2·3
    assert.equal(deltas.length, 3);
    assert.deepEqual(deltas.map((e) => e.depth).sort(), [1, 2, 3]);
  });
});
