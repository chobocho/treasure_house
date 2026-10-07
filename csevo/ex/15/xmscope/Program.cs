// 슬라이드 p15-v14-xm-scope — 가까운 범위가 이긴다, C# 14
using System;

namespace Outer
{
    static class OuterExt
    {
        public static string Tag(this int n) => "outer(this)";
        extension(int n) { public string Kind => "outer(block)"; }
    }

    namespace Inner
    {
        static class InnerExt
        {
            extension(int n)
            {
                public string Tag() => "inner(block)";
            }
        }

        class Program
        {
            static void Main()
            {
                Console.WriteLine(5.Tag());         // inner wins
                Console.WriteLine(5.Kind);          // only in outer
                Console.WriteLine(OuterExt.Tag(5)); // explicit
            }
        }
    }
}
