// 슬라이드 p14-v13-or-call — 부를 수 없게 되는 오버로드, C# 13
using System;
using System.Runtime.CompilerServices;

class C3
{
    public void M1(int i) => Console.WriteLine("M1(int)");
    [OverloadResolutionPriority(1)]
    public void M1(long l) => Console.WriteLine("M1(long)");

    public void M3(string s) => Console.WriteLine("M3(string)");
    [OverloadResolutionPriority(1)]
    public void M3(object o) => Console.WriteLine("M3(object)");
}

class Program
{
    static void Main()
    {
        int i = 1;
        var c = new C3();
        c.M1(i);                  // calls M1(long)
        c.M3("s");                // calls M3(object)
#if DEL1
        Action<int> f = c.M1;     // through a delegate
        f(i);
#endif
#if DEL3
        Action<string> g = c.M3;  // variance
        g("s");
#endif
        typeof(C3).GetMethod("M1", [typeof(int)])!
            .Invoke(c, [i]);      // reflection
        typeof(C3).GetMethod("M3", [typeof(string)])!
            .Invoke(c, ["s"]);
    }
}
