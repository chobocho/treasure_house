// 트레이스·해시·리플레이·락스텝 부명령 (SPEC §18.3, §19, §20, §24).

import * as fs from 'fs';
import * as path from 'path';

import * as H from './harness';
import * as F from '../src/fixed';
import * as MAIN from '../src/main';

H.title('trace');

const N = 40;
const tr = MAIN.cmdTrace(N).split('\n').slice(0, -1);
H.check('틱마다 한 줄', tr.length, N);
H.check('첫 줄의 틱', tr[0].slice(0, 6), '{"t":1');
H.check('마지막 줄의 틱', tr[tr.length - 1].indexOf('{"t":' + N + ',') === 0,
        true);
H.check('키 순서가 명세대로',
        ['"t":', '"h":', '"cr":', '"su":', '"sc":', '"n":', '"ev":']
          .filter((k) => tr[0].indexOf(k) < 0), []);
H.check('공백이 없다', tr[0].indexOf(' ') >= 0, false);
H.check('해시는 8자리 대문자 16진',
        tr.filter((ln) => {
          const h = ln.split('"h":"')[1].slice(0, 8);
          return h.toUpperCase() !== h;
        }).length, 0);
H.check('두 번 돌려도 같다', MAIN.cmdTrace(N).split('\n').slice(0, -1), tr);

const hs = MAIN.cmdHashes(N).split('\n').slice(0, -1);
H.check('해시 줄 수', hs.length, N);
H.check('형식은 "틱 해시"', H.fields(hs[0])[0], '1');
H.check('트레이스의 해시와 같다', hs.map((ln) => H.fields(ln)[1]),
        tr.map((ln) => ln.split('"h":"')[1].slice(0, 8)));
H.checkTrue('해시가 변한다', new Set(hs).size === N);

const out = MAIN.cmdLockstep(60);
H.checkTrue('락스텝 60틱 일치', out.indexOf('락스텝 60틱 일치') >= 0);
H.checkTrue('float_bug 실험 결과가 한 줄 나온다', out.indexOf('float_bug:') >= 0);
const lines = out.trim().split('\n');
H.note(lines[lines.length - 2]);

const tmp = path.join(H.BASE, 'out');
if (!fs.existsSync(tmp)) fs.mkdirSync(tmp, { recursive: true });
const p = path.join(tmp, 'test_replay.bin');
const msg = MAIN.cmdReplay(p, 60);
H.checkTrue('리플레이 재생이 일치한다',
            msg.trim().slice(msg.trim().length - 2) === '일치');
H.checkTrue('리플레이는 작다 (' + msg.trim() + ')',
            fs.statSync(p).size < 4096);
const head: number[] = [];
const buf = fs.readFileSync(p);
for (let i = 0; i < 4; i += 1) head.push(buf[i]);
H.check('상태는 저장하지 않는다 — 파일에 머리 넷 글자', head, F.ascii('RTSR'));
fs.unlinkSync(p);

H.done();
