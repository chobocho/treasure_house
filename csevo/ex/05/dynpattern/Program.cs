// 슬라이드 p5-v4-dyn-pattern — 뒤 버전: dynamic 에 패턴 맞추기, C# 7.0
using System;

class Program
{
    static string Describe(dynamic d)
    {
        if (d is int n) return "int " + (n + 1);
        if (d is string s) return "string of " + s.Length;
        return "other";
    }

    static void Main()
    {
        Console.WriteLine(Describe(41));
        Console.WriteLine(Describe("four"));
        Console.WriteLine(Describe(4.0));
#if BAD
        dynamic e = 1;
        if (e is dynamic x) Console.WriteLine(x);
#endif
    }
}
