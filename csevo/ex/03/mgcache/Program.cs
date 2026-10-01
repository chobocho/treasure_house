// 슬라이드 p3-v2-mg-cache — 메서드 그룹 변환의 대리자 객체, C# 2.0
using System;

delegate void D();

class App
{
    static void M() { }

    static void Main()
    {
        D[] ds = new D[2];
        for (int i = 0; i < 2; i++) ds[i] = M;    // one site, twice
        Console.WriteLine("same site:  " +
            object.ReferenceEquals(ds[0], ds[1]));
        D a = M;
        D b = M;                                   // two sites
        Console.WriteLine("two sites:  " +
            object.ReferenceEquals(a, b));
        Console.WriteLine("equal (==): " + (a == b));
    }
}
