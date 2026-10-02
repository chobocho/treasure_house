// 슬라이드 p7-v6-us-string — 정적·인스턴스 멤버가 섞인 String, C# 6.0
using System;
using static System.String;
#if BAD
using static string;
#endif

class Program
{
    static void Main()
    {
        string[] parts = { "a", "b", "c" };
        Console.WriteLine(Join("-", parts));
        Console.WriteLine(Concat("x", "y"));
        Console.WriteLine(IsNullOrEmpty(Empty));
    }
}
