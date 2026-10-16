// JSON-RPC 2.0 요청 하나를 표준 기능만으로 만든다.
// region: request
const request = {
  jsonrpc: "2.0",
  id: 1,
  method: "SendMessage",
  params: {
    message: {
      role: "ROLE_USER",
      messageId: "msg-1",
      parts: [{ text: "1박 2일, 30명" }],
    },
  },
};
// endregion

console.log(JSON.stringify(request, null, 2));
