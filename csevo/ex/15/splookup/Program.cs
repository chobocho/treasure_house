// 슬라이드 p15-v14-sp-lookup — 확장 메서드 찾기가 바뀐다, C# 14
using System;

namespace N1
{
    using N2;

    public static class N1Ext
    {
        public static string Test(this ReadOnlySpan<string> s) => "N1";
    }

    public class Program
    {
        public static void Main()
        {
            Span<string> span = new string[0];
            Console.WriteLine(span.Test());   // inner scope first
        }
    }
}

namespace N2
{
    public static class N2Ext
    {
        public static string Test(this Span<string> s) => "N2";
    }
}
