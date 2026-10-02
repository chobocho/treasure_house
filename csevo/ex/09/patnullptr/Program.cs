// 슬라이드 p9-v8-nullptr — 포인터에 null 상수 패턴, C# 8.0
using System;

unsafe class App
{
    static string Kind(int* p) => p switch
    {
        null => "null pointer",
        _ => "points to " + *p,
    };

    static void Main()
    {
        int x = 5;
        int* p = &x;
        int* q = null;
        Console.WriteLine(Kind(p));
        Console.WriteLine(Kind(q));
        Console.WriteLine("{0} {1}", p is null, q == null);
    }
}
