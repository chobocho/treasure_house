// 슬라이드 p9-v8-sl-fix — 16.3 이 잘못 받아 주던 것, C# 8.0
using System;

class App
{
    static void Main()
    {
        object local = "x";
        void Local() { }

        static void StaticLocal()
        {
            Local();                     // a non-static local fn
            _ = new Func<int>(local.GetHashCode);   // needs local
        }
        StaticLocal();
    }
}
