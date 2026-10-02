// 슬라이드 p10-v9-top-trace — 스택 트레이스에 보이는 이름, C# 9.0
using System;
using System.Runtime.CompilerServices;

Console.WriteLine(Who());
Fail(0);

static string Who([CallerMemberName] string n = "") => "caller: " + n;
static void Fail(int x) => Console.WriteLine(10 / x);
