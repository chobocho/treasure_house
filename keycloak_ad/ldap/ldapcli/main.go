// ldapcli — LDAP 을 눈으로 보게 해 주는 도구.
//
// 널리 쓰이는 ldapsearch 는 결과만 보여 준다. 이 도구는 **오간
// 바이트**를 함께 보여 준다. 3부에서 "LDAP 은 바이트다" 를 증명하는
// 자리이자, 7부에서 Keycloak 이 보낸 것과 우리가 보낸 것을 견주는
// 자리다.
//
//	go run ./ldap/ldapcli -h localhost:10389 \
//	    -D 'CN=svc-keycloak,OU=Service Accounts,\
//	        DC=ad,DC=campus,DC=example' \
//	    -w 'Passw0rd!-demo' \
//	    search '(sAMAccountName=minji)' cn mail
//
//		go run ./ldap/ldapcli -h localhost:10389 \
//		    -D 'CN=Kim Minji,OU=Students,DC=ad,DC=campus,DC=example' \
//		    -w 'Passw0rd!-demo' bind
//
//		go run ./ldap/ldapcli -h localhost:10636 -ldaps \
//
// -cacert certs/demo-ca.crt -name ldap.ad.campus.example ... search ...
package main

import (
	"crypto/tls"
	"crypto/x509"
	"flag"
	"fmt"
	"net"
	"os"
	"strings"
	"time"

	"treasure/keycloak_ad/ldap/ber"
	"treasure/keycloak_ad/ldap/proto"
)

func usage() {
	fmt.Fprint(os.Stderr, `사용법:
  ldapcli [옵션] bind
  ldapcli [옵션] search '(필터)' [속성...]

옵션:
`)
	flag.PrintDefaults()
}

func main() {
	host := flag.String("h", "localhost:10389", "서버 주소")
	bindDN := flag.String("D", "", "바인드 DN (또는 UPN)")
	pass := flag.String("w", "", "비밀번호")
	base := flag.String("b", "DC=ad,DC=campus,DC=example",
		"검색 시작점")
	scope := flag.String("s", "sub", "범위: base · one · sub")
	useTLS := flag.Bool("ldaps", false, "처음부터 TLS 로 붙는다")
	caFile := flag.String("cacert", "", "믿을 CA 인증서")
	srvName := flag.String("name", "", "인증서에서 확인할 이름")
	insecure := flag.Bool("k", false, "인증서를 확인하지 않는다 (위험)")
	quiet := flag.Bool("q", false, "바이트 풀이를 생략하고 결과만")
	flag.Usage = usage
	flag.Parse()

	args := flag.Args()
	if len(args) == 0 {
		usage()
		os.Exit(2)
	}

	c, err := dial(*host, *useTLS, *caFile, *srvName, *insecure)
	if err != nil {
		fmt.Fprintf(os.Stderr, "붙지 못했다: %v\n", err)
		os.Exit(1)
	}
	defer c.Close()
	cl := &client{conn: c, quiet: *quiet}

	if err := cl.bind(*bindDN, *pass); err != nil {
		fmt.Fprintf(os.Stderr, "%v\n", err)
		os.Exit(1)
	}
	if args[0] == "bind" {
		return
	}
	if args[0] != "search" || len(args) < 2 {
		usage()
		os.Exit(2)
	}
	if err := cl.search(*base, *scope, args[1], args[2:]); err != nil {
		fmt.Fprintf(os.Stderr, "%v\n", err)
		os.Exit(1)
	}
}

func dial(host string, useTLS bool, caFile, srvName string,
	insecure bool) (net.Conn, error) {
	if !useTLS {
		return net.DialTimeout("tcp", host, 5*time.Second)
	}
	cfg := &tls.Config{InsecureSkipVerify: insecure}
	if srvName != "" {
		cfg.ServerName = srvName
	}
	if caFile != "" {
		pem, err := os.ReadFile(caFile)
		if err != nil {
			return nil, err
		}
		pool := x509.NewCertPool()
		if !pool.AppendCertsFromPEM(pem) {
			return nil, fmt.Errorf("%s 를 CA 로 못 읽겠다", caFile)
		}
		cfg.RootCAs = pool
	}
	return tls.Dial("tcp", host, cfg)
}

