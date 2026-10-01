// 슬라이드 p3-v2-anon-trace — 스택 트레이스에 보이는 이름, C# 2.0
using System;

delegate void Step(int x);

class App
{
    static void Each(int[] xs, Step s)
    {
        foreach (int x in xs) s(x);
    }

    static void Main()
    {
        int[] xs = new int[] { 1, 0 };
        Each(xs, delegate(int x)
        {
            Console.WriteLine(10 / x);
        });
    }
}
