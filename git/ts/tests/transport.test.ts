// 전송의 시험 — SPEC.md §14, 12단계 "pkt-line 으로 진짜 git 과 대화".
//
// fetch-pack 은 진짜 git upload-pack 을 자식으로 띄워 말한다(PLAN.md
// §9 결정 8 — 서버는 git 이다). golden/pkt/<경우>.log 는 SPEC §14.3 의
// 요청을 그대로 보냈을 때 git 이 돌려준 대화의 기록이고, mygit 의
// 기록은 글자까지 같아야 한다. 받은 팩 바이트와 표준 출력도 같아야
// 한다. 멍청한 clone 은 golden/scen/clone.scn 이 장면 시험으로 본다.
import * as assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { afterEach, beforeEach, describe, test } from 'node:test';
import * as cli from '../src/cli';
import * as objects from '../src/objects';
import * as refs from '../src/refs';
import * as transport from '../src/transport';
import * as golden from './golden';

const CASES = ['full', 'two-refs', 'have-first'];

describe('pkt-line', () => {
  test('s14_1 length counts itself', () => {
    const pkt = (s: string) => transport.pktLine(Buffer.from(s))
      .toString();
    assert.equal(pkt('a\n'), '0006a\n');
    assert.equal(pkt(''), '0004');
    assert.equal(pkt('x'.repeat(65516)).slice(0, 4), 'fff0');
  });

  test('s14_3 render like the golden log', () => {
    assert.equal(transport.render(Buffer.from('command=ls-refs\n')),
      '0014command=ls-refs\\n');
  });
});

describe('fetch-pack', () => {
  const box = { tmp: '', src: '', root: '', gitdir: '' };
  const env = () => ({ ...process.env,
    GIT_CEILING_DIRECTORIES: box.tmp });

  async function setUp(): Promise<void> {
    box.tmp = golden.tempdir();
    box.src = path.join(box.tmp, 'src');
    fs.cpSync(golden.gpath('pkt', 'src', 'git'),
      path.join(box.src, '.git'), { recursive: true });
    for (const d of ['objects/pack', 'refs/tags']) {
      fs.mkdirSync(path.join(box.src, '.git', d), { recursive: true });
    }
    box.root = path.join(box.tmp, 'local');
    fs.mkdirSync(box.root);
    await cli.run(['init'], box.root, env());
    box.gitdir = path.join(box.root, '.git');
  }
  beforeEach(setUp);
  afterEach(() => golden.rmTree(box.tmp));

  async function fetch(name: string):
    Promise<[number, Buffer, Buffer, string]> {
    const [wants, haves] = golden.read('pkt', name + '.args').toString()
      .split('\n');
    if (haves) {
      // 가진 값 = 로컬 참조. 원본의 객체를 넣고 참조를 세운다
      const objs = path.join(box.gitdir, 'objects');
      fs.rmSync(objs, { recursive: true });
      fs.cpSync(path.join(box.src, '.git', 'objects'), objs,
        { recursive: true });
      refs.updateRef(box.gitdir, 'refs/heads/old', haves, null, 'test',
        'T <t@t> 0 +0000');
    }
    const log = path.join(box.tmp, name + '.log');
    const [code, out, err] = await cli.run(
      ['fetch-pack', box.src, ...wants.split(' ')], box.root,
      { ...env(), MYGIT_PKT_LOG: log });
    return [code, out, err, fs.readFileSync(log, 'utf8')];
  }

  test('s14_3 conversation matches git', async () => {
    for (const name of CASES) {
      const [code, out, err, log] = await fetch(name);
      assert.deepEqual([code, err.toString()], [0, ''], name);
      assert.deepEqual(out, golden.read('pkt', name + '.stdout'), name);
      assert.equal(log, golden.read('pkt', name + '.log').toString(),
        name);
      golden.rmTree(box.tmp);
      await setUp();
    }
  });

  test('s14_3 received pack is stored and readable', async () => {
    await fetch('full');
    const want = golden.read('pkt', 'full.pack');
    const name = `pack-${want.subarray(-20).toString('hex')}.pack`;
    assert.deepEqual(fs.readFileSync(path.join(box.gitdir, 'objects',
      'pack', name)), want);
    const head = golden.read('pkt', 'full.stdout').toString()
      .split(' ')[0];
    assert.equal(objects.readObject(box.gitdir, head)[0], 'commit');
  });
});
