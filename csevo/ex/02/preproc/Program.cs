// 슬라이드 p2-v1-preproc — #define 과 #if, C# 1.0
#define VERBOSE
#undef LEGACY
using System;

class App
{
    static void Main()
    {
#if VERBOSE && !LEGACY
        Console.WriteLine("verbose build");
#elif LEGACY
        Console.WriteLine("legacy build");
#else
        Console.WriteLine("plain build");
#endif

#if NIGHTLY
        Console.WriteLine("NIGHTLY is defined (by -define:)");
#endif

        #region not a scope, just a fold marker
        int x = 1;
        #endregion
        Console.WriteLine("x = " + x);
    }
}
