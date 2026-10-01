// 슬라이드 p2-v1-oppair — 짝으로 선언해야 하는 연산자, C# 1.0
using System;

class Version
{
    public int N;
    public static bool operator ==(Version a, Version b)
    {
        return a.N == b.N;
    }
    public static bool operator <(Version a, Version b)
    {
        return a.N < b.N;
    }
}

class App
{
    static void Main()
    {
        Version a = new Version(), b = new Version();
        Console.WriteLine(a == b);
    }
}
