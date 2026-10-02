// 슬라이드 p5-v4-opt-params — 선택적 매개변수 뒤의 params, C# 4.0
using System;

class Program
{
    static void P(int a = 1, params int[] rest)
    {
        Console.WriteLine("a=" + a + " rest=" + rest.Length);
    }

    static void Main()
    {
        P();
        P(5);
        P(5, 6, 7);
        P(rest: new int[] { 8, 9 });
        P(rest: 8);
    }
}
