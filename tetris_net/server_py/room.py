# -*- coding: utf-8 -*-
"""room.py — 방 하나의 게임 규칙. **순수 상태 기계**다.

소켓도 타이머도 time.time() 도 없다. (pid, 메시지, now) 를 넣으면
[(누구에게, 무엇을)] 이 나온다. 그래야 Go·JS 구현과 같은 골든 벡터로 검증할 수 있다.

규격 전문은 ../protocol.md, 검증표는 ../protocol_vectors.json.
room.mjs / room.go 와 나란히 놓고 읽어도 될 만큼 구조를 맞춰 뒀다.
"""

DEFAULTS = {
    'max': 8,          # 좌석 수 (1~8)
    'perPeer': 2,      # PC 1대가 쥘 수 있는 좌석 수 — "한 PC 에서 최대 2명"이 이 한 줄이다
    'target': 'random',
    'delay': 900,      # 가비지 유예(ms). 서버는 중계만 하고 지키는 건 클라이언트다
    'cap': 8,          # 한 락에서 솟을 수 있는 최대 줄
    'hitTTL': 8000,    # "최근에 나를 때렸다"로 치는 시간(ms)
}

MASK32 = 0xFFFFFFFF


class Room:
    def __init__(self, cfg=None, seed=1):
        self.cfg = dict(DEFAULTS)
        self.cfg.update(cfg or {})
        if self.cfg['max'] < 1:
            self.cfg['max'] = 1
        self.seats = [None] * self.cfg['max']
        self.phase = 'lobby'
        self.peers = set()
        self.rng_state = (seed & MASK32) or 1
        self.round_seed = 0

    # 규격의 xorshift32. 세 구현이 여기서부터 갈리면 그 뒤는 볼 것도 없다.
    def rng(self):
        x = self.rng_state
        x ^= (x << 13) & MASK32
        x ^= x >> 17
        x ^= (x << 5) & MASK32
        self.rng_state = x & MASK32
        return self.rng_state

    # ── 조회 헬퍼 ──
    def host(self):
        return min(self.peers) if self.peers else 0

    def occupied(self):
        return [i for i, s in enumerate(self.seats) if s is not None]

    def alive_seats(self):
        return [i for i in self.occupied() if self.seats[i]['alive']]

    def mine(self, pid):
        return [i for i in self.occupied() if self.seats[i]['pid'] == pid]

    def seat_list(self):
        out = []
        for i in self.occupied():
            s = self.seats[i]
            out.append({'i': i, 'pid': s['pid'], 'name': s['name'], 'kind': s['kind'],
                        'lv': s['lv'], 'ready': s['ready'], 'alive': s['alive']})
        return out

    def room_msg(self):
        return [(0, {'t': 'room', 'host': self.host(), 'seats': self.seat_list()})]

    @staticmethod
    def err(pid, code):
        return [(pid, {'t': 'err', 'code': code})]

    # ── 진입점 ──
    def handle(self, pid, msg, now):
        t = (msg or {}).get('t')
        if t == 'bye':
            return self.on_bye(pid, now)
        self.peers.add(pid)
        fn = {
            'seat': self.on_seat, 'unseat': self.on_unseat, 'ready': self.on_ready,
        }.get(t)
        if fn:
            return fn(pid, msg)
        if t == 'start':
            return self.on_start(pid)
        if t == 'atk':
            return self.on_atk(pid, msg, now)
        if t == 'st':
            return self.on_st(pid, msg)
        if t == 'ko':
            return self.on_ko(pid, msg, now)
        return []

    def on_seat(self, pid, m):
        if self.phase != 'lobby':
            return self.err(pid, 'phase')
        i = m.get('i')
        i = -1 if i is None else int(i)
        if i < 0:                                  # 자동 배정 = 가장 앞의 빈 자리
            i = next((k for k, s in enumerate(self.seats) if s is None), -1)
            if i < 0:
                return self.err(pid, 'seat')
        elif i >= len(self.seats) or self.seats[i] is not None:
            return self.err(pid, 'seat')
        # 자리를 먼저 확정하고 그다음에 PC 당 좌석 수를 본다. 순서를 바꾸면
        # "빈 자리도 없고 내 몫도 찼을 때" 어느 오류가 나가는지가 구현마다 달라진다.
        if len(self.mine(pid)) >= self.cfg['perPeer']:
            return self.err(pid, 'full')
        self.seats[i] = {
            'pid': pid, 'name': m.get('name') or '',
            'kind': 'ai' if m.get('kind') == 'ai' else 'human', 'lv': m.get('lv') or '',
            'ready': False, 'alive': True, 'recv': 0, 'height': 0, 'place': 0, 'hits': [],
        }
        return self.room_msg()

    def on_unseat(self, pid, m):
        if self.phase != 'lobby':
            return self.err(pid, 'phase')
        i = int(m.get('i', -1))
        if i < 0 or i >= len(self.seats) or self.seats[i] is None or self.seats[i]['pid'] != pid:
            return self.err(pid, 'own')
        self.seats[i] = None
        return self.room_msg()

    def on_ready(self, pid, m):
        if self.phase != 'lobby':
            return self.err(pid, 'phase')
        v = bool(m.get('v'))
        for i in self.mine(pid):
            self.seats[i]['ready'] = v
        return self.room_msg()

    def on_start(self, pid):
        if self.phase != 'lobby':
            return self.err(pid, 'phase')
        if pid != self.host():
            return self.err(pid, 'host')
        occ = self.occupied()
        if not occ:
            return self.err(pid, 'seat')
        # AI 좌석은 준비를 기다리지 않는다 — 누를 사람이 없다.
        for i in occ:
            if self.seats[i]['kind'] == 'human' and not self.seats[i]['ready']:
                return self.err(pid, 'ready')
        self.round_seed = self.rng()
        self.phase = 'play'
        for i in occ:
            s = self.seats[i]
            s['alive'], s['recv'], s['height'], s['place'], s['hits'] = True, 0, 0, 0, []
        return [(0, {'t': 'start', 'seed': self.round_seed, 'seats': self.seat_list()})]

    # ── 공격 라우팅 — 이 게임에서 서버가 하는 유일한 판단 ──
    def pick_target(self, frm, now):
        cand = [j for j in self.alive_seats() if j != frm]
        if not cand:
            return -1
        mode = self.cfg['target']
        if mode == 'even':                         # 가장 덜 맞은 쪽 — 난수를 쓰지 않는다
            return min(cand, key=lambda j: (self.seats[j]['recv'], j))
        if mode == 'ko':                           # 가장 높이 쌓인 쪽 = 죽기 직전
            return min(cand, key=lambda j: (-self.seats[j]['height'], j))
        if mode == 'attackers':                    # 최근에 나를 때린 쪽에 반격
            for h in reversed(self.seats[frm]['hits']):
                if now - h['at'] > self.cfg['hitTTL']:
                    break                          # hits 는 시간순이라 여기서 끊으면 된다
                if h['from'] != frm and self.seats[h['from']] and self.seats[h['from']]['alive']:
                    return h['from']
            # 기억이 없으면 random 으로 떨어진다 — 이때만 난수를 쓴다
        return cand[self.rng() % len(cand)]

    def on_atk(self, pid, m, now):
        if self.phase != 'play':
            return self.err(pid, 'phase')
        i = int(m.get('i', -1))
        if i < 0 or i >= len(self.seats) or self.seats[i] is None or self.seats[i]['pid'] != pid:
            return self.err(pid, 'own')
        n = int(m.get('n', 0))
        if n <= 0 or not self.seats[i]['alive']:
            return []
        j = self.pick_target(i, now)
        if j < 0:
            return []                              # 혼자 남았거나 1인용 — 공격은 허공으로
        hole = self.rng() % 10
        self.seats[j]['recv'] += n
        self.seats[j]['hits'].append({'from': i, 'at': now})
        # 관전 화면이 "누가 누구를" 화살표로 그려야 하므로 피해자에게만 보내지 않는다.
        return [(0, {'t': 'grb', 'i': j, 'n': n, 'from': i, 'hole': hole})]

    def on_st(self, pid, m):
        if self.phase != 'play':
            return self.err(pid, 'phase')
        i = int(m.get('i', -1))
        if i < 0 or i >= len(self.seats) or self.seats[i] is None or self.seats[i]['pid'] != pid:
            return self.err(pid, 'own')
        s = m.get('s') or []
        if len(s) > 4:
            self.seats[i]['height'] = int(s[4])     # 서버가 읽는 칸은 s[0], s[4] 뿐
        return [(p, {'t': 'st', 'i': i, 'b': m.get('b'), 's': m.get('s')})
                for p in sorted(self.peers) if p != pid]

    # 좌석 하나를 탈락시킨다. end 까지 낼 수 있으므로 out 을 받아 이어 붙인다.
    def kill(self, i, now, out):
        if self.phase != 'play':
            return
        s = self.seats[i]
        if s is None or not s['alive']:
            return
        place = len(self.alive_seats())             # 지금 살아 있는 수 = 그대로 등수
        s['alive'] = False
        s['place'] = place
        by = -1
        for h in reversed(s['hits']):
            if now - h['at'] > self.cfg['hitTTL']:
                break
            if h['from'] != i:
                by = h['from']
                break
        out.append((0, {'t': 'ko', 'i': i, 'place': place, 'by': by}))

        left = self.alive_seats()
        if len(left) <= 1:
            if len(left) == 1:
                self.seats[left[0]]['place'] = 1
            self.phase = 'over'
            order = sorted(self.occupied(), key=lambda k: self.seats[k]['place'])
            out.append((0, {'t': 'end', 'order': order}))

    def on_ko(self, pid, m, now):
        if self.phase != 'play':
            return self.err(pid, 'phase')
        i = int(m.get('i', -1))
        if i < 0 or i >= len(self.seats) or self.seats[i] is None or self.seats[i]['pid'] != pid:
            return self.err(pid, 'own')
        out = []
        self.kill(i, now, out)
        return out

    # PC 가 끊겼다. 로비면 자리를 비우고, 대전 중이면 그 PC 의 좌석이 번호 순으로 전멸한다.
    def on_bye(self, pid, now):
        if pid not in self.peers:
            return []
        self.peers.discard(pid)
        held = self.mine(pid)
        if self.phase == 'play':
            out = []
            for i in held:
                self.kill(i, now, out)   # kill() 이 phase 를 over 로 바꾸면 뒤는 무시된다
            return out
        for i in held:
            self.seats[i] = None
        return self.room_msg()           # 방장이 바뀔 수 있으므로 항상 알린다
