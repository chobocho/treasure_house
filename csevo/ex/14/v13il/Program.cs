// 슬라이드 p14-v13-pm-lower — params 호출과 lock 이 만드는 IL, C# 13
using System;
using System.Collections.Generic;
using System.Threading;

class Program
{
    static int A(params int[] xs) => xs.Length;
    static int S(params ReadOnlySpan<int> xs) => xs.Length;
    static int E(params IEnumerable<int> xs) => 0;

    static int ArrayVars(int x) => A(x, x, x);
    static int SpanConsts() => S(1, 2, 3);
    static int SpanVars(int x) => S(x, x, x);
    static int SpanNone() => S();
    static int EnumVars(int x) => E(x, x, x);
    static readonly Lock gate = new();
    static readonly object monitor = new();
    static int n;

    static void LockLock() { lock (gate) { n++; } }
    static void LockObject() { lock (monitor) { n++; } }

    static void Main(string[] args)
    {
        foreach (string m in args) Il.Calls(m);
    }
}
