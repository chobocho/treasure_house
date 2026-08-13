#!r7rs
(import (scheme base) (scheme write)
        (except (srfi 1) assoc member map for-each list-copy)
        (except (srfi 13) string->list string-copy string-fill!))
(display "GW-BASIC Scheme bootstrap OK\n")
