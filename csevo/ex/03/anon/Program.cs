// 슬라이드 p3-v2-anon-gate — 익명 메서드, C# 2.0
using System;
using System.Collections;

delegate bool Test(int x);

class App
{
    static ArrayList Filter(int[] xs, Test t)
    {
        ArrayList r = new ArrayList();
        foreach (int x in xs) if (t(x)) r.Add(x);
        return r;
    }

    static void Main()
    {
        int[] xs = new int[] { 3, 8, 1, 9, 5 };
        int limit = 4;
        Test t = delegate(int x) { return x > limit; };
        foreach (int x in Filter(xs, t)) Console.Write(x + " ");
        Console.WriteLine();
    }
}
