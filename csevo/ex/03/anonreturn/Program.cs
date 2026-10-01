// 슬라이드 p3-v2-anon-jump — 익명 메서드 안의 return, C# 2.0
using System;

delegate void Visit(int x);

class App
{
    static void Each(int[] xs, Visit v)
    {
        foreach (int x in xs) v(x);
    }

    static void Main()
    {
        int[] xs = new int[] { 1, 2, 3, 4 };
        Each(xs, delegate(int x)
        {
            if (x % 2 == 0) return;     // leaves this call only
            Console.WriteLine("odd " + x);
        });
        Console.WriteLine("Main goes on");
    }
}
