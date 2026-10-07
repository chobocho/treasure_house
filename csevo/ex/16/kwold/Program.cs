// 슬라이드 p16-kw-old — 문맥 키워드를 이름으로(C# 2–8 의 낱말), C# 1
using System;

class Program
{
    static void Main() { Console.WriteLine(Run()); }
#if YIELD
    static object Run() { int yield = 1; return yield; }
#elif PARTIAL
    class partial { }
    static partial Run() { return new partial(); }
#elif VAR
    class var { }
    static object Run() { var v = new var(); return v; }
#elif FROM
    static object Run() { int from = 6; return from; }
#elif DYNAMIC
    class dynamic { }
    static object Run() { dynamic d = new dynamic(); return d; }
#elif ASYNC
    class async { }
    static async Run()
    {
        int await = 0; async[] all = { new async() }; return all[await];
    }
#elif WHEN
    static object Run() { int when = 1; return when; }
#elif NAMEOF
    static string nameof(object o) { return "method"; }
    static object Run() { int x = 1; return nameof(x); }
#elif DISCARD
    static object Run() { int _ = 1; _ = _ + 1; return _; }
#elif UNMANAGED
    class unmanaged { }
    static object F<T>(T t) where T : unmanaged { return t; }
    static object Run() { return F(new unmanaged()); }
#elif NOTNULL
    class notnull { }
    static object F<T>(T t) where T : notnull { return t; }
    static object Run() { return F(new notnull()); }
#else
    static object Run() { return "no symbol"; }
#endif
}
