// 슬라이드 p4-v3-ext-near — 가까운 네임스페이스가 이긴다, C# 3.0
using System;

namespace Outer
{
    static class OuterExt
    {
        public static string Who(this int x) { return "Outer"; }
    }

    namespace Inner
    {
        static class InnerExt
        {
            public static string Who(this int x)
            {
                return "Outer.Inner";
            }
        }

        class App
        {
            static void Main()
            {
                Console.WriteLine("from Inner: " + 1.Who());
                Probe.Run();
            }
        }
    }

    class Probe
    {
        public static void Run()
        {
            Console.WriteLine("from Outer: " + 1.Who());
        }
    }
}
