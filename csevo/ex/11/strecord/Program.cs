// 슬라이드 p11-v10-st-record — record struct 의 초기화자, C# 10.0
using System;

#if R1
record struct R1 { public int F = 42; }     // no constructor at all
#endif
record struct R2() { public int F = 42; }   // empty parameter list
record struct R5(int F)
{
#if R5
    public R5() { }                         // no this(...)
#else
    public R5() : this(-1) { }
#endif
}

class App
{
    static void Main() =>
        Console.WriteLine(new R2().F + " " + new R5() + " "
            + default(R5));
}
