// 카드에 문이 셋일 때 TS 클라이언트는 어느 문을 고르나.
// 설정 셋으로 공장을 지어 같은 메시지를 보낸다. 어느 문으로
// 들어갔는지는 서버(13/doors_common.ts)의 기록이 말한다.
//   node 13/pick.ts URL
import { Message, TaskState } from "@a2a-js/sdk";
import {
  ClientFactory,
  ClientFactoryOptions,
  RestTransportFactory,
} from "@a2a-js/sdk/client";
import { GrpcTransportFactory } from "@a2a-js/sdk/client/grpc";

// region: configs
const two = [new GrpcTransportFactory(), new RestTransportFactory()];
const configs: Record<string, ClientFactoryOptions> = {
  기본: ClientFactoryOptions.default,
  "GRPC·HTTP+JSON": { transports: two },
  "GRPC 우선": { transports: two, preferredTransports: ["GRPC"] },
};
// endregion

const message = Message.fromJSON({
  ...{ messageId: "m-1", role: "ROLE_USER" },
  parts: [{ text: "2026-10-30 1박 30명" }],
});
for (const [label, options] of Object.entries(configs)) {
  const client = await new ClientFactory(options).createFromUrl(
    process.argv[2],
  );
  const state = await client
    .sendMessage({
      ...{ tenant: "", message },
      ...{ configuration: undefined, metadata: undefined },
    })
    .then((r) =>
      "messageId" in r
        ? "Message"
        : TaskState[r.status!.state].slice(11),
    )
    // 실패도 한 줄로
    .catch((e: Error) => `실패 ${e.constructor.name}`);
  console.log(`${label} → ${state}`);
}
//@ norun
