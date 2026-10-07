// 슬라이드 p15-v14-wave — 경고 웨이브 10 의 CS9265 가 보는 것, C# 14
using System;
using System.Runtime.CompilerServices;

ref struct Refs
{
    public ref int A;            // ref-assigned in the constructor
    public ref int B;            // ref-assigned in an initializer
    public ref int C;            // never ref-assigned, only read

    public Refs(ref int x) { A = ref x; }
}

class Program
{
    static void Main()
    {
        int n = 1;
        var r = new Refs(ref n) { B = ref n };
        r.A = 2;
        Console.WriteLine(n + " " + r.B + " "
            + Unsafe.IsNullRef(ref r.C));
    }
}
