# 🎮 Scheme(Racket) 기반 테트리스 만들기 가이드북
순수 표준 Scheme 자체는 내장된 그래픽/GUI 라이브러리가 없기 때문에, 게임을 개발할 때는 Scheme의 가장 대중적이고 강력한 방언(Dialect)인 **Racket**과 그 내장 라이브러리인 2htdp/universe를 사용하는 것이 표준적인 방법입니다.
이 가이드북은 Racket을 사용하여 상태(State) 기반의 함수형 프로그래밍 방식으로 동작하는 테트리스를 만드는 방법을 안내합니다.
## 1. 개발 환경 준비
 1. **DrRacket 설치**: Racket 공식 홈페이지(https://racket-lang.org/)에서 DrRacket IDE를 다운로드하고 설치합니다.
 2. **언어 설정**: DrRacket을 실행하고, 파일의 맨 첫 줄에 #lang racket을 선언하여 Racket 언어를 사용함을 명시합니다.
## 2. 핵심 개념 설계
함수형 프로그래밍에서의 게임 개발은 **"상태(World State)를 어떻게 정의하고, 시간(Tick)과 이벤트(Key)에 따라 상태를 어떻게 변화시킬 것인가"**로 귀결됩니다.
 * **블록 (Block)**: 보드에 고정된 1칸 단위의 블록 (x, y 좌표와 색상).
 * **테트로미노 (Tetro)**: 현재 위에서 떨어지고 있는 조각. (중심 좌표와 4개 블록의 상대 좌표 배열).
 * **월드 (World)**: 게임 전체의 상태. (보드에 고정된 블록 리스트, 현재 떨어지는 조각, 점수, 게임오버 상태).
## 3. 풀 소스 코드
아래의 코드는 복사하여 DrRacket에 붙여넣기만 하면 즉시 동작하는 완성된 테트리스 소스 코드입니다. 하단의 (start)를 실행하면 게임 창이 열립니다.
```scheme
#lang racket
(require 2htdp/image 2htdp/universe)

;;; --- 1. 상수 및 기본 설정 ---
(define W 10)  ; 보드 가로 칸 수
(define H 20)  ; 보드 세로 칸 수
(define S 25)  ; 블록 한 칸의 픽셀 크기
(define BG (empty-scene (* W S) (* H S) "black"))

;;; --- 2. 데이터 구조 ---
;; block: 고정된 개별 블록 (x, y 좌표와 색상)
(struct block (x y color) #:transparent)
;; tetro: 움직이는 테트로미노 (현재 x, y 중심과 상대 좌표 리스트, 색상)
(struct tetro (x y blocks color) #:transparent)
;; world: 게임 전체 상태 (고정된 블록들, 움직이는 블록, 점수, 게임오버 여부)
(struct world (board active score game-over?) #:transparent)

;; 테트로미노 모양 정의 (상대 좌표)
(define SHAPES
  (list
   (list "cyan"   '((0 . 0) (1 . 0) (2 . 0) (3 . 0)))  ; I
   (list "yellow" '((0 . 0) (1 . 0) (0 . 1) (1 . 1)))  ; O
   (list "purple" '((1 . 0) (0 . 1) (1 . 1) (2 . 1)))  ; T
   (list "green"  '((1 . 0) (2 . 0) (0 . 1) (1 . 1)))  ; S
   (list "red"    '((0 . 0) (1 . 0) (1 . 1) (2 . 1)))  ; Z
   (list "blue"   '((0 . 0) (0 . 1) (1 . 1) (2 . 1)))  ; J
   (list "orange" '((2 . 0) (0 . 1) (1 . 1) (2 . 1))))) ; L

;; 새로운 테트로미노 생성
(define (spawn)
  (define shape (list-ref SHAPES (random (length SHAPES))))
  (tetro 3 0 (second shape) (first shape)))

;;; --- 3. 렌더링 (그리기) 함수 ---
(define (draw-block b img)
  (place-image (overlay (square (- S 1) "solid" (block-color b))
                        (square S "solid" "gray"))
               (+ (* (block-x b) S) (/ S 2))
               (+ (* (block-y b) S) (/ S 2))
               img))

(define (draw-tetro t img)
  (foldl (lambda (pt acc)
           (draw-block (block (+ (tetro-x t) (car pt))
                              (+ (tetro-y t) (cdr pt))
                              (tetro-color t))
                       acc))
         img
         (tetro-blocks t)))

(define (draw-world w)
  (define scene
    (if (world-game-over? w)
        (place-image (text "GAME OVER" 30 "white") (/ (* W S) 2) (/ (* H S) 2) BG)
        (foldl draw-block BG (world-board w))))
  (define scene-with-active
    (if (world-game-over? w) scene (draw-tetro (world-active w) scene)))
  (place-image (text (number->string (world-score w)) 20 "white")
               20 20 scene-with-active))

;;; --- 4. 게임 로직 ---
;; 충돌 검사 (벽 또는 다른 블록)
(define (collision? t board)
  (for/or ([pt (tetro-blocks t)])
    (define nx (+ (tetro-x t) (car pt)))
    (define ny (+ (tetro-y t) (cdr pt)))
    (or (< nx 0) (>= nx W) (< ny 0) (>= ny H)
        (for/or ([b board])
          (and (= nx (block-x b)) (= ny (block-y b)))))))

;; 회전 로직 (90도 회전 행렬 적용)
(define (rotate t)
  (if (equal? (tetro-color t) "yellow") t ; O 모양은 회전하지 않음
      (tetro (tetro-x t) (tetro-y t)
             (map (lambda (pt) (cons (- (cdr pt)) (car pt))) (tetro-blocks t))
             (tetro-color t))))

;; 블록 고정 및 줄 삭제 처리
(define (merge-and-clear w)
  (define t (world-active w))
  ;; 1. 움직이던 블록을 고정된 블록 리스트로 변환
  (define new-blocks
    (map (lambda (pt) (block (+ (tetro-x t) (car pt))
                             (+ (tetro-y t) (cdr pt))
                             (tetro-color t)))
         (tetro-blocks t)))
  (define merged-board (append new-blocks (world-board w)))
  
  ;; 2. 꽉 찬 줄 찾기
  (define (row-count r)
    (length (filter (lambda (b) (= (block-y b) r)) merged-board)))
  (define full-rows
    (filter (lambda (r) (= (row-count r) W)) (build-list H values)))
  
  ;; 3. 줄 삭제 및 위에 있는 블록 내리기
  (define cleared-board
    (foldl (lambda (r acc)
             (map (lambda (b)
                    (if (< (block-y b) r)
                        (block (block-x b) (+ (block-y b) 1) (block-color b))
                        b))
                  (filter (lambda (b) (not (= (block-y b) r))) acc)))
           merged-board
           (sort full-rows <))) ; 위에서부터 순차적으로 지워야 좌표가 꼬이지 않음
  
  (define next-t (spawn))
  (world cleared-board next-t 
         (+ (world-score w) (* (length full-rows) 100))
         (collision? next-t cleared-board))) ; 스폰 즉시 충돌이면 게임오버

;; 매 틱마다 블록 낙하
(define (tick w)
  (if (world-game-over? w) w
      (let ([next-t (tetro (tetro-x (world-active w)) (+ (tetro-y (world-active w)) 1)
                           (tetro-blocks (world-active w)) (tetro-color (world-active w)))])
        (if (collision? next-t (world-board w))
            (merge-and-clear w)
            (world (world-board w) next-t (world-score w) #f)))))

;; 키보드 입력 처리
(define (handle-key w key)
  (if (world-game-over? w) w
      (let* ([t (world-active w)]
             [next-t
              (cond [(string=? key "left")  (tetro (- (tetro-x t) 1) (tetro-y t) (tetro-blocks t) (tetro-color t))]
                    [(string=? key "right") (tetro (+ (tetro-x t) 1) (tetro-y t) (tetro-blocks t) (tetro-color t))]
                    [(string=? key "down")  (tetro (tetro-x t) (+ (tetro-y t) 1) (tetro-blocks t) (tetro-color t))]
                    [(string=? key "up")    (rotate t)]
                    [else t])])
        (if (collision? next-t (world-board w)) w
            (world (world-board w) next-t (world-score w) #f)))))

;;; --- 5. 게임 실행 ---
(define (start)
  (big-bang (world '() (spawn) 0 #f)
    (on-tick tick 0.5)         ; 0.5초마다 tick 함수 호출 (낙하 속도)
    (on-key handle-key)        ; 키보드 이벤트 핸들링
    (to-draw draw-world)       ; 화면 그리기
    (name "Scheme Tetris")))

;; REPL이나 최하단에 아래 코드를 입력해 실행하세요
;; (start)

```
## 4. 조작 방법
코드 최하단에 (start)를 작성하거나 DrRacket의 REPL 창에 (start)를 입력하여 게임을 실행합니다.

| 입력 키 | 동작 설명 |
|---|---|
| **왼쪽 방향키 (Left)** | 테트로미노를 왼쪽으로 한 칸 이동 |
| **오른쪽 방향키 (Right)** | 테트로미노를 오른쪽으로 한 칸 이동 |
| **아래 방향키 (Down)** | 테트로미노를 한 칸 빠르게 낙하 (Soft Drop) |
| **위 방향키 (Up)** | 테트로미노를 90도 회전 |

※ 회전은 도형의 로컬 원점(0,0) 기준이라 표준 테트리스(SRS)와 달리 회전 시 위치가 약간 이동합니다 — 교육용 단순화입니다.
## 5. 코드 동작 원리 가이드
 * **상태 불변성 (Immutability)**: 이 코드는 변수의 값을 직접 수정하는 파괴적 할당(set!)을 사용하지 않습니다. tick 함수나 handle-key 함수는 현재의 world 상태를 입력으로 받아, **새롭게 계산된 다음 world 상태를 반환**합니다.
 * **big-bang 아키텍처**: 2htdp/universe의 big-bang은 초기 상태를 인자로 받아 무한 루프를 돌며 on-tick(시간 경과), on-key(키 입력) 이벤트가 발생할 때마다 상태를 업데이트하고, 업데이트된 상태를 to-draw로 전달하여 화면에 새롭게 렌더링합니다.
 * **foldl을 활용한 렌더링**: 보드 위에 누적된 블록들을 리스트의 시작부터 끝까지 순회하며 화면을 도화지(acc) 위에 덧그리는 로직은 foldl 함수를 통해 우아하게 처리됩니다.

---
## 🔗 관련 문서
- [[Lua Tetris]]
- [[체커 게임 만들기]]
- [[Todo]]