type client struct {
	conn  net.Conn
	buf   []byte
	seq   int64
	quiet bool
}

// send 는 한 통을 보내면서, 보내기 전에 그 바이트를 풀어 보여 준다.
func (c *client) send(raw []byte, what string) {
	if !c.quiet {
		fmt.Printf("→ 보냄 %s (%d바이트)\n", what, len(raw))
		fmt.Print(Dump(raw))
		fmt.Println()
	}
	c.conn.Write(raw)
}

func (c *client) recv() (proto.Message, error) {
	c.conn.SetReadDeadline(time.Now().Add(10 * time.Second))
	tmp := make([]byte, 4096)
	for {
		n, err := ber.MessageLength(c.buf)
		if err == nil && len(c.buf) >= n {
			msg, perr := proto.ParseMessage(c.buf[:n])
			if !c.quiet {
				fmt.Printf("← 받음 (%d바이트)\n", n)
				fmt.Print(Dump(c.buf[:n]))
				fmt.Println()
			}
			c.buf = c.buf[n:]
			return msg, perr
		}
		r, rerr := c.conn.Read(tmp)
		if r > 0 {
			c.buf = append(c.buf, tmp[:r]...)
			continue
		}
		return proto.Message{}, fmt.Errorf("더 읽을 수 없다: %v", rerr)
	}
}

func (c *client) next() int64 { c.seq++; return c.seq }

func (c *client) bind(dn, pass string) error {
	id := c.next()
	raw := ber.Seq(ber.Int(id),
		ber.Encode(ber.Tag(ber.Application, true, proto.OpBindRequest),
			cat(ber.Int(3), ber.Str(dn),
				ber.Encode(ber.Tag(ber.Context, false, 0),
					[]byte(pass)))))
	c.send(raw, "BindRequest")
	msg, err := c.recv()
	if err != nil {
		return err
	}
	fmt.Print(Describe(msg))
	kids, err := ber.Children(msg.Op.Value)
	if err != nil || len(kids) < 1 {
		return fmt.Errorf("바인드 응답을 못 읽는다")
	}
	code, _ := kids[0].Int()
	if code != proto.ResultSuccess {
		return fmt.Errorf("바인드 실패: %s",
			proto.ResultName(int(code)))
	}
	return nil
}

func (c *client) search(base, scope, filter string,
	attrs []string) error {
	f, err := proto.ParseFilterString(filter)
	if err != nil {
		return fmt.Errorf("필터: %w", err)
	}
	var al [][]byte
	for _, a := range attrs {
		al = append(al, ber.Str(a))
	}
	id := c.next()
	raw := ber.Seq(ber.Int(id),
		ber.Encode(
			ber.Tag(ber.Application, true, proto.OpSearchRequest),
			cat(ber.Str(base), ber.Enum(int64(scopeNum(scope))),
				ber.Enum(0), ber.Int(0), ber.Int(0), ber.Bool(false),
				proto.EncodeFilter(f), ber.Seq(al...))))
	c.send(raw, "SearchRequest")

	found := 0
	for {
		msg, err := c.recv()
		if err != nil {
			return err
		}
		fmt.Print(Describe(msg))
		if msg.OpNum() == proto.OpSearchResultDone {
			fmt.Printf("\n찾은 항목 %d개\n", found)
			return nil
		}
		found++
	}
}

func scopeNum(s string) int {
	switch strings.ToLower(s) {
	case "base":
		return proto.ScopeBaseObject
	case "one":
		return proto.ScopeSingleLevel
	}
	return proto.ScopeWholeSubtree
}

func cat(parts ...[]byte) []byte {
	var out []byte
	for _, p := range parts {
		out = append(out, p...)
	}
	return out
}
