// 슬라이드 p11-v10-gu-scope — using 별칭은 global 을 못 본다, C# 10.0
#if BAD
using Names = Col.List<string>;             // Col: a global alias
#else
using Names = System.Collections.Generic.List<string>;
#endif
#if BAD2
using Pipe = Console;                       // System: a global using
#endif

class App
{
    static void Main()
    {
        var xs = new Names { "ann" };
        var ys = new Col.Queue<int>();      // fine inside members
        Console.WriteLine(xs.Count + ys.Count);
    }
}
