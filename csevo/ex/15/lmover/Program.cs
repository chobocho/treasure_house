// 슬라이드 p15-v14-lm-over — scoped 는 오버로드를 가르지 않는다, C# 14
using System;

delegate void WithScoped(scoped ReadOnlySpan<int> s);
delegate void Plain(ReadOnlySpan<int> s);
delegate bool WithOut(string s, out int v);
delegate bool WithRef(string s, ref int v);

class Program
{
    static void M(WithScoped d) => Console.WriteLine("WithScoped");
    static void M(Plain d) => Console.WriteLine("Plain");
    static void N(WithOut d) => Console.WriteLine("WithOut");
    static void N(WithRef d) => Console.WriteLine("WithRef");

    static void Main()
    {
        N((s, out v) => int.TryParse(s, out v));    // out decides
        N((s, ref v) => v > 0);                     // ref decides
#if AMBIG
        M((scoped s) => { });                       // scoped does not
#endif
    }
}
