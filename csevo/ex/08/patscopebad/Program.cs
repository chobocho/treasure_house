// 슬라이드 p8-v7-pat-scopebad — 넓은 범위가 낳는 오류, C# 7.0
using System;

class App
{
    static void M(object o)
    {
        if (o is int n) Console.WriteLine(n);
        Console.WriteLine(n);               // in scope, not assigned

        if (o is string s) { }
        if (o is string s) { }              // same block: same name

        while (o is long m) { o = null; }
        Console.WriteLine(m);               // while: own scope

        if (o != null) Console.WriteLine(o is int k);
        Console.WriteLine(k);               // embedded statement scope
    }

    static void Main() { }
}
