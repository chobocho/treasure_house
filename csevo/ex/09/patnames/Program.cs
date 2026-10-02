// 슬라이드 p9-v8-pospat-names — 위치 패턴의 이름, C# 8.0
using System;

class Range2
{
    public int Lo, Hi;
    public void Deconstruct(out int lo, out int hi)
    {
        lo = Lo;
        hi = Hi;
    }
}

class App
{
    static void Main()
    {
        var r = new Range2 { Lo = 0, Hi = 9 };
        // names are optional; when written, they are checked
        Console.WriteLine(r is (lo: 0, hi: var h) ? "hi " + h : "-");
        var t = (Width: 3, Height: 4);
        if (t is (Width: 3, Height: var y))
            Console.WriteLine("y " + y);
#if BAD
        Console.WriteLine(r is (low: 0, _));
        Console.WriteLine(t is (Height: 3, _));
#endif
    }
}
