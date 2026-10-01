// 슬라이드 p3-v2-anon-why — 익명 메서드 이전의 대리자, C# 1.0
using System;
using System.Collections;

delegate bool Test(int x);

class Above                  // a class only to carry 'limit'
{
    int limit;
    public Above(int limit) { this.limit = limit; }
    public bool Check(int x) { return x > limit; }
}

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
        Test t = new Test(new Above(limit).Check);
        foreach (int x in Filter(xs, t)) Console.Write(x + " ");
        Console.WriteLine();
    }
}
