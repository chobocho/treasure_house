// 슬라이드 p15-v14-lm-break — scoped 는 언제나 한정자, C# 14
using System;

ref struct @scoped
{
    public int V;
}

delegate int F(scoped scoped s);

class Program
{
    static void Main()
    {
        F f = (scoped scoped s) => s.V;          // target-typed
        Console.WriteLine(f(new @scoped { V = 3 }));
#if VAR
        var v = (scoped scoped s) => s.V;        // the document's form
#endif
#if DEF
        F g = (scoped s = default) => s.V;       // open question 1
#elif FIX
        F g = (@scoped s = default) => s.V;
#endif
    }
}
