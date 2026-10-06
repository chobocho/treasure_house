// 슬라이드 p14-v13-wave — 경고 웨이브 9 는 없다, C# 13
using System;

ref struct Holder
{
    public ref int R;           // never ref-assigned
    public int Read() => System.Runtime.CompilerServices.Unsafe
        .IsNullRef(ref R) ? -1 : R;
}

class Program
{
    static void Main()
    {
        var h = new Holder();
        Console.WriteLine(h.Read());
    }
}
