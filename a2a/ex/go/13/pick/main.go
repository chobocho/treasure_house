// 카드에 문이 셋일 때 Go 클라이언트는 어느 문을 고르나.
// 설정 셋으로 클라이언트를 지어 같은 메시지를 보낸다. 어느 문으로
// 들어갔는지는 서버(13/grpcmount 의 ServeDoors)의 기록이 말한다.
//
//	go run ./13/pick URL
package main

import (
	"context"
	"fmt"
	"os"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
	a2agrpc "github.com/a2aproject/a2a-go/v2/a2agrpc/v1"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

var plain = grpc.WithTransportCredentials(insecure.NewCredentials())

// region: configs
// JSON-RPC 를 뺀 둘: 기본값을 끄고 gRPC·HTTP+JSON 만 단다
var two = []a2aclient.FactoryOption{a2aclient.WithDefaultsDisabled(),
	a2agrpc.WithGRPCTransport(plain), a2aclient.WithRESTTransport(nil)}
var grpcFirst = a2aclient.WithConfig(a2aclient.Config{
	PreferredTransports: []a2a.TransportProtocol{
		a2a.TransportProtocolGRPC},
})
var configs = []struct {
	label string
	opts  []a2aclient.FactoryOption
}{
	{"기본", nil},
	{"GRPC·HTTP+JSON", two},
	{"GRPC 우선", append(two[:3:3], grpcFirst)},
}

// endregion

func main() {
	ctx := context.Background()
	card, err := agentcard.DefaultResolver.Resolve(ctx, os.Args[1])
	if err != nil {
		panic(err)
	}
	for _, c := range configs {
		client, err := a2aclient.NewFromCard(ctx, card, c.opts...)
		if err != nil {
			panic(err)
		}
		m := a2a.NewMessage(a2a.MessageRoleUser,
			a2a.NewTextPart("2026-10-30 1박 30명"))
		m.ID = "m-1"
		res, err := client.SendMessage(ctx,
			&a2a.SendMessageRequest{Message: m})
		if err != nil { // 실패도 한 줄로
			fmt.Printf("%s → 실패 %v\n", c.label, err)
			continue
		}
		state := strings.TrimPrefix(
			string(res.(*a2a.Task).Status.State), "TASK_STATE_")
		fmt.Printf("%s → %s\n", c.label, state)
		client.Destroy()
	}
}

//@ norun
