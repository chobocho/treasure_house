// 슬라이드 p7-v6-small — 열거형의 기반 형식을 형식 이름으로, C# 6.0
using System;

enum Small : System.Byte { A = 1, B = 255 }
enum Plain : int { C }

class Program
{
    static int[] Get(params int[] a) { return a; }

    static void Main()
    {
        Console.WriteLine(Enum.GetUnderlyingType(typeof(Small)).Name);
        Console.WriteLine(Enum.GetUnderlyingType(typeof(Plain)).Name);
        // params with no arguments: one shared empty array?
        Console.WriteLine(Get().Length + " "
            + ReferenceEquals(Get(), Get()) + " "
            + ReferenceEquals(Get(), Array.Empty<int>()));
    }
}
