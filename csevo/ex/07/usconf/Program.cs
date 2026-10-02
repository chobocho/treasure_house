// 슬라이드 p7-v6-us-conflict — 같은 이름이 둘 이상이면, C# 6.0
using System;
using static A;
using static B;

static class A
{
    public static string F(int x) => "A.F(int)";
    public static string G() => "A.G";
    public static string H() => "A.H";
}

static class B
{
    public static string F(string s) => "B.F(string)";
    public static string G() => "B.G";
}

class Program
{
    static string H() => "Program.H";

    static void Main()
    {
        Console.WriteLine(F(1));          // overloads across A and B
        Console.WriteLine(F("s"));
        Console.WriteLine(H());           // own member comes first
#if BAD
        Console.WriteLine(G());
#endif
    }
}
