// 슬라이드 p10-v9-top-locfn — 최상위의 함수는 지역 함수, C# 9.0
using System;
using System.Reflection;

int calls = 0;
Console.WriteLine(Add(2, 3) + " " + Twice(4) + " calls=" + calls);

int Add(int a, int b) { calls++; return a + b; }  // captures calls
static int Twice(int x) => x * 2;                 // captures nothing
#if BAD
int Add(int a, int b, int c) => a + b + c;        // an overload?
#endif

BindingFlags all = BindingFlags.Static | BindingFlags.Instance
    | BindingFlags.NonPublic | BindingFlags.DeclaredOnly;
foreach (MethodInfo m in typeof(Program).GetMethods(all))
    Console.WriteLine("method " + m.Name);
foreach (Type n in typeof(Program).GetNestedTypes(all))
    Console.WriteLine("nested " + n.Name);
