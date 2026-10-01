// 슬라이드 p4-v3-ext-ambig — 같은 자리에서 둘이 보이면 모호하다, C# 3.0
using System;
using Left;
using Right;

namespace Left
{
    static class L
    {
        public static string Side(this int x) { return "left"; }
    }
}

namespace Right
{
    static class R
    {
        public static string Side(this int x) { return "right"; }
    }
}

class App
{
    static void Main()
    {
        Console.WriteLine(1.Side());
    }
}
