// 슬라이드 p14-v13-mg-scope — 확장 메서드도 안쪽 범위부터, C# 13
using System;

class C { }

namespace Outer
{
    static class E1
    {
        public static void M(this C c, string s)
            => Console.WriteLine("E1.M(string)");
    }

    namespace Inner
    {
        static class E2
        {
            public static void M(this C c, int x)
                => Console.WriteLine("E2.M(int)");
        }

        class Program
        {
            static void Main()
            {
                var f = new C().M;   // Inner's E2 before Outer's E1
                f(1);
                Console.WriteLine(f.GetType().Name);
            }
        }
    }
}
