// 슬라이드 p4-v3-ext-using — using 으로 들여와야 보인다, C# 3.0
using System;

namespace Tools
{
    static class StringExt
    {
        public static string Shout(this string s)
        {
            return s.ToUpper() + "!";
        }
    }
}

// global namespace: searched only when nothing nearer was found
static class Fallback
{
    public static string Shout(this object o) { return "(fallback)"; }
}

namespace Demo
{
#if !NOUSING
    using Tools;
#endif

    class App
    {
        static void Main()
        {
            Console.WriteLine("hello".Shout());
            Console.WriteLine(Tools.StringExt.Shout("still callable"));
        }
    }
}
