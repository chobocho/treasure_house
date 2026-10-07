// 슬라이드 p16-kw-new — 문맥 키워드를 이름으로(C# 9–14 의 낱말), C# 8.0
using System;

class Program
{
    static void Main() { Console.WriteLine(Run()); }
#if RECORD
    class record { }
    static object Run() { return new record(); }
#elif NOT
    class not { }
    static object Run()
    {
        object o = new not();
        return o is not x ? x : null;
    }
#elif NINT
    class nint { }
    static object Run() { nint n = new nint(); return n; }
#elif INIT
    int init = 1;
    static object Run() { return new Program().init; }
#elif REQUIRED
    class required { }
    static object Run() { return new required(); }
#elif SCOPED
    class scoped { }
    static object Run() { return new scoped(); }
#elif FILE
    class file { }
    static object Run() { return new file(); }
#elif ALLOWS
    class allows { }
    static object Run() { return new allows(); }
#elif FIELD
    int field = 7;
    int P { get { return field; } }
    static object Run() { return new Program().P; }
#elif EXTENSION
    class extension { }
    static object Run() { return new extension(); }
#else
    static object Run() { return "no symbol"; }
#endif
}
